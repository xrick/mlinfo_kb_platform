from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ParseBase(ABC):
    """
    抽象基礎解析類別
    
    提供解析流程的標準介面，包含三個主要階段：
    - beforeParse: 解析前準備工作
    - inParse: 主要解析邏輯
    - endParse: 解析後處理工作
    """
    
    def __init__(self):
        """初始化解析器"""
        self._data = None
        self._config = {}
    
    @abstractmethod
    def beforeParse(self, data: Any, config: Optional[Dict] = None) -> bool:
        """
        解析前準備工作
        
        Args:
            data: 要解析的資料
            config: 解析配置參數
            
        Returns:
            bool: 準備工作是否成功
        """
        pass
    
    @abstractmethod
    def inParse(self) -> List[Dict]:
        """
        主要解析邏輯
        
        Returns:
            List[Dict]: 解析結果列表
        """
        pass
    
    @abstractmethod
    def endParse(self) -> bool:
        """
        解析後處理工作
        
        Returns:
            bool: 後處理是否成功
        """
        pass
    
    def parse(self, data: Any, config: Optional[Dict] = None) -> List[Dict]:
        """
        執行完整的解析流程
        
        Args:
            data: 要解析的資料
            config: 解析配置參數
            
        Returns:
            List[Dict]: 解析結果列表
        """
        try:
            # 解析前準備
            if not self.beforeParse(data, config):
                raise Exception("解析前準備失敗")
            
            # 主要解析
            result = self.inParse()
            
            # 解析後處理
            if not self.endParse():
                raise Exception("解析後處理失敗")
            
            return result
            
        except Exception as e:
            raise Exception(f"解析過程發生錯誤: {str(e)}")
    
    @property
    def data(self) -> Any:
        """獲取當前資料"""
        return self._data
    
    @data.setter
    def data(self, value: Any):
        """設置資料"""
        self._data = value
    
    @property
    def config(self) -> Dict:
        """獲取配置"""
        return self._config
    
    @config.setter
    def config(self, value: Dict):
        """設置配置"""
        self._config = value 