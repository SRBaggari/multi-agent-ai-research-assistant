"""
Registration and login.

Passwords are stored as bcrypt hashes (never in plain text) and login
returns a JWT that the frontend sends back as a Bearer token.
"""

import re

from datetime import datetime, timedelta, timezone

import bcrypt

from jose import jwt, JWTError

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from pydantic import BaseModel, Field

from pymongo.errors import PyMongoError

from app.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRE_DAYS,
)

from app.database.mongodb import users_collection


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ==================================================
# Request models
# ==================================================

class RegisterRequest(BaseModel):

    name: str = Field(min_length=1, max_length=100)

    email: str = Field(min_length=3, max_length=200)

    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):

    email: str

    password: str


# ==================================================
# Token helpers
# ==================================================

def create_token(user_id: str, email: str) -> str:

    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:

    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    except JWTError as error:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token."
        ) from error


def _bearer_token(request: Request) -> str | None:
    """Pull the raw token out of the Authorization header."""

    header = request.headers.get("Authorization", "")

    if not header.lower().startswith("bearer "):
        return None

    token = header[7:].strip()

    return token or None


def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency for endpoints that REQUIRE a logged-in user.

    Raises 401 when the token is missing, malformed or expired.
    """

    token = _bearer_token(request)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token."
        )

    payload = decode_token(token)

    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
    }


def get_optional_user(request: Request) -> dict | None:
    """
    FastAPI dependency for endpoints that work with or without login.

    Returns the user when a valid token is present, otherwise None.
    An invalid token is ignored rather than rejected, so Swagger and
    anonymous use keep working.
    """

    token = _bearer_token(request)

    if not token:
        return None

    try:
        payload = decode_token(token)

    except HTTPException:
        return None

    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
    }


# ==================================================
# Endpoints
# ==================================================

@router.post("/register")
def register(request: RegisterRequest):

    email = request.email.strip().lower()

    if not EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email address."
        )

    try:
        existing_user = users_collection.find_one({"email": email})

    except PyMongoError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not reach the database. Is MongoDB running?"
        ) from error

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    password_hash = bcrypt.hashpw(
        request.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:

        result = users_collection.insert_one({
            "name": request.name.strip(),
            "email": email,
            "password": password_hash,
            "created_at": datetime.now(timezone.utc),
        })

    except PyMongoError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not save the new user to the database."
        ) from error

    user_id = str(result.inserted_id)

    return {
        "message": "Registration successful",
        "token": create_token(user_id, email),
        "user": {
            "id": user_id,
            "name": request.name.strip(),
            "email": email,
        },
    }


@router.post("/login")
def login(request: LoginRequest):

    email = (request.email or "").strip().lower()

    if not email or not request.password:
        raise HTTPException(
            status_code=400,
            detail="Email and password are required."
        )

    try:
        user = users_collection.find_one({"email": email})

    except PyMongoError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not reach the database. Is MongoDB running?"
        ) from error

    # The same message for both cases, so the response does not reveal
    # which email addresses are registered.
    invalid = HTTPException(
        status_code=401,
        detail="Invalid email or password."
    )

    if not user:
        raise invalid

    stored_hash = user.get("password", "")

    try:
        password_valid = bcrypt.checkpw(
            request.password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )

    except ValueError:
        # Stored value is not a bcrypt hash (e.g. an old plain-text row).
        password_valid = False

    if not password_valid:
        raise invalid

    user_id = str(user["_id"])

    return {
        "message": "Login successful",
        "token": create_token(user_id, email),
        "user": {
            "id": user_id,
            "name": user.get("name", ""),
            "email": email,
        },
    }


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    """Return the logged-in user. Used by the frontend to verify a token."""

    return current_user
