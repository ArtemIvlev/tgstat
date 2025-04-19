from sqlalchemy.orm import sessionmaker
from tgstats.database.models import Base
from tgstats.database.database import Database

db = Database()
Session = sessionmaker(bind=db.engine)

def init_db():
    Base.metadata.create_all(db.engine)

def get_session():
    return Session()
