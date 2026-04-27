import psycopg2.extras
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.api.frontend_api.dependencies import get_db, USER_ID

router = APIRouter(prefix="/settings", tags=["settings"])


# ── Profile ──────────────────────────────────────────────────────────────────

@router.get("/profile")
def get_profile(conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT u.name, u.email, u.phone_number,
                   us.about, us.profession
            FROM users u
            LEFT JOIN user_settings us ON us.user_id = u.id
            WHERE u.id = %s
            """,
            (USER_ID,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone_number"],
        "about": row["about"],
        "profession": row["profession"],
    }


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    about: Optional[str] = None
    profession: Optional[str] = None


@router.put("/profile")
def update_profile(body: ProfileUpdate, conn=Depends(get_db)):
    with conn.cursor() as cur:
        if any(v is not None for v in [body.name, body.email, body.phone]):
            cur.execute(
                """
                UPDATE users
                SET name = COALESCE(%s, name),
                    email = COALESCE(%s, email),
                    phone_number = COALESCE(%s, phone_number),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (body.name, body.email, body.phone, USER_ID),
            )
        if any(v is not None for v in [body.about, body.profession]):
            cur.execute(
                """
                UPDATE user_settings
                SET about = COALESCE(%s, about),
                    profession = COALESCE(%s, profession),
                    updated_at = NOW()
                WHERE user_id = %s
                """,
                (body.about, body.profession, USER_ID),
            )
        conn.commit()

    return {"status": "ok"}


# ── AI Model ─────────────────────────────────────────────────────────────────

@router.get("/ai-model")
def get_ai_model(conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT llm_tone, response_style, api_keys, answer_persona FROM user_settings WHERE user_id = %s",
            (USER_ID,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User settings not found")

    return {
        "llm_tone": row["llm_tone"],
        "response_style": row["response_style"],
        "api_keys": row["api_keys"] or {},
        "answer_persona": row["answer_persona"],
    }


class AIModelUpdate(BaseModel):
    llm_tone: Optional[str] = None
    response_style: Optional[str] = None
    api_keys: Optional[dict] = None
    answer_persona: Optional[str] = None


@router.put("/ai-model")
def update_ai_model(body: AIModelUpdate, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_settings
            SET llm_tone = COALESCE(%s, llm_tone),
                response_style = COALESCE(%s, response_style),
                api_keys = COALESCE(%s::jsonb, api_keys),
                answer_persona = COALESCE(%s, answer_persona),
                updated_at = NOW()
            WHERE user_id = %s
            """,
            (
                body.llm_tone,
                body.response_style,
                psycopg2.extras.Json(body.api_keys) if body.api_keys is not None else None,
                body.answer_persona,
                USER_ID,
            ),
        )
        conn.commit()

    return {"status": "ok"}


# ── Tracked Entities ──────────────────────────────────────────────────────────

@router.get("/tracked-entities")
def get_tracked_entities(conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT te.id, te.normalized_name, te.entity_type, te.boost_value,
                   e.id AS entity_id
            FROM tracked_entities te
            LEFT JOIN entities e
              ON lower(e.normalized_name) = lower(te.normalized_name)
             AND e.entity_type = te.entity_type
             AND e.user_id = te.user_id
            WHERE te.user_id = %s
            ORDER BY te.normalized_name
            """,
            (USER_ID,),
        )
        rows = cur.fetchall()

    return {
        "tracked": [
            {
                "tracked_entity_id": str(r["id"]),
                "normalized_name": r["normalized_name"],
                "entity_type": r["entity_type"],
                "boost_value": r["boost_value"],
                "entity_id": str(r["entity_id"]) if r["entity_id"] else None,
            }
            for r in rows
        ]
    }


@router.get("/entities/search")
def search_entities(q: str = Query(""), conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, name, entity_type, mention_count
            FROM entities
            WHERE user_id = %s AND name ILIKE %s
            ORDER BY mention_count DESC
            LIMIT 20
            """,
            (USER_ID, f"%{q}%"),
        )
        rows = cur.fetchall()

    return {
        "entities": [
            {
                "entity_id": str(r["id"]),
                "name": r["name"],
                "entity_type": r["entity_type"],
                "mention_count": r["mention_count"],
            }
            for r in rows
        ]
    }


class TrackedEntityCreate(BaseModel):
    normalized_name: str
    entity_type: str
    boost_value: float = 0.2


@router.post("/tracked-entities")
def add_tracked_entity(body: TrackedEntityCreate, conn=Depends(get_db)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO tracked_entities (user_id, normalized_name, entity_type, boost_value)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, normalized_name) DO UPDATE
              SET boost_value = EXCLUDED.boost_value
            RETURNING id
            """,
            (USER_ID, body.normalized_name.lower(), body.entity_type, body.boost_value),
        )
        row = cur.fetchone()
        conn.commit()

    return {"status": "ok", "tracked_entity_id": str(row["id"])}


class BoostUpdate(BaseModel):
    boost_value: float


@router.put("/tracked-entities/{tracked_entity_id}")
def update_tracked_entity(tracked_entity_id: str, body: BoostUpdate, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE tracked_entities SET boost_value = %s WHERE id = %s AND user_id = %s RETURNING id",
            (body.boost_value, tracked_entity_id, USER_ID),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tracked entity not found")
        conn.commit()
    return {"status": "ok"}


@router.delete("/tracked-entities/{tracked_entity_id}")
def delete_tracked_entity(tracked_entity_id: str, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM tracked_entities WHERE id = %s AND user_id = %s RETURNING id",
            (tracked_entity_id, USER_ID),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tracked entity not found")
        conn.commit()
    return {"status": "ok"}
