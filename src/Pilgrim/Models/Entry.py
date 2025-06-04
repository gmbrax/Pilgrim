from sqlalchemy import Column, Integer, String, ForeignKey, Table

from Pilgrim import Base


photo_entry_association = Table('photo_entry_association', Base.metadata,
Column('id', Integer, primary_key=True, autoincrement=True),
    Column('fk_Photo_id', Integer, ForeignKey('photo.id')),
    Column('fk_Entry_id', Integer, ForeignKey('Entry.id')))


class Entry(Base):
    __tablename__ = "Entry"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    text = Column(String)
    date = Column(String)
    fk_TravelDiary_id = Column(Integer, ForeignKey("TravelDiary.id"))
