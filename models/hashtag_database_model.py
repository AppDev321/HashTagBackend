from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime,JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Load the database URL from an environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://default:phKrmd9w6sUL@ep-icy-cake-a4pchsu0.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require")
#DATABASE_URL = "postgresql://root:root@localhost/hash_tag_db"



Base = declarative_base()

class SearchTag(Base):
    __tablename__ = "search_tags"

    id = Column(Integer, primary_key=True, index=True)
    searchWord = Column(String, index=True)
    best = Column(JSON )
    top = Column(JSON )
    recommended = Column(JSON )
    exact = Column(JSON )
    popular = Column(JSON )
    related = Column(JSON )


# Create the database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Drop the table if it exists
# Base.metadata.drop_all(bind=engine)  # This will drop all tables defined in Base


# Create tables
Base.metadata.create_all(bind=engine)
