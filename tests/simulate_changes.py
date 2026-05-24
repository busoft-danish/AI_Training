"""
Simulation script to seed and mutate test data.

Run stages:
  python simulate_changes.py seed      — insert 5 drivers + 5 incidents
  python simulate_changes.py update    — update 3 records
  python simulate_changes.py delete    — delete 2 records
"""
import asyncio
import sys
from datetime import datetime, timezone

import pandas as pd
import asyncpg

PG_DSN = "postgresql://postgres:YourNewSecurePassword@localhost:5432/kidshuttle_"
EXCEL_PATH = "drivers.xlsx"

INITIAL_DRIVERS = [
    {"driver_id": "D001", "name": "Alice Johnson", "license_expiry": "2025-12-01",
     "training_certs": "CPR, First Aid", "last_inspection_date": "2024-11-01"},
    {"driver_id": "D002", "name": "Bob Smith", "license_expiry": "2026-03-15",
     "training_certs": "Defensive Driving", "last_inspection_date": "2024-10-20"},
    {"driver_id": "D003", "name": "Carol White", "license_expiry": "2025-07-30",
     "training_certs": "CPR", "last_inspection_date": "2024-09-15"},
    {"driver_id": "D004", "name": "David Brown", "license_expiry": "2027-01-10",
     "training_certs": "First Aid, Safety", "last_inspection_date": "2024-08-05"},
    {"driver_id": "D005", "name": "Eva Green", "license_expiry": "2025-11-20",
     "training_certs": "CPR, Defensive Driving", "last_inspection_date": "2024-07-22"},
]


async def seed_postgres() -> None:
    conn = await asyncpg.connect(PG_DSN)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS safety_incidents (
            incident_id TEXT PRIMARY KEY,
            event_description TEXT,
            severity TEXT,
            resolved_at TEXT,
            status TEXT,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS resolution_notes (
            incident_id TEXT PRIMARY KEY,
            response_steps TEXT,
            resolution TEXT,
            preventive_measures TEXT
        )
    """)
    incidents = [
        ("I001", "Child left on bus", "HIGH", "2024-11-01", "RESOLVED"),
        ("I002", "Minor fender bender", "LOW", "2024-10-15", "RESOLVED"),
        ("I003", "Driver fatigue reported", "MEDIUM", None, "OPEN"),
        ("I004", "Route deviation", "LOW", "2024-09-20", "RESOLVED"),
        ("I005", "Seatbelt malfunction", "HIGH", None, "OPEN"),
    ]
    for inc in incidents:
        await conn.execute(
            "INSERT INTO safety_incidents (incident_id, event_description, severity, resolved_at, status) "
            "VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING",
            *inc,
        )
        await conn.execute(
            "INSERT INTO resolution_notes (incident_id, response_steps, resolution, preventive_measures) "
            "VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING",
            inc[0], "Step 1: Assess. Step 2: Report.", "Issue resolved.", "Add checklist.",
        )
    await conn.close()
    print("Seeded 5 incidents into PostgreSQL.")


def seed_excel() -> None:
    pd.DataFrame(INITIAL_DRIVERS).to_excel(EXCEL_PATH, index=False)
    print(f"Seeded 5 drivers into {EXCEL_PATH}.")


async def update_records() -> None:
    # Update 3 drivers in Excel
    df = pd.read_excel(EXCEL_PATH, dtype=str)
    df.loc[df["driver_id"] == "D001", "training_certs"] = "CPR, First Aid, Advanced Safety"
    df.loc[df["driver_id"] == "D002", "last_inspection_date"] = "2025-01-15"
    df.loc[df["driver_id"] == "D003", "license_expiry"] = "2026-07-30"
    df.to_excel(EXCEL_PATH, index=False)
    print("Updated D001, D002, D003 in Excel.")

    # Update 3 incidents in PostgreSQL
    conn = await asyncpg.connect(PG_DSN)
    await conn.execute(
        "UPDATE safety_incidents SET status='RESOLVED', updated_at=NOW() WHERE incident_id='I003'"
    )
    await conn.execute(
        "UPDATE safety_incidents SET severity='CRITICAL', updated_at=NOW() WHERE incident_id='I005'"
    )
    await conn.execute(
        "UPDATE resolution_notes SET resolution='Fully resolved with new protocol.' WHERE incident_id='I001'"
    )
    await conn.close()
    print("Updated I003, I005 status and I001 resolution in PostgreSQL.")


async def delete_records() -> None:
    # Delete 2 drivers from Excel
    df = pd.read_excel(EXCEL_PATH, dtype=str)
    df = df[~df["driver_id"].isin(["D004", "D005"])]
    df.to_excel(EXCEL_PATH, index=False)
    print("Deleted D004, D005 from Excel.")

    # Delete 2 incidents from PostgreSQL
    conn = await asyncpg.connect(PG_DSN)
    await conn.execute("DELETE FROM resolution_notes WHERE incident_id IN ('I004', 'I005')")
    await conn.execute("DELETE FROM safety_incidents WHERE incident_id IN ('I004', 'I005')")
    await conn.close()
    print("Deleted I004, I005 from PostgreSQL.")


async def main() -> None:
    stage = sys.argv[1] if len(sys.argv) > 1 else "seed"
    if stage == "seed":
        await seed_postgres()
        seed_excel()
    elif stage == "update":
        await update_records()
    elif stage == "delete":
        await delete_records()
    else:
        print(f"Unknown stage: {stage}. Use: seed | update | delete")


if __name__ == "__main__":
    asyncio.run(main())
