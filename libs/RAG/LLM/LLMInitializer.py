from langchain_community.llms import Ollama

class LLMInitializer:
    # def __init__(self, model_name: str = "gpt-oss:20b", temperature: float = 0.1):
    # def __init__(self, model_name: str = "deepseek-r1:7b", temperature: float = 0.1):
    def __init__(self, model_name: str = "gpt-oss:20b", temperature: float = 0.1, request_timeout: int = 60):
        """
        gpt-oss:20b
        deepseek-r1:7b
        初始化 LLM。
        :param model_name: 在 Ollama 中運行的模型名稱。
        :param temperature: 控制生成文本的隨機性。
        :param request_timeout: 請求超時時間（秒），防止無限等待。
        """
        self.model_name = model_name
        self.temperature = temperature
        self.request_timeout = request_timeout
        self.llm = None

    def get_llm(self):
        """獲取已初始化的 LLM 實例"""
        if self.llm is None:
            try:
                self.llm = Ollama(
                    model=self.model_name,
                    temperature=self.temperature
                )
                print(f"成功初始化 Ollama 模型: {self.model_name} (timeout: {self.request_timeout}s)")
            except Exception as e:
                print(f"初始化 Ollama 模型失敗: {e}")
                # 可以在這裡提供一個備用的 LLM 或拋出異常
                raise ConnectionError("無法連接到 Ollama 服務。請確保 Ollama 正在運行。") from e
        return self.llm

    def invoke(self, prompt: str) -> str:
        """
        直接調用 LLM
        
        Args:
            prompt: 用戶提示詞
            
        Returns:
            LLM 回應
        """
        return self.get_llm().invoke(prompt)