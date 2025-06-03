from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

class Database:
    def __init__(self):
        self.engine = create_engine('sqlite:///database.db', echo=False,connect_args={"check_same_thread": False})
        self.Session = sessionmaker(bind=self.engine,autoflush=False,autocommit=False)
        self.Base = declarative_base()
    def create(self):
        self.Base.metadata.create_all(self.engine)
    def get_db(self):
        db = self.Session()
        try:
            yield db
        finally:
            db.close()


