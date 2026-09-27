import sqlalchemy
from google.cloud.sql.connector import Connector
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

connector = Connector()

def getconn():
    return connector.connect(
        settings.instance_connection_name,
        "pg8000",
        user=settings.db_user,
        password=settings.db_pass,
        db=settings.db_name,
    )

engine = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=getconn,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()