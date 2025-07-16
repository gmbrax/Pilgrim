from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
import shutil

from pilgrim.utils import ConfigManager

Base = declarative_base()



class Database:
    def __init__(self,config_manager:ConfigManager):
        db_path = config_manager.database_url
        self.engine = create_engine(
            f"sqlite:///{config_manager.database_url}",
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
