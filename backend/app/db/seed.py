"""
Seed script — inserts the single prototype user and all data_sources rows.
Safe to run multiple times (ON CONFLICT DO NOTHING).

Run from backend/:
    python -m app.db.seed
"""

from app.db.connection import get_connection

USER_ID = "5dd97b4c-ab58-4ae7-9fa0-a3d71eef16d9"

DATA_SOURCES = [
    ("39218ef4-b3ce-4b98-b1e2-34afa243c785", "whatsapp", "push"),
    ("250f8201-6caa-4b88-8983-b450f8343af6", "gmail",    "scheduled"),
    ("1c03923e-730c-471b-95a0-4014d000414a", "gmeet",    "scheduled"),
    ("a26589c9-8edf-4f44-b7ec-ee5d9e06482e", "calendar", "scheduled"),
    ("2f269226-cc45-4eb8-9c67-7efa8ecb3463", "manual",   "manual"),
]


def seed():
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Insert prototype user
        cur.execute(
            """
            INSERT INTO users (id, name, email)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (USER_ID, "EchoMind User", "user@echomind.local"),
        )

        # Insert data sources
        for src_id, name, mode in DATA_SOURCES:
            cur.execute(
                """
                INSERT INTO data_sources (id, name, ingestion_mode)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (src_id, name, mode),
            )

        conn.commit()
        print("Seed complete.")
        print(f"  user_id : {USER_ID}")
        for src_id, name, _ in DATA_SOURCES:
            print(f"  {name:<10}: {src_id}")

    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
