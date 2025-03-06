import os
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import sys
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

print(f"Connecting to database...", file=sys.stderr)
engine = create_engine(
    DATABASE_URL,
    echo=True,  # SQL logging
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,  # Recycle connections every hour
    pool_size=5,  # Maximum number of permanent connections
    max_overflow=10,  # Maximum number of additional temporary connections
    connect_args={
        "sslmode": "require",  # Force SSL mode
        "connect_timeout": 10,  # Connection timeout in seconds
        "keepalives": 1,  # Enable TCP keepalives
        "keepalives_idle": 30,  # Seconds between TCP keepalives
        "keepalives_interval": 10,  # Seconds between TCP keepalive retransmits
        "keepalives_count": 5  # Maximum number of TCP keepalive retransmits
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger)  # Discord user ID
    guild_id = Column(BigInteger)  # Discord server ID
    balance = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint for user_id + guild_id combination
    __table_args__ = (
        UniqueConstraint('user_id', 'guild_id', name='unique_user_guild'),
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(BigInteger)
    to_user_id = Column(BigInteger)
    guild_id = Column(BigInteger)
    amount = Column(Integer)
    transaction_type = Column(String)  # 'transfer', 'daily', 'admin_set', etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class ServiceLevel(Base):
    __tablename__ = "service_levels"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger)  # Discord server ID
    name = Column(String)
    emoji = Column(String)
    required_balance = Column(Integer)
    color = Column(Integer)
    benefits = Column(String)  # Store as JSON string

@contextmanager
def get_db():
    """Database session context manager"""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error: {str(e)}", file=sys.stderr)
        raise
    finally:
        db.close()

print("Creating database tables...", file=sys.stderr)
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!", file=sys.stderr)
except Exception as e:
    print(f"Error creating database tables: {e}", file=sys.stderr)
    raise