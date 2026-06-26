from sqlalchemy import create_engine, Column, String, Integer, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# SQLite database path
DATABASE_URL = "sqlite:///./investigations.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class InvestigationRun(Base):
    __tablename__ = "investigation_runs"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    dataset_metadata = Column(JSON, nullable=True)
    
    # State snapshots
    investigation_state = Column(JSON, nullable=True)
    planner_notebook = Column(JSON, nullable=True)
    investigation_tree = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    business_impact = Column(JSON, nullable=True)
    decision_support = Column(JSON, nullable=True)
    
    # Explainability & Metrics
    primary_root_cause = Column(String, nullable=True)
    explainability_score = Column(Integer, nullable=True)
    
    final_report = Column(String, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
