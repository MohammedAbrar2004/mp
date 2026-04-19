from app.connectors.gmail.client import fetch_recent_emails
from pipelines.ingestion_pipeline import process


def run():
    emails = fetch_recent_emails(limit=50)

    if not emails:
        print("No emails fetched.")
        return

    print(f"Fetched {len(emails)} emails. Sending to pipeline...")

    process(emails)

    print("Gmail ingestion completed.")


if __name__ == "__main__":
    run()
