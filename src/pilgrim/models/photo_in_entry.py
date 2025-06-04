from sqlalchemy import Table, Column, Integer, ForeignKey

from ..database import Base

photo_entry_association = Table('photo_entry_association', Base.metadata,
Column('id', Integer, primary_key=True, autoincrement=True),
    Column('fk_Photo_id', Integer, ForeignKey('photo.id')),
    Column('fk_Entry_id', Integer, ForeignKey('Entry.id')))
