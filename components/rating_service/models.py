from sqlalchemy import Column, BigInteger, TIMESTAMP, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()


class ProfileRating(Base):
    __tablename__ = 'profile_ratings'

    profile_telegram_id = Column(BigInteger, primary_key=True, index=True)
    rating_score = Column(Float)
    last_calculated_at = Column(TIMESTAMP, server_default=func.now())
