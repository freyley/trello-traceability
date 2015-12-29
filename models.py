#!/usr/bin/env python

import settings
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Board(Base):
    __tablename__ = 'board'
    id = Column(String, primary_key=True)
    name = Column(String)

class TrelloList(Base):
    __tablename__ = 'list'
    id = Column(String, primary_key=True)
    name = Column(String)
    board = relationship(Board)
    board_id = Column(String, ForeignKey(Board.id))

class Checklist(Base):
    __tablename__ = 'checklist'
    id = Column(String, primary_key=True)
    name = Column(String)

class Card(Base):
    __tablename__ = 'card'
    id = Column(String, primary_key=True)
    name = Column(String)
    trellolist = relationship(TrelloList)
    trellolist_id = Column(String, ForeignKey(TrelloList.id))
    magic_checklist = relationship(Checklist)
    magic_checklist_id = Column(String, ForeignKey(Checklist.id))

def get_session():
    from sqlalchemy import create_engine
    engine = create_engine(settings.TRELLO_DB_CONNECTION_STRING)
    from sqlalchemy.orm import sessionmaker
    session = sessionmaker()
    session.configure(bind=engine)
    return session

def main():
    session = get_session()
    Base.metadata.create_all(session.kw['bind'])

if __name__=='__main__':
    main()