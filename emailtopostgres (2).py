import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_sync.log'),
        logging.StreamHandler()
    ]
)

def connect_to_gmail(email_address, password):
    """Connect to Gmail IMAP server."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(email_address, password)
        logging.info("Successfully connected to Gmail")
        return mail
    except imaplib.IMAP4.error as e:
        logging.error(f"Failed to connect to Gmail: {e}")
        raise

def connect_to_db():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        logging.info("Successfully connected to PostgreSQL")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Failed to connect to database: {e}")
        raise

def create_table(conn):
    """Create emails table if it doesn't exist."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id SERIAL PRIMARY KEY,
                    message_id TEXT UNIQUE,
                    subject TEXT,
                    sender TEXT,
                    date TIMESTAMP,
                    body TEXT
                )
            """)
        conn.commit()
        logging.info("Emails table created or verified")
    except psycopg2.Error as e:
        logging.error(f"Failed to create table: {e}")
        raise

def insert_email(conn, message_id, subject, sender, date, body):
    """Insert email into database, avoiding duplicates."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("INSERT INTO emails (message_id, subject, sender, date, body) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (message_id) DO NOTHING"),
                (message_id, subject, sender, date, body)
            )
        conn.commit()
        if cur.rowcount > 0:
            logging.info(f"Inserted email with message_id: {message_id}")
        else:
            logging.info(f"Skipped duplicate email with message_id: {message_id}")
    except psycopg2.Error as e:
        logging.error(f"Failed to insert email {message_id}: {e}")
        raise

def fetch_emails(mail_connection, db_connection, folder="inbox", sender=None, days_back=None):
    """Fetch emails from Gmail with filters and save to database."""
    try:
        # Select folder (e.g., "inbox", "[Gmail]/Sent Mail", "[Gmail]/Starred")
        mail_connection.select(f'"{folder}"')
        logging.info(f"Selected folder: {folder}")

        # Build search criteria
        search_criteria = []
        if days_back:
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            search_criteria.append(f'SINCE "{since_date}"')
        if sender:
            search_criteria.append(f'FROM "{sender}"')
        search_query = " ".join(search_criteria) if search_criteria else "ALL"
        logging.info(f"Searching emails with query: {search_query}")

        # Search emails
        _, message_numbers = mail_connection.search(None, search_query)
        email_count = len(message_numbers[0].split())
        logging.info(f"Found {email_count} emails matching criteria")

        for num in message_numbers[0].split():
            try:
                _, msg_data = mail_connection.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                # Extract email details
                message_id = email_message["Message-ID"] or "unknown_" + str(num)
                subject, encoding = decode_header(email_message["Subject"] or "")[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="replace")
                else:
                    subject = subject or "No Subject"
                sender_field = email_message["From"] or "unknown"
                date = parsedate_to_datetime(email_message["Date"]) if email_message["Date"] else None

                # Extract email body
                body = ""
                try:
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="replace")
                                break
                            elif part.get_content_type() == "text/html" and not body:
                                body = part.get_payload(decode=True).decode(errors="replace")
                    else:
                        body = email_message.get_payload(decode=True).decode(errors="replace")
                except (UnicodeDecodeError, AttributeError):
                    body = "Unable to decode email body"
                    logging.warning(f"Failed to decode body for message_id: {message_id}")

                # Insert into database
                insert_email(db_connection, message_id, subject, sender_field, date, body)

            except Exception as e:
                logging.error(f"Error processing email {num}: {e}")
                continue

    except Exception as e:
        logging.error(f"Error fetching emails from folder {folder}: {e}")
        raise

def main():
    """Main function to run the email sync process."""
    try:
        # Load environment variables
        load_dotenv()
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_PASSWORD")

        if not gmail_user or not gmail_password:
            raise ValueError("GMAIL_USER or GMAIL_PASSWORD not set in .env file")

        # Connect to Gmail and database
        mail_conn = connect_to_gmail(gmail_user, gmail_password)
        db_conn = connect_to_db()

        # Create table
        create_table(db_conn)

        # Fetch emails with filters
        # Example: Fetch emails from the last 7 days, from a specific sender, in the inbox
        fetch_emails(
            mail_conn,
            db_conn,
            folder="inbox",  # Can be "[Gmail]/Sent Mail", "[Gmail]/Starred", etc.
            sender="example@domain.com",  # Set to None to include all senders
            days_back=7  # Set to None to include all dates
        )

    except Exception as e:
        logging.error(f"Program failed: {e}")
        raise
    finally:
        try:
            mail_conn.close()
            mail_conn.logout()
            logging.info("Closed Gmail connection")
        except:
            pass
        try:
            db_conn.close()
            logging.info("Closed database connection")
        except:
            pass

if __name__ == "__main__":
    main()