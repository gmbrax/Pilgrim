from sqlalchemy import Table, Column, Integer, ForeignKey

from ..database import Base

photo_entry_association = Table('photo_entry_association', Base.metadata,
Column('id', Integer, primary_key=True, autoincrement=True),
    Column('fk_photo_id', Integer, ForeignKey('photos.id')),
    Column('fk_entry_id', Integer, ForeignKey('entries.id')))
