from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from db.session import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True)
    token = Column(String, nullable=False, unique=True)
    expired_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
