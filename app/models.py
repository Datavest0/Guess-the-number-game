from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base

class Guess(Base):
    __tablename__ = "guess"
    id = Column(Integer, primary_key=True, autoincrement=True)
    guess = Column(Integer, nullable=True)
    result = Column(String(64), nullable=True)
    computer_number = Column(Integer, nullable=True)