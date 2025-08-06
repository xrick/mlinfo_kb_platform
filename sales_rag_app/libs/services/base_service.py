from abc import ABC, abstractmethod

class BaseService(ABC):
    @abstractmethod
    def chat_stream(self, query: str, **kwargs):
        """
        處理聊天請求並以流式方式返回結果。
        必須是一個生成器 (generator)。
        """
        raise NotImplementedError