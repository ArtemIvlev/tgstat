from abc import ABC, abstractmethod

class BaseCollector(ABC):
    def __init__(self, client, db):
        self.client = client
        self.db = db

    @abstractmethod
    async def run(self, channel):
        pass
