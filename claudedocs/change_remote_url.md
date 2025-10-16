# Problem: Submodule Remote URL Changed but Remote Branch Missing

## 背景描述

原始子模組 `notebookservices/OpenNotebook` 追蹤的是 `https://github.com/xrick/open-notebook`。後來在主倉庫的 `.gitmodules` 中，將子模組 URL 改成 `https://github.com/xrick/lcj_open_notebook.git`，但沒有同步更新子模組工作樹內的 remote 設定。結果本地工作樹仍然指向舊的遠端，且新的遠端尚未擁有對應的 commit 或分支，導致在檢查或同步時出現「遠端分支不存在」的狀況，遠端倉庫也看不到 `notebookservices` 子模組。

## 解決方案

1. **同步 `.gitmodules` 設定**  
   在主專案根目錄執行：
   ```bash
   git submodule sync --recursive
   ```
   這會把 `.gitmodules` 的新 URL 寫入 `.git/config`，確保本地子模組 remote 設定更新。

2. **更新子模組 remote**  
   進入子模組目錄確認並調整 remote：
   ```bash
   cd notebookservices/OpenNotebook
   git remote -v
   git remote set-url origin https://github.com/xrick/lcj_open_notebook.git
   git fetch origin
   ```

3. **確保新遠端有對應分支與 commit**  
   - 如果 `lcj_open_notebook` 已包含 `main` 分支：
     ```bash
     git checkout main
     git pull origin main
     ```
   - 若新遠端尚無 `main`，需將舊遠端的相應 commit 推送到新 repo，或在子模組內建立新分支後推送。

4. **更新主專案中的子模組指標**  
   回到主專案根目錄：
   ```bash
   cd /home/mapleleaf/LCJRepos/projects/mlinfo_kb_platform
   git add .gitmodules notebookservices/OpenNotebook
   git commit -m "chore: point notebookservices submodule to lcj fork"
   git push
   ```

完成以上步驟後，主倉庫與子模組都會正確指向 `xrick/lcj_open_notebook` 的遠端分支，遠端伺服器上也會重新顯示 `notebookservices/OpenNotebook` 子模組。

