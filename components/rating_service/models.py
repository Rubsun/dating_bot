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
    likes_given = Column(Integer, nullable=False, default=0)
    dislikes_given = Column(Integer, nullable=False, default=0)
    likes_received = Column(Integer, nullable=False, default=0)
    dislikes_received = Column(Integer, nullable=False, default=0)
    matches_count = Column(Integer, nullable=False, default=0)
    chats_count = Column(Integer, nullable=False, default=0)
    refs_count = Column(Integer, nullable=False, default=0)
