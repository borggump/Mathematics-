import os
import sys
import psycopg2
from pypff import open_file, PffFile
from datetime import datetime
from email.utils import parseaddr

def connect_to_postgres(dbname, user, password, host, port):
    try:
        return psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
    except psycopg2.Error as e:
        print(f"Unable to connect to the database: {e}")
        sys.exit(1)

def create_tables(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id SERIAL PRIMARY KEY,
                    subject TEXT,
                    sender TEXT,
                    recipient TEXT,
                    date TIMESTAMP,
                    body TEXT
                )
            """)
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error creating table: {e}")
        conn.rollback()
        sys.exit(1)

def insert_email(cur, subject, sender, recipient, date, body):
    try:
        cur.execute("""
            INSERT INTO emails (subject, sender, recipient, date, body)
            VALUES (%s, %s, %s, %s, %s)
        """, (subject, sender, recipient, date, body))
    except psycopg2.Error as e:
        print(f"Error inserting email: {e}")
        raise

def process_folder(folder, cur):
    for message in folder.sub_messages:
        try:
            subject = message.get_subject() or ""
            sender = parseaddr(message.get_sender_name())[1] or ""
            recipient = parseaddr(message.get_recipient_name())[1] or ""
            date = message.get_delivery_time() or datetime.now()
            body = message.get_plain_text_body() or ""

            if isinstance(body, bytes):
                body = body.decode('utf-8', errors='ignore')

            insert_email(cur, subject, sender, recipient, date, body)
        except Exception as e:
            print(f"Error processing message: {e}")
            continue

    for subfolder in folder.sub_folders:
        process_folder(subfolder, cur)

def convert_pst_to_postgres(pst_file_path, conn):
    try:
        pst = open_file(pst_file_path)
        root = pst.get_root_folder()

        with conn.cursor() as cur:
            process_folder(root, cur)

        conn.commit()
        pst.close()
    except Exception as e:
        print(f"Error during PST conversion: {e}")
        conn.rollback()
        sys.exit(1)

def main():
    # PostgreSQL connection details
    dbname = "your_database_name"
    user = "your_username"
    password = "your_password"
    host = "localhost"
    port = "5432"

    # Path to your .PST file
    pst_file_path = "path/to/your/file.pst"

    if not os.path.exists(pst_file_path):
        print(f"PST file not found: {pst_file_path}")
        sys.exit(1)

    conn = connect_to_postgres(dbname, user, password, host, port)
    create_tables(conn)
    convert_pst_to_postgres(pst_file_path, conn)
    conn.close()

    print("Conversion completed successfully.")

if __name__ == "__main__":
    main()