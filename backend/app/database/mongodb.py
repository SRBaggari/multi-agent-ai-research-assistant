import os

from pymongo import MongoClient

from dotenv import load_dotenv


load_dotenv()


MONGO_URI = os.getenv(
    "MONGO_URI"
)

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "research_assistant"
)


if not MONGO_URI:

    raise ValueError(
        "MONGO_URI is not set in .env"
    )


client = MongoClient(
    MONGO_URI
)


db = client[
    DATABASE_NAME
]


users_collection = db[
    "users"
]

papers_collection = db[
    "papers"
]

research_collection = db[
    "research"
]


def test_database():

    try:

        client.admin.command(
            "ping"
        )

        return True

    except Exception:

        return False