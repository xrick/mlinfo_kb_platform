# libs/utils_classes/Profiler.py
import cProfile
import pstats
import time

class Profiler:
    def __init__(self, sort_by='cumtime'):
        """
        初始化分析器。
        :param sort_by: pstats 報告的排序依據，例如 'cumtime' 或 'tottime'。
        """
        self._profiler = cProfile.Profile()
        self.sort_by = sort_by

    def __enter__(self):
        """
        在進入 with 區塊時，啟動分析器 [1]。
        """
        self._profiler.enable()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        在離開 with 區塊時，停止分析器並印出報告 [1]。
        """
        self._profiler.disable()
        print("\n--- 效能分析報告 ---")
        stats = pstats.Stats(self._profiler).sort_stats(self.sort_by)
        stats.print_stats()


'''使用範例
# --- 使用我們新建立的 Profiler 類別 ---

def slow_function():
    """一個模擬耗時操作的函式。"""
    time.sleep(1)

def fast_function():
    """一個執行速度很快的函式。"""
    _ = 1 + 1

def main_task():
    """我們想要分析效能的主任務區段。"""
    fast_function()
    slow_function()
    fast_function()

# 現在，衡量 main_task 的效能變得非常簡單：
print("=== 開始分析 ===")
with Profiler(sort_by='cumtime'):
    main_task()
print("=== 分析結束 ===")
說明
• __init__：我們在這裡初始化 cProfile.Profile 物件，並允許使用者自訂報告的排序方式，增加了靈活性。
• __enter__：這個方法對應到 profiler.enable()，它會在 with 陳述式開始時被自動呼叫。
• __exit__：這個方法對應到 profiler.disable() 以及後續的 pstats 處理。無論 with 區塊中的程式碼是否成功執行，它都會被呼叫，確保分析總能完成並呈現結果。
透過這樣的封裝，您成功地將方法四的複雜步驟轉化為如同方法三一樣簡潔的語法。現在，當您想找出程式中真正的效能瓶頸時，只需要使用 with Profiler(): 包裹住懷疑的程式碼區段即可，這無疑是更方便且更專業的做法
'''