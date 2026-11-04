
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "corporate-leads.csv"
DB_PATH = BASE_DIR / "data" / "leads.db"

STAGES = (
    "New",
    "Contacted",
    "Meeting",
    "Proposal",
    "Invoice sent",
    "Paid",
    "Lost",
)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                industry TEXT,
                contact_name TEXT,
                contact_role TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                source TEXT,
                stage TEXT NOT NULL,
                deal_value_bdt INTEGER DEFAULT 0,
                last_contact TEXT,
                next_follow_up TEXT,
                notes TEXT
            )
        """)

        existing_count = connection.execute(
            "SELECT COUNT(*) FROM leads"
        ).fetchone()[0]

        if existing_count > 0:
            print("Database already contains leads.")
            return

        if not CSV_PATH.exists():
            raise FileNotFoundError(
                f"CSV file not found: {CSV_PATH}"
            )

        with CSV_PATH.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        if len(rows) != 25:
            raise ValueError(
                f"Expected 25 leads, found {len(rows)}"
            )

        for row in rows:
            stage = row["stage"].strip()

            if stage not in STAGES:
                raise ValueError(
                    f"Invalid stage: {stage}"
                )

            connection.execute("""
                INSERT INTO leads VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
            """, (
                row["lead id"],
                row["company"],
                row["industry"],
                row["contact name"],
                row["contact role"],
                row["contact email"],
                row["contact phone"],
                row["source"],
                stage,
                int(row["deal value (BDT)"] or 0),
                row["last contact"],
                row["next follow-up"],
                row["notes"]
            ))

        print(f"Imported {len(rows)} leads.")


def get_all_leads():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM leads ORDER BY lead_id"
        ).fetchall()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    initialize_database()

    leads = get_all_leads()
    print(f"Total leads in SQLite: {len(leads)}")

def update_lead(lead_id, updates):
    """
    Update selected fields for one lead in SQLite.
    """

    allowed_fields = {
        "company",
        "contact_name",
        "contact_role",
        "contact_email",
        "contact_phone",
        "stage",
        "last_contact",
        "next_follow_up",
        "notes"
    }

    # Only permit approved fields
    safe_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    if not safe_updates:
        return False

    connection = get_connection()

    try:
        fields = ", ".join(
            f"{field} = ?"
            for field in safe_updates
        )

        values = list(safe_updates.values())
        values.append(lead_id)

        cursor = connection.execute(
            f"UPDATE leads SET {fields} WHERE lead_id = ?",
            values
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()
