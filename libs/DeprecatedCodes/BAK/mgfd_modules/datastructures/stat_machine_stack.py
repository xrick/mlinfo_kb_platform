#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stat Machine Stack - 簡化易用的 Stack 資料結構

這個模組提供了一個簡單易用的 Stack 資料結構，專門設計用於狀態機系統，
支援存放任何類型的資料，並提供直觀的 API 介面。

主要用途：
- 狀態機狀態歷史追蹤
- 事件處理順序管理
- 狀態回滾功能
- 通用資料堆疊操作

使用範例：
    # 基本使用
    stack = Stack("my_stack")
    stack.push("hello")
    stack.push(123)
    stack.push({"state": "user", "input": "hello"})
    
    # 狀態機使用
    state_stack = Stack("state_history")
    state_stack.push({"state": "initial", "timestamp": "2025-01-01"})
    current_state = state_stack.peek()
"""

from typing import Any, List, Optional
from datetime import datetime
import logging


class Stack:
    """
    簡化易用的 Stack 資料結構
    
    支援存放任何類型的資料，提供直觀的 API 介面。
    專門設計用於狀態機系統，但也可用於通用堆疊操作。
    
    屬性：
        name (str): Stack 的名稱，用於識別和除錯
        _items (List[Any]): 內部儲存的資料列表
    
    使用範例：
        # 創建 Stack
        stack = Stack("my_stack")
        
        # 推入資料
        stack.push("hello")
        stack.push(123)
        stack.push({"key": "value"})
        
        # 基本操作
        print(stack.peek())  # {"key": "value"}
        print(stack.pop())   # {"key": "value"}
        print(stack.size())  # 2
    """
    
    def __init__(self, name: str = "stack"):
        """
        初始化 Stack
        
        Args:
            name (str): Stack 的名稱，預設為 "stack"
        
        使用範例：
            # 基本初始化
            stack = Stack()
            
            # 自訂名稱
            state_stack = Stack("state_history")
            event_stack = Stack("event_queue")
        """
        self._items: List[Any] = []
        self.name = name
        self._logger = logging.getLogger(f"{__name__}.{name}")
        self._logger.debug(f"Stack '{name}' 初始化完成")
    
    def push(self, item: Any) -> None:
        """
        推入項目到 Stack 頂部
        
        Args:
            item (Any): 要推入的項目，可以是任何類型
        
        使用範例：
            stack = Stack("test")
            
            # 推入不同類型的資料
            stack.push("字串資料")
            stack.push(123)
            stack.push({"key": "value"})
            stack.push([1, 2, 3])
            stack.push(None)
            
            print(stack.size())  # 5
        """
        self._items.append(item)
        self._logger.debug(f"推入項目: {type(item).__name__} = {item}")
    
    def pop(self) -> Optional[Any]:
        """
        彈出 Stack 頂部的項目
        
        Returns:
            Optional[Any]: 頂部的項目，如果 Stack 為空則返回 None
        
        使用範例：
            stack = Stack("test")
            stack.push("first")
            stack.push("second")
            stack.push("third")
            
            print(stack.pop())  # "third"
            print(stack.pop())  # "second"
            print(stack.pop())  # "first"
            print(stack.pop())  # None (Stack 已空)
        """
        if self.is_empty():
            self._logger.warning("嘗試從空的 Stack 彈出項目")
            return None
        
        item = self._items.pop()
        self._logger.debug(f"彈出項目: {type(item).__name__} = {item}")
        return item
    
    def peek(self) -> Optional[Any]:
        """
        查看 Stack 頂部的項目，但不移除
        
        Returns:
            Optional[Any]: 頂部的項目，如果 Stack 為空則返回 None
        
        使用範例：
            stack = Stack("test")
            stack.push("hello")
            stack.push("world")
            
            print(stack.peek())  # "world"
            print(stack.size())  # 2 (項目仍在 Stack 中)
            
            # 狀態機使用案例
            state_stack = Stack("state_history")
            state_stack.push({"state": "user_input", "message": "hello"})
            current_state = state_stack.peek()
            print(f"當前狀態: {current_state}")
        """
        if self.is_empty():
            self._logger.debug("嘗試查看空的 Stack")
            return None
        
        item = self._items[-1]
        self._logger.debug(f"查看頂部項目: {type(item).__name__} = {item}")
        return item
    
    def is_empty(self) -> bool:
        """
        檢查 Stack 是否為空
        
        Returns:
            bool: True 如果 Stack 為空，否則 False
        
        使用範例：
            stack = Stack("test")
            print(stack.is_empty())  # True
            
            stack.push("item")
            print(stack.is_empty())  # False
            
            stack.pop()
            print(stack.is_empty())  # True
            
            # 在迴圈中使用
            while not stack.is_empty():
                item = stack.pop()
                print(f"處理項目: {item}")
        """
        return len(self._items) == 0
    
    def size(self) -> int:
        """
        取得 Stack 中項目的數量
        
        Returns:
            int: Stack 中項目的數量
        
        使用範例：
            stack = Stack("test")
            print(stack.size())  # 0
            
            stack.push("item1")
            stack.push("item2")
            stack.push("item3")
            print(stack.size())  # 3
            
            stack.pop()
            print(stack.size())  # 2
            
            # 狀態機使用案例
            state_stack = Stack("state_history")
            state_stack.push({"state": "initial"})
            state_stack.push({"state": "processing"})
            state_stack.push({"state": "complete"})
            print(f"狀態歷史長度: {state_stack.size()}")
        """
        return len(self._items)
    
    def clear(self) -> None:
        """
        清空 Stack 中的所有項目
        
        使用範例：
            stack = Stack("test")
            stack.push("item1")
            stack.push("item2")
            stack.push("item3")
            
            print(stack.size())  # 3
            stack.clear()
            print(stack.size())  # 0
            print(stack.is_empty())  # True
            
            # 狀態機重置使用案例
            state_stack = Stack("state_history")
            # ... 添加一些狀態 ...
            state_stack.clear()  # 重置狀態歷史
        """
        cleared_count = len(self._items)
        self._items.clear()
        self._logger.info(f"清空 Stack，移除了 {cleared_count} 個項目")
    
    def to_list(self) -> List[Any]:
        """
        將 Stack 轉換為列表（複製）
        
        Returns:
            List[Any]: 包含 Stack 中所有項目的列表副本
        
        使用範例：
            stack = Stack("test")
            stack.push("first")
            stack.push("second")
            stack.push("third")
            
            # 轉換為列表
            items_list = stack.to_list()
            print(items_list)  # ["first", "second", "third"]
            
            # 修改列表不會影響原 Stack
            items_list.append("fourth")
            print(stack.size())  # 3 (原 Stack 不變)
            
            # 狀態機使用案例
            state_stack = Stack("state_history")
            # ... 添加狀態 ...
            state_history = state_stack.to_list()
            for i, state in enumerate(state_history):
                print(f"狀態 {i}: {state}")
        """
        return self._items.copy()
    
    def get_items(self) -> List[Any]:
        """
        取得 Stack 中所有項目的列表（直接引用）
        
        注意：這會返回內部列表的直接引用，修改會影響原 Stack
        
        Returns:
            List[Any]: Stack 中所有項目的列表
        
        使用範例：
            stack = Stack("test")
            stack.push("item1")
            stack.push("item2")
            
            # 取得項目列表
            items = stack.get_items()
            print(items)  # ["item1", "item2"]
            
            # 注意：修改會影響原 Stack
            items.append("item3")
            print(stack.size())  # 3 (原 Stack 也被修改)
        """
        return self._items
    
    def __str__(self) -> str:
        """
        字串表示
        
        Returns:
            str: Stack 的字串表示
        
        使用範例：
            stack = Stack("my_stack")
            stack.push("item1")
            stack.push("item2")
            
            print(str(stack))  # "Stack(my_stack)[2 items]"
        """
        return f"Stack({self.name})[{self.size()} items]"
    
    def __repr__(self) -> str:
        """
        詳細的字串表示，用於除錯
        
        Returns:
            str: Stack 的詳細字串表示
        
        使用範例：
            stack = Stack("test")
            stack.push("hello")
            stack.push(123)
            
            print(repr(stack))  # "Stack(name='test', items=['hello', 123])"
        """
        return f"Stack(name='{self.name}', items={self._items})"
    
    def __len__(self) -> int:
        """
        取得 Stack 的長度
        
        Returns:
            int: Stack 中項目的數量
        
        使用範例：
            stack = Stack("test")
            stack.push("item1")
            stack.push("item2")
            
            print(len(stack))  # 2
        """
        return len(self._items)
    
    def __bool__(self) -> bool:
        """
        檢查 Stack 是否非空
        
        Returns:
            bool: True 如果 Stack 非空，否則 False
        
        使用範例：
            stack = Stack("test")
            print(bool(stack))  # False
            
            stack.push("item")
            print(bool(stack))  # True
            
            # 在條件判斷中使用
            if stack:
                print("Stack 非空")
            else:
                print("Stack 為空")
        """
        return not self.is_empty()


# 專門用於狀態機的 Stack 擴展類別
class StateStack(Stack):
    """
    專門用於狀態機的 Stack 擴展類別
    
    提供額外的狀態管理功能，如狀態回滾、狀態歷史等。
    
    使用範例：
        # 創建狀態 Stack
        state_stack = StateStack("chat_state")
        
        # 記錄狀態變化
        state_stack.push_state({"state": "initial", "timestamp": "2025-01-01"})
        state_stack.push_state({"state": "user_input", "message": "hello"})
        state_stack.push_state({"state": "processing", "action": "extract_slots"})
        
        # 查看當前狀態
        current_state = state_stack.get_current_state()
        print(f"當前狀態: {current_state}")
        
        # 回滾到上一個狀態
        previous_state = state_stack.rollback()
        print(f"回滾到: {previous_state}")
    """
    
    def __init__(self, name: str = "state_stack"):
        """
        初始化狀態 Stack
        
        Args:
            name (str): Stack 的名稱，預設為 "state_stack"
        """
        super().__init__(name)
        self._logger.info(f"狀態 Stack '{name}' 初始化完成")
    
    def push_state(self, state: dict) -> None:
        """
        推入狀態，自動添加時間戳記和索引
        
        Args:
            state (dict): 狀態字典
        
        使用範例：
            state_stack = StateStack("chat_state")
            
            # 推入狀態
            state_stack.push_state({
                "state": "initial",
                "user_input": None,
                "slots": {}
            })
            
            state_stack.push_state({
                "state": "user_input",
                "user_input": "我想買筆電",
                "slots": {"intent": "purchase"}
            })
            
            state_stack.push_state({
                "state": "processing",
                "user_input": "我想買筆電",
                "slots": {"intent": "purchase", "product": "laptop"}
            })
        """
        state_with_meta = {
            'state_data': state,
            'timestamp': datetime.now().isoformat(),
            'index': self.size()
        }
        self.push(state_with_meta)
        self._logger.info(f"推入狀態: {state.get('state', 'unknown')} (索引: {state_with_meta['index']})")
    
    def get_current_state(self) -> dict:
        """
        取得當前狀態資料
        
        Returns:
            dict: 當前狀態的資料，如果沒有狀態則返回空字典
        
        使用範例：
            state_stack = StateStack("chat_state")
            state_stack.push_state({"state": "initial", "slots": {}})
            state_stack.push_state({"state": "user_input", "message": "hello"})
            
            current_state = state_stack.get_current_state()
            print(current_state)  # {"state": "user_input", "message": "hello"}
        """
        if self.is_empty():
            return {}
        
        top_item = self.peek()
        return top_item.get('state_data', {})
    
    def get_state_history(self) -> List[dict]:
        """
        取得完整的狀態歷史
        
        Returns:
            List[dict]: 包含所有狀態歷史的列表
        
        使用範例：
            state_stack = StateStack("chat_state")
            state_stack.push_state({"state": "initial"})
            state_stack.push_state({"state": "processing"})
            state_stack.push_state({"state": "complete"})
            
            history = state_stack.get_state_history()
            for i, state_info in enumerate(history):
                print(f"狀態 {i}: {state_info['state_data']['state']} "
                      f"({state_info['timestamp']})")
        """
        return self.to_list()
    
    def rollback(self) -> Optional[dict]:
        """
        回滾到上一個狀態
        
        Returns:
            Optional[dict]: 被回滾的狀態，如果沒有狀態可回滾則返回 None
        
        使用範例：
            state_stack = StateStack("chat_state")
            state_stack.push_state({"state": "initial"})
            state_stack.push_state({"state": "processing"})
            state_stack.push_state({"state": "error"})
            
            # 回滾到上一個狀態
            rolled_back_state = state_stack.rollback()
            print(f"回滾到: {rolled_back_state}")
            
            current_state = state_stack.get_current_state()
            print(f"當前狀態: {current_state}")
        """
        if self.size() <= 1:
            self._logger.warning("無法回滾：只有一個或沒有狀態")
            return None
        
        rolled_back_state = self.pop()
        self._logger.info(f"回滾狀態: {rolled_back_state.get('state_data', {}).get('state', 'unknown')}")
        return rolled_back_state.get('state_data', {})
    
    def rollback_to(self, index: int) -> bool:
        """
        回滾到指定的索引位置
        
        Args:
            index (int): 目標索引位置
        
        Returns:
            bool: 回滾是否成功
        
        使用範例：
            state_stack = StateStack("chat_state")
            state_stack.push_state({"state": "initial"})
            state_stack.push_state({"state": "step1"})
            state_stack.push_state({"state": "step2"})
            state_stack.push_state({"state": "step3"})
            state_stack.push_state({"state": "error"})
            
            # 回滾到索引 2 (step2)
            success = state_stack.rollback_to(2)
            if success:
                current_state = state_stack.get_current_state()
                print(f"回滾成功，當前狀態: {current_state}")
            else:
                print("回滾失敗")
        """
        if index < 0 or index >= self.size():
            self._logger.warning(f"無效的索引: {index}，Stack 大小: {self.size()}")
            return False
        
        # 移除索引之後的所有狀態
        while self.size() > index + 1:
            self.pop()
        
        self._logger.info(f"回滾到索引 {index}")
        return True
    
    def get_state_at(self, index: int) -> Optional[dict]:
        """
        取得指定索引位置的狀態
        
        Args:
            index (int): 狀態索引
        
        Returns:
            Optional[dict]: 指定位置的狀態，如果索引無效則返回 None
        
        使用範例：
            state_stack = StateStack("chat_state")
            state_stack.push_state({"state": "initial"})
            state_stack.push_state({"state": "processing"})
            state_stack.push_state({"state": "complete"})
            
            # 取得索引 1 的狀態
            state_at_1 = state_stack.get_state_at(1)
            print(f"索引 1 的狀態: {state_at_1}")
        """
        if index < 0 or index >= self.size():
            return None
        
        items = self.get_items()
        state_info = items[index]
        return state_info.get('state_data', {})
    
    def find_state_by_type(self, state_type: str) -> Optional[dict]:
        """
        根據狀態類型查找最近的狀態
        
        Args:
            state_type (str): 要查找的狀態類型
        
        Returns:
            Optional[dict]: 找到的狀態，如果沒有找到則返回 None
        
        使用範例：
            state_stack = StateStack("chat_state")
            state_stack.push_state({"state": "initial"})
            state_stack.push_state({"state": "user_input", "message": "hello"})
            state_stack.push_state({"state": "processing"})
            state_stack.push_state({"state": "user_input", "message": "world"})
            
            # 查找最近的 user_input 狀態
            user_input_state = state_stack.find_state_by_type("user_input")
            print(f"最近的 user_input 狀態: {user_input_state}")
        """
        items = self.get_items()
        for item in reversed(items):  # 從最新開始查找
            state_data = item.get('state_data', {})
            if state_data.get('state') == state_type:
                return state_data
        
        return None


# 使用範例和測試函數
def demo_basic_stack():
    """基本 Stack 使用範例"""
    print("=== 基本 Stack 使用範例 ===")
    
    # 創建 Stack
    stack = Stack("demo_stack")
    
    # 推入不同類型的資料
    stack.push("字串資料")
    stack.push(123)
    stack.push({"key": "value"})
    stack.push([1, 2, 3])
    
    print(f"Stack: {stack}")
    print(f"大小: {stack.size()}")
    print(f"是否為空: {stack.is_empty()}")
    
    # 基本操作
    print(f"頂部項目: {stack.peek()}")
    print(f"彈出項目: {stack.pop()}")
    print(f"彈出項目: {stack.pop()}")
    
    print(f"剩餘大小: {stack.size()}")
    print(f"轉換為列表: {stack.to_list()}")
    
    # 清空 Stack
    stack.clear()
    print(f"清空後大小: {stack.size()}")


def demo_state_stack():
    """狀態 Stack 使用範例"""
    print("\n=== 狀態 Stack 使用範例 ===")
    
    # 創建狀態 Stack
    state_stack = StateStack("chat_state")
    
    # 模擬對話狀態變化
    state_stack.push_state({
        "state": "initial",
        "user_input": None,
        "slots": {},
        "timestamp": "2025-01-01T10:00:00"
    })
    
    state_stack.push_state({
        "state": "user_input",
        "user_input": "我想買筆電",
        "slots": {"intent": "purchase"},
        "timestamp": "2025-01-01T10:00:05"
    })
    
    state_stack.push_state({
        "state": "processing",
        "user_input": "我想買筆電",
        "slots": {"intent": "purchase", "product": "laptop"},
        "timestamp": "2025-01-01T10:00:10"
    })
    
    state_stack.push_state({
        "state": "error",
        "user_input": "我想買筆電",
        "slots": {"intent": "purchase", "product": "laptop"},
        "error": "無法找到符合條件的筆電",
        "timestamp": "2025-01-01T10:00:15"
    })
    
    print(f"狀態歷史長度: {state_stack.size()}")
    
    # 查看當前狀態
    current_state = state_stack.get_current_state()
    print(f"當前狀態: {current_state['state']}")
    
    # 回滾到上一個狀態
    rolled_back = state_stack.rollback()
    print(f"回滾到: {rolled_back['state']}")
    
    # 查看狀態歷史
    history = state_stack.get_state_history()
    for i, state_info in enumerate(history):
        print(f"狀態 {i}: {state_info['state_data']['state']} "
              f"({state_info['timestamp']})")
    
    # 查找特定狀態
    user_input_state = state_stack.find_state_by_type("user_input")
    if user_input_state:
        print(f"找到 user_input 狀態: {user_input_state['user_input']}")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 執行範例
    demo_basic_stack()
    demo_state_stack()
    
    print("\n=== 實作完成 ===")
    print("Stack 資料結構已成功實作，包含詳細的說明和使用案例。")
