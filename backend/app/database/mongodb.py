"""
MongoDB connection.

PyMongo connects lazily, so importing this module never blocks and
never crashes the application when the database is down.  Connection
problems surface as a clear error from the endpoint that needed it.
"""

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import MONGO_URI, DATABASE_NAME


# serverSelectionTimeoutMS keeps a dead database from hanging a request
# for the default 30 seconds.

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
)

db = client[DATABASE_NAME]

users_collection = db["users"]

papers_collection = db["papers"]

research_collection = db["research"]


def test_database() -> bool:
    """Return True when the database answers a ping."""

    try:
        client.admin.command("ping")
        return True

    except PyMongoError:
        return False


def ensure_indexes():
    """
    Create the indexes the app relies on.

    Failures are not fatal: the app still works without them, and the
    database may simply be unavailable at start-up.
    """

    try:
        users_collection.create_index("email", unique=True)
        papers_collection.create_index("paper_id", unique=True)

    except PyMongoError:
        pass
