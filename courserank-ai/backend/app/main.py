import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models import Course, GradingComponent, Review  # noqa: ensure all models registered
from app.models.sentiment import CourseScore, SentimentResult  # noqa
from app.routes.courses import router as courses_router
from app.routes.reviews import router as reviews_router
from app.routes.admin import router as admin_router

Base.metadata.create_all(bind=engine)


def _seed_if_empty():
    """Seed the database with starter courses if the courses table is empty."""
    from sqlalchemy import func
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        count = db.query(func.count(Course.id)).scalar()
        if count == 0:
            print("Database is empty — seeding starter courses...")
            from app.seed import seed
            seed()
            print("Seed complete.")
    except Exception as e:
        print(f"Auto-seed skipped: {e}")
    finally:
        db.close()


_seed_if_empty()


app = FastAPI(
    title="CourseRank AI",
    description="AI-powered course intelligence for Western University students.",
    version="0.1.0",
)

# CORS — allow local dev + any Vercel deployment domain
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
extra_origin = os.getenv("FRONTEND_URL")
if extra_origin:
    allowed_origins.append(extra_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses_router)
app.include_router(reviews_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {
        "service": "CourseRank AI API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
