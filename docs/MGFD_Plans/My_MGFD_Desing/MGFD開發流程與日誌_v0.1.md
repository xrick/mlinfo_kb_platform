MGFD開發流程與日誌  
version 0.1 2025/08/11

原始概念：A turn of chat of user and LLM, named Chat-Turn  
	\[user query\] → prompt-lvl1 → LLM → response-1 →(to user)   
        \[user query\] → prompt-lvl2 → LLM

1. 核心模組  
   1. Dialogue State Management

   2. Slot Filling

   3. Two Level Prompting: Think, then Act  
      1. Think

      2. Act

   4. (optional not implement now) Long Term Memory

   5. (optional  not implement now)   
      Recommendation System Concepts Integration

