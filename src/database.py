from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Database:
    def __init__(self):
        self.engine = create_engine(
            "sqlite:///database.db",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        self.session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def create(self):
        Base.metadata.create_all(self.engine)

    def get_db(self):
        return self.session()
