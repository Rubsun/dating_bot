from sqlalchemy import Column, BigInteger, String, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(BigInteger, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)  # Male, Female, Other
    city = Column(String(100), nullable=False)
    photo_path = Column(String(255), nullable=True)  # To save the photo file path

    # rating = relationship("ProfileRating", uselist=False, back_populates="profile")  # One-to-one relationship
