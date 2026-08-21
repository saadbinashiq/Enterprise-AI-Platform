import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Local dev default: SQLite file, zero setup required.
# Production path: set DATABASE_URL="postgresql://user:pass@host:5432/enterprise_ai"
# in .env (see .env.example) and pip install psycopg2-binary.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db/enterprise.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    return SessionLocal()
