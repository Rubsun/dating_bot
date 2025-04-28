from sqlalchemy import Column, BigInteger, TIMESTAMP, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()


class ProfileRating(Base):
    __tablename__ = 'profile_ratings'

    profile_telegram_id = Column(BigInteger, primary_key=True, index=True)
    rating_score = Column(Float)
    last_calculated_at = Column(TIMESTAMP, server_default=func.now())


class ProfileStats(Base):
    __tablename__ = 'profile_stats'

    profile_telegram_id = Column(BigInteger, primary_key=True, index=True)
    likes_given = Column(Integer, nullable=True)
    dislikes_given = Column(Integer, nullable=True)
    likes_received = Column(Integer, nullable=True)
    dislikes_received = Column(Integer, nullable=True)
    matches_count = Column(Integer, nullable=True)
    chats_count = Column(Integer, nullable=True)
    refs_count = Column(Integer, nullable=True)
