from app.db.connection import get_connection, close_connection

USER_ID = "5dd97b4c-ab58-4ae7-9fa0-a3d71eef16d9"

SOURCE_ID_MAP: dict[str, str] = {
    "whatsapp": "39218ef4-b3ce-4b98-b1e2-34afa243c785",
    "gmail": "250f8201-6caa-4b88-8983-b450f8343af6",
    "gmeet": "1c03923e-730c-471b-95a0-4014d000414a",
    "calendar": "a26589c9-8edf-4f44-b7ec-ee5d9e06482e",
    "manual": "2f269226-cc45-4eb8-9c67-7efa8ecb3463",
}


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        close_connection(conn)
