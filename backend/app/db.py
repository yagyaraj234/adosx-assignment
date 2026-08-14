from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def reset_db():
    """Drop and recreate all tables - data is a static 120-row CSV, cheap to redo each start."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
