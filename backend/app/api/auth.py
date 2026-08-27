from datetime import datetime, timedelta

import os

import bcrypt

from jose import jwt

from fastapi import (
    APIRouter,
    HTTPException
)

from pydantic import BaseModel

from app.database.mongodb import (
    users_collection
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "change-this-secret"
)

JWT_ALGORITHM = "HS256"


class RegisterRequest(BaseModel):

    name: str

    email: str

    password: str


class LoginRequest(BaseModel):

    email: str

    password: str


def create_token(user_id: str):

    payload = {

        "user_id":
            user_id,

        "exp":
            datetime.utcnow()
            + timedelta(days=1)

    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


@router.post("/register")
def register(
    request: RegisterRequest
):

    existing_user = (
        users_collection.find_one({
            "email":
                request.email
        })
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    password_hash = bcrypt.hashpw(
        request.password.encode(),
        bcrypt.gensalt()
    ).decode()

    result = (
        users_collection.insert_one({

            "name":
                request.name,

            "email":
                request.email,

            "password":
                password_hash,

            "created_at":
                datetime.utcnow()

        })
    )

    token = create_token(
        str(result.inserted_id)
    )

    return {

        "message":
            "Registration successful",

        "token":
            token

    }


@router.post("/login")
def login(
    request: LoginRequest
):

    user = (
        users_collection.find_one({
            "email":
                request.email
        })
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = bcrypt.checkpw(

        request.password.encode(),

        user["password"].encode()

    )

    if not password_valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_token(
        str(user["_id"])
    )

    return {

        "message":
            "Login successful",

        "token":
            token

    }