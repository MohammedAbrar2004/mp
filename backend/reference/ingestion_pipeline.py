"""
Ingestion pipeline for EchoMind.
Orchestrates connectors, preprocessing, and database insertion with robust error handling.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import psycopg2
from psycopg2 import errors as psycopg2_errors

from app.utils.logger import setup_logging, get_logger
from app.utils.error_handler import ErrorTracker, IngestionError, classify_error

from app.connectors.whatsapp.whatsapp_connector import WhatsAppConnector
try:
    from app.connectors.gmail.gmail_connector import GmailConnector
except ImportError:
    GmailConnector = None

from app.connectors.gmeet.gmeet_connector import GMeetConnector
from app.connectors.calendar.calendar_connector import CalendarConnector
from app.connectors.manual.manual_connector import ManualConnector

from app.preprocessing.preprocessor import Preprocessor
from app.db.connection import get_connection
from app.db.repository import insert_memory_chunk, insert_media_file

logger = get_logger("EchoMind.Pipeline")

# Mapping of source_type to source_id
SOURCE_ID_MAP = {
    "whatsapp": "39218ef4-b3ce-4b98-b1e2-34afa243c785",
    "gmail": "250f8201-6caa-4b88-8983-b450f8343af6",
    "gmeet": "1c03923e-730c-471b-95a0-4014d000414a",
    "calendar": "a26589c9-8edf-4f44-b7ec-ee5d9e06482e",
    "manual": "2f269226-cc45-4eb8-9c67-7efa8ecb3463",
}

# Dummy user_id for all inserts (prototype)
USER_ID = "5dd97b4c-ab58-4ae7-9fa0-a3d71eef16d9"


def run_ingestion() -> dict:
    """
    Run the ingestion pipeline across all connectors.
    Processes data with robust error handling and detailed reporting.
    
    Returns:
        dict: Statistics on inserted, duplicates, errors
    """
    connectors = [
        ("WhatsApp", WhatsAppConnector()),
        ("Gmail", GmailConnector()) if GmailConnector else None,
        ("GMeet", GMeetConnector()),
        ("Calendar", CalendarConnector()),
        ("Manual", ManualConnector()),
        ("Phone", PhoneConnector())
    ]
    # Filter out None connectors
    connectors = [(name, c) for name, c in connectors if c is not None]
    
    preprocessor = Preprocessor()
    connection = None
    cursor = None
    
    # Statistics tracking
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    error_tracker = ErrorTracker()
    
    try:
        logger.info("=" * 70)
        logger.info("EchoMind Ingestion Pipeline Started")
        logger.info(f"Connectors to process: {len(connectors)}")
        logger.info("=" * 70)
        
        # Get database connection
        connection = get_connection()
        cursor = connection.cursor()
        logger.info("Database connection established")
        
        # Process each connector
        for connector_name, connector in connectors:
            logger.info(f"\n[{connector_name}] Fetching data...")
            connector_error_count = 0
            connector_fetched = 0
            
            try:
                # Fetch data from connector
                try:
                    data = connector.fetch_data()
                    connector_fetched = len(data)
                    logger.info(f"[{connector_name}] Retrieved {len(data)} items")
                except Exception as e:
                    is_permanent, error_type = classify_error(e)
                    logger.error(f"[{connector_name}] Failed to fetch data: {error_type}: {e}")
                    error_tracker.add_error(IngestionError(
                        source_type=connector_name.lower(),
                        external_message_id="fetch_all",
                        error_message=str(e),
                        error_type=error_type,
                        is_permanent=is_permanent
                    ))
                    continue
                
                # Process each normalized input
                for idx, normalized_input in enumerate(data, 1):
                    try:
                        # Preprocess the input
                        processed_data = preprocessor.process(normalized_input)
                        
                        # Get source_id from mapping
                        source_id = SOURCE_ID_MAP.get(processed_data["source_type"])
                        if not source_id:
                            logger.warning(f"[{connector_name}] No source_id mapping for {processed_data['source_type']}")
                            connector_error_count += 1
                            continue
                        
                        # Insert into database via repository
                        try:
                            chunk_id = insert_memory_chunk(cursor, {
                                "user_id": USER_ID,
                                "source_id": source_id,
                                "external_message_id": processed_data["external_message_id"],
                                "timestamp": processed_data["timestamp"],
                                "participants": processed_data["participants"],
                                "content_type": processed_data["content_type"],
                                "raw_content": processed_data["raw_content"],
                                "initial_salience": processed_data["initial_salience"],
                                "metadata": processed_data["metadata"]
                            })
                            
                            connection.commit()
                            logger.debug(f"[{connector_name}] Inserted chunk {chunk_id}")
                            
                            # Handle media if present
                            if normalized_input.media:
                                for media_idx, media_obj in enumerate(normalized_input.media, 1):
                                    try:
                                        insert_media_file(cursor, chunk_id, media_obj, processed_data["source_type"])
                                        logger.debug(f"[{connector_name}] Inserted media {media_idx}/{len(normalized_input.media)}")
                                    except Exception as me:
                                        logger.warning(f"[{connector_name}] Failed to save media: {me}")
                                        connection.rollback()
                                        raise
                                connection.commit()
                            
                            inserted_count += 1
                            logger.debug(f"[{connector_name}] Item {idx}/{len(data)}: ✓ Inserted")
                        
                        except psycopg2_errors.UniqueViolation:
                            duplicate_count += 1
                            connection.rollback()
                            logger.debug(f"[{connector_name}] Item {idx}/{len(data)}: - Duplicate")
                        
                        except psycopg2.DatabaseError as db_err:
                            error_count += 1
                            connector_error_count += 1
                            connection.rollback()
                            is_permanent, error_type = classify_error(db_err)
                            logger.error(f"[{connector_name}] Item {idx}/{len(data)}: ! Database error: {error_type}")
                            error_tracker.add_error(IngestionError(
                                source_type=connector_name.lower(),
                                external_message_id=normalized_input.external_message_id,
                                error_message=str(db_err),
                                error_type=error_type,
                                is_permanent=is_permanent
                            ))
                    
                    except Exception as e:
                        error_count += 1
                        connector_error_count += 1
                        is_permanent, error_type = classify_error(e)
                        logger.error(f"[{connector_name}] Item {idx}/{len(data)}: ! Error: {error_type}: {e}")
                        error_tracker.add_error(IngestionError(
                            source_type=connector_name.lower(),
                            external_message_id=normalized_input.external_message_id,
                            error_message=str(e),
                            error_type=error_type,
                            is_permanent=is_permanent
                        ))
            
            except Exception as e:
                logger.error(f"[{connector_name}] Connector error: {e}")
                error_tracker.add_error(IngestionError(
                    source_type=connector_name.lower(),
                    external_message_id="connector_error",
                    error_message=str(e),
                    error_type=type(e).__name__,
                    is_permanent=True
                ))
            
            # Log connector summary
            logger.info(
                f"[{connector_name}] Summary: "
                f"Fetched={connector_fetched}, "
                f"Inserted={inserted_count}, "
                f"Errors={connector_error_count}"
            )
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info("EchoMind Ingestion Pipeline Complete")
        logger.info(f"  Total Inserted: {inserted_count}")
        logger.info(f"  Total Duplicates: {duplicate_count}")
        logger.info(f"  Total Errors: {error_count}")
        logger.info("=" * 70)
        
        # Log error summary
        error_tracker.log_summary()
        
        return {
            "inserted": inserted_count,
            "duplicates": duplicate_count,
            "errors": error_count,
            "error_summary": error_tracker.get_summary()
        }
    
    except Exception as e:
        logger.critical(f"Fatal error in ingestion pipeline: {e}")
        if connection:
            try:
                connection.rollback()
            except:
                pass
        return {
            "inserted": inserted_count,
            "duplicates": duplicate_count,
            "errors": error_count + 1,
            "fatal_error": str(e)
        }
    
    finally:
        # Close cursor and connection
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if connection:
            try:
                connection.close()
            except:
                pass
        logger.info("Database connection closed")


def run_ingestion_for_items(
    normalized_inputs: list,
    source_type: str
) -> tuple[int, int, int]:
    """
    Run ingestion for a pre-fetched list of NormalizedInput objects.
    Used by the HTTP receiver for push-based connectors.
    
    Returns:
        tuple: (inserted_count, duplicate_count, error_count)
    """
    preprocessor = Preprocessor()
    connection = None
    cursor = None
    inserted = 0
    duplicates = 0
    errors = 0
    error_tracker = ErrorTracker()

    try:
        logger.info(f"Processing {len(normalized_inputs)} items from {source_type}")
        connection = get_connection()
        cursor = connection.cursor()

        for idx, normalized_input in enumerate(normalized_inputs, 1):
            try:
                processed_data = preprocessor.process(normalized_input)
                source_id = SOURCE_ID_MAP.get(source_type)

                if not source_id:
                    logger.warning(f"No source_id mapping for {source_type}")
                    errors += 1
                    continue

                # Insert memory_chunk via repository
                chunk_id = insert_memory_chunk(cursor, {
                    "user_id": USER_ID,
                    "source_id": source_id,
                    "external_message_id": processed_data["external_message_id"],
                    "timestamp": processed_data["timestamp"],
                    "participants": processed_data["participants"],
                    "content_type": processed_data["content_type"],
                    "raw_content": processed_data["raw_content"],
                    "initial_salience": processed_data["initial_salience"],
                    "metadata": processed_data["metadata"]
                })
                connection.commit()

                # Handle media if present
                if normalized_input.media:
                    for media_obj in normalized_input.media:
                        insert_media_file(cursor, chunk_id, media_obj, source_type)
                    connection.commit()

                inserted += 1
                logger.debug(f"Inserted item {idx}/{len(normalized_inputs)}")

            except psycopg2_errors.UniqueViolation:
                duplicates += 1
                connection.rollback()
                logger.debug(f"Item {idx}/{len(normalized_inputs)}: Duplicate")

            except Exception as e:
                errors += 1
                connection.rollback()
                is_permanent, error_type = classify_error(e)
                logger.error(f"Item {idx}/{len(normalized_inputs)}: {error_type}: {e}")
                error_tracker.add_error(IngestionError(
                    source_type=source_type,
                    external_message_id=normalized_input.external_message_id,
                    error_message=str(e),
                    error_type=error_type,
                    is_permanent=is_permanent
                ))

    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}")
        if connection:
            try:
                connection.rollback()
            except:
                pass

    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if connection:
            try:
                connection.close()
            except:
                pass
        
        logger.info(
            f"Ingestion results: Inserted={inserted}, Duplicates={duplicates}, Errors={errors}"
        )

    return inserted, duplicates, errors


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    setup_logging(level="INFO")
    run_ingestion()
