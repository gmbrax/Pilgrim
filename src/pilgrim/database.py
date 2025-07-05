from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
import shutil

Base = declarative_base()

def get_database_path() -> Path:
    """
    Get the database file path following XDG Base Directory specification.
    Creates the directory if it doesn't exist.
    """
    # Get home directory
    home = Path.home()
    
    # Create .pilgrim directory if it doesn't exist
    pilgrim_dir = home / ".pilgrim"
    pilgrim_dir.mkdir(exist_ok=True)
    
    # Database file path
    db_path = pilgrim_dir / "database.db"
    
    # If database doesn't exist in new location but exists in current directory,
    # migrate it
    if not db_path.exists():
        current_db = Path("database.db")
        if current_db.exists():
            shutil.copy2(current_db, db_path)
            print(f"Database migrated from {current_db} to {db_path}")
    
    return db_path

class Database:
    def __init__(self):
        db_path = get_database_path()
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        self._session_maker = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def create(self):
        Base.metadata.create_all(self.engine)

    def session(self):
        return self._session_maker()

    def get_db(self):
        return self._session_maker()
