from abc import ABC, abstractmethod

class DatabaseQuery(ABC):
    @abstractmethod
    def connect(self):
        raise NotImplementedError

    @abstractmethod
    def query(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError