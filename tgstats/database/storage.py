from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tgstats.config.config import DB_URL
from tgstats.database.models import Base

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return Session()
