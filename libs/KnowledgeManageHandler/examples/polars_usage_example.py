#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polars 使用示例
展示如何使用 KnowledgeManageHandler 的 Polars 功能
"""

import asyncio
import logging
from pathlib import Path
import sys

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from KnowledgeManageHandler import KnowledgeManager


async def main():
    """主函數，展示 Polars 功能的使用"""
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 開始 Polars 功能演示...")
    
    # 初始化知識管理器
    km = KnowledgeManager()
    
    # 檢查 Polars 是否可用
    if not hasattr(km, 'polars_helper') or km.polars_helper is None:
        print("❌ Polars 功能不可用，請檢查安裝")
        return
    
    print("✅ Polars 功能已啟用")
    
    # 示例 1: 連接 CSV 數據源
    print("\n📊 示例 1: 連接 CSV 數據源")
    csv_config = {
        "name": "sample_data",
        "type": "csv",
        "path": "data/sample_data.csv"  # 請根據實際路徑調整
    }
    
    # 注意：這裡需要實際的 CSV 文件，所以我們跳過實際連接
    print("   - 配置 CSV 數據源連接")
    print("   - 支援自動內存管理")
    print("   - 支援多種編碼格式")
    
    # 示例 2: 執行 Polars 查詢
    print("\n🔍 示例 2: 執行 Polars 查詢")
    print("   - 支援 LazyFrame 查詢優化")
    print("   - 支援並行處理")
    print("   - 自動內存使用監控")
    
    # 示例查詢表達式
    sample_queries = [
        "df.filter(pl.col('price') > 1000)",
        "df.select(['modelname', 'price', 'modeltype'])",
        "df.groupby('modeltype').agg([pl.col('price').mean().alias('avg_price')])"
    ]
    
    for i, query in enumerate(sample_queries, 1):
        print(f"   - 查詢 {i}: {query}")
    
    # 示例 3: 性能監控
    print("\n📈 示例 3: 性能監控")
    print("   - 查詢執行時間統計")
    print("   - 內存使用監控")
    print("   - 性能優化建議")
    
    # 示例 4: 錯誤處理和降級
    print("\n🛡️ 示例 4: 錯誤處理和降級")
    print("   - 自動重試機制")
    print("   - SQLite 降級查詢")
    print("   - 詳細錯誤日誌")
    
    # 示例 5: 配置管理
    print("\n⚙️ 示例 5: 配置管理")
    print("   - 內存限制設定")
    print("   - 並行處理配置")
    print("   - 性能監控開關")
    
    # 顯示當前配置
    print(f"\n📋 當前 Polars 配置:")
    for key, value in km.polars_config.items():
        if isinstance(value, (dict, list)):
            print(f"   {key}: {type(value).__name__}")
        else:
            print(f"   {key}: {value}")
    
    # 示例 6: 實際使用場景
    print("\n💡 實際使用場景")
    print("   - 大數據集分析")
    print("   - 實時數據查詢")
    print("   - 數據預處理和轉換")
    print("   - 與現有 SQLite 系統的無縫整合")
    
    print("\n🎉 Polars 功能演示完成！")
    print("\n📚 使用說明:")
    print("   1. 確保已安裝 polars: pip install polars")
    print("   2. 使用 query_polars_data() 方法執行查詢")
    print("   3. 使用 get_polars_stats() 監控性能")
    print("   4. 配置文件中可以調整各種參數")


def create_sample_data():
    """創建示例數據文件"""
    try:
        import pandas as pd
        
        # 創建示例數據
        sample_data = {
            'modelname': ['ThinkPad X1', 'MacBook Pro', 'Dell XPS', 'HP Spectre'],
            'price': [1500, 2000, 1800, 1600],
            'modeltype': ['Business', 'Professional', 'Premium', 'Ultrabook'],
            'cpu': ['Intel i7', 'Apple M2', 'Intel i9', 'Intel i7'],
            'ram': [16, 16, 32, 16],
            'storage': [512, 512, 1024, 512]
        }
        
        df = pd.DataFrame(sample_data)
        
        # 創建數據目錄
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        # 保存為 CSV
        csv_path = data_dir / "sample_data.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"✅ 示例數據已創建: {csv_path}")
        
        # 保存為 Parquet
        parquet_path = data_dir / "sample_data.parquet"
        df.to_parquet(parquet_path, index=False)
        
        print(f"✅ 示例數據已創建: {parquet_path}")
        
    except ImportError:
        print("❌ 需要安裝 pandas 來創建示例數據")
    except Exception as e:
        print(f"❌ 創建示例數據失敗: {e}")


if __name__ == "__main__":
    # 創建示例數據
    create_sample_data()
    
    # 運行演示
    asyncio.run(main())
