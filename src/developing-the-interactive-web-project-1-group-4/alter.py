import os
import psycopg
from dotenv import load_dotenv
load_dotenv()
# Change this to your actual environment variable name.
database_url = os.environ["Database_url"]

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE ti_user
ADD COLUMN contact_me VARCHAR(200);
        """)
print("contact_me column added successfully.")