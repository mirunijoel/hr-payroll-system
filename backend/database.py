import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "seed.sql")


def get_connection(db_path=None):
    """Open a connection to db_path, or to the current value of DB_PATH if not given.

    Reads DB_PATH from the module namespace at call time rather than
    binding it as a default argument, so tests can point this module at
    an isolated database by reassigning database.DB_PATH before the app
    is created, without threading a db_path through every caller.
    """
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None, seed=False):
    """Create the database from schema.sql if it doesn't exist yet.

    Seeds from seed.sql when seed=True, only on first creation, so
    re-running the app never wipes or duplicates existing data.
    """
    if db_path is None:
        db_path = DB_PATH

    if os.path.exists(db_path):
        return

    conn = get_connection(db_path)
    try:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())

        if seed:
            with open(SEED_PATH, "r") as f:
                conn.executescript(f.read())

        conn.commit()
    finally:
        conn.close()
