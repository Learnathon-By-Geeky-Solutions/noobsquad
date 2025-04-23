# models/university.py
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from database.session import Base

class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    departments = Column(MutableList.as_mutable(ARRAY(String)))  # ✅ This tracks changes!
    total_members = Column(Integer, default=0)
