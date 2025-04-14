from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tgstats.database.models import Base

class Database:
    def __init__(self, db_url='sqlite:///tgstats.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def __enter__(self):
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def query(self, *args):
        return self.session.query(*args)
    
    def add(self, obj):
        self.session.add(obj)
    
    def commit(self):
        self.session.commit()
    
    def flush(self):
        self.session.flush() 