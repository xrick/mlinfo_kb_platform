# utils/clean_csv.py
import os
import pandas as pd

def clean_csv_in_folder(folder_path='.'):
    """
    清理指定資料夾內所有 CSV 檔案的 'version' 和 'modelname' 欄位。

    Args:
        folder_path (str): CSV 檔案所在的資料夾路徑。預設為當前目錄。
    """
    # 遍歷資料夾中的所有檔案
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv') and '_cleaned' not in filename:
            file_path = os.path.join(folder_path, filename)
            
            try:
                # 讀取 CSV 檔案
                df = pd.read_csv(file_path)

                # 1. 清理 'version' 欄位
                if 'version' in df.columns:
                    # 移除 "Version:" 和 "version_" 字串
                    df['version'] = df['version'].str.replace('Version:', '', regex=False)
                    df['version'] = df['version'].str.replace('version_', '', regex=False)
                    # 移除前後多餘的空格
                    df['version'] = df['version'].str.strip()

                # 2. 清理 'modelname' 欄位
                if 'modelname' in df.columns:
                    # 移除 "Model Name:" 字串
                    df['modelname'] = df['modelname'].str.replace('Model Name:', '', regex=False)
                    # 移除前後多餘的空格
                    df['modelname'] = df['modelname'].str.strip()

                # 產生新的檔名並儲存
                new_filename = filename.replace('.csv', '_cleaned.csv')
                new_file_path = os.path.join(folder_path, new_filename)
                df.to_csv(new_file_path, index=False)
                
                print(f'已處理檔案：{filename} -> 新檔案：{new_filename}')

            except Exception as e:
                print(f'處理檔案 {filename} 時發生錯誤：{e}')

# --- 使用方式 ---
# 直接執行此腳本，它會處理與腳本相同目錄下的所有 CSV 檔案。
if __name__ == '__main__':
    clean_csv_in_folder()