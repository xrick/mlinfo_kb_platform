#!/bin/bash

echo "�� 啟動MGFD系統..."

# 檢查Redis
echo "�� 檢查Redis服務..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis未運行，嘗試啟動..."
    sudo systemctl start redis
    sleep 2
fi

# 檢查Redis連接
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis連接成功"
else
    echo "❌ Redis連接失敗，請檢查Redis服務"
    exit 1
fi

# 運行測試
echo "🧪 運行系統測試..."
python test_mgfd_system_phase2.py

if [ $? -eq 0 ]; then
    echo "✅ 系統測試通過"
else
    echo "❌ 系統測試失敗"
    exit 1
fi

# 啟動應用程式
echo "🌐 啟動Flask應用程式..."
python main.py