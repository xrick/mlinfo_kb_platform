# libs/utils_classes/Time.py
import time

# 1. 建立計時的上下文管理器
class Timer:
    def __init__(self, description="程式碼區段"):
        self.description = description

    def __enter__(self):
        # 進入 `with` 區塊時觸發
        print(f"開始計時: {self.description}...")
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 離開 `with` 區塊時觸發
        self.end_time = time.perf_counter()
        self.execution_time = self.end_time - self.start_time
        print(f"{self.description} 執行完畢，耗時: {self.execution_time:.6f} 秒")
        # 返回 False 表示如果 `with` 區塊內有異常，正常拋出

# # 2. 使用 `with` 陳述式包裹目標區段
# def main_process():
#     print("主流程開始")
    
#     # 衡量第一個區段
#     with Timer("資料預處理"):
#         time.sleep(0.5)
#         # 假設這裡是大量的資料處理程式碼
#         _ = [i*i for i in range(1_000_000)]
        
#     print("繼續執行其他任務...")
    
#     # 衡量第二個區段
#     with Timer("模型訓練"):
#         time.sleep(1)
#         # 假設這裡是模型訓練程式碼

#     print("主流程結束")

# main_process()