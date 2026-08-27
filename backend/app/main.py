from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware
)

from app.api.auth import router as auth_router

from app.api.papers import router as papers_router

from app.api.research import router as research_router


app = FastAPI(
    title="Multi-Agent AI Research Assistant",
    description=(
        "AI-powered research paper "
        "analysis using RAG and "
        "multi-agent systems."
    ),
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# --------------------------------------------------
# Routes
# --------------------------------------------------

app.include_router(
    auth_router
)

app.include_router(
    papers_router
)

app.include_router(
    research_router
)


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/")
def root():

    return {

        "message":
            "Multi-Agent AI Research Assistant API",

        "status":
            "running"

    }


@app.get("/health")
def health():

    return {

        "status":
            "healthy"

    }