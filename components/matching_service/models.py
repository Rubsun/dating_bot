from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class Like(Base):
    __tablename__ = 'likes'

    # Составной первичный ключ: комбинация liker_telegram_id и liked_telegram_id
    liker_telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    liked_telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    like_type = Column(String(10), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())



class Match(Base):
    __tablename__ = 'matches'

    # Составной первичный ключ: комбинация user1_telegram_id и user2_telegram_id
    # Чтобы избежать дубликатов (A-B и B-A), мы будем всегда хранить ID в определенном порядке
    user1_telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    user2_telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    matched_at = Column(TIMESTAMP, server_default=func.now())