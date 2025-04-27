from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, TIMESTAMP, DECIMAL, Index
from sqlalchemy.sql import func
import datetime
from geoalchemy2 import Geometry

Base = declarative_base()

class Like(Base):
    __tablename__ = 'likes'
    __table_args__ = (
        Index('idx_liker', 'liker_telegram_id'),
        Index('idx_liked', 'liked_telegram_id'),
    )

    liker_telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    liked_telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    like_type = Column(String(10), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Match(Base):
    __tablename__ = 'matches'

    user1_telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    user2_telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    user1_username = Column(String, primary_key=True, nullable=False)
    user2_username = Column(String, primary_key=True, nullable=False)
    matched_at = Column(TIMESTAMP, server_default=func.now())


class UserInfo(Base):
    __tablename__ = "user_infos"
    __table_args__ = (
        Index('idx_user_location', 'location', postgresql_using='gist'),
    )

    user_id = Column(BigInteger, primary_key=True)
    age = Column(Integer)
    gender = Column(String)
    rating = Column(DECIMAL)
    preferred_gender = Column(String)
    preferred_min_age = Column(Integer)
    preferred_max_age = Column(Integer)
    location = Column(Geometry(geometry_type="POINT", srid=4326))
