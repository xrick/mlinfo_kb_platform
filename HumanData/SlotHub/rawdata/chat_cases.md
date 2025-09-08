Rule:

請**嚴格遵守**若預到系統無法理解的詞語、字詞、概念詞、沒有遇到過的用語，請詢問LLM，並產生回答與客戶進行確認，直到確定後，再繼續進行槽位資料收集。

case-1:
user-input-1 :"請介紹目前新出的筆電"-> system:各模組進行處理，發現需要啟動funnnel chat進行槽位資料收集->system:依照預設的槽位資料收集的問題向客戶詢問->客戶回答->[optional:若預到系統無法理解的字詞，請詢問LLM，並產生回答與客戶進行確認，直到確定後，再繼續進行槽位資料收集]->system進行槽位資料收集->直到槽位資料滿足可以進行產品查詢->system進行內部產品搜尋->呈現產品詳細規格給客戶。

case-2:

user: input-1: "請介紹目前最新型的筆電"->

system: response-1: "您好，是否能告知購買筆電主要的用途"->



----------------------- perplexity--------------------


好的，這裏為您整理了幾種當前最先進（State-of-the-Art）的提示（Prompt）範式，並為每種範式提供詳細且實用的 Python 範例。這些技術旨在引導大型語言模型（LLM）產生更準確、更具邏輯性和更符合需求的結果。

## 1. 零樣本提示 (Zero-Shot Prompting)

**說明：**

零樣本提示是最直接的提示方法。在這種模式下，您直接向模型提出請求，而不提供任何具體的任務範例。模型僅依賴其在訓練階段學到的龐大知識來理解任務並生成答案 。這種方法適用於通用請求，或當模型已經對該任務有充分理解時 。[mirascope**+2**](https://mirascope.com/blog/prompt-engineering-examples)

**Python 範例：**

這個範例將使用 OpenAI API 進行情感分析。我們直接指示模型分析文本情感，而無需提供任何「正面」或「負面」的例子 。[plainenglish](https://plainenglish.io/blog/zero-shot-few-shot-and-chain-of-thought-prompt)

<pre class="not-prose w-full rounded font-mono text-sm font-extralight"><div class="codeWrapper text-light selection:text-super selection:bg-super/10 bg-offset my-md relative flex flex-col rounded font-mono text-sm font-normal"><div class="translate-y-xs -translate-x-xs bottom-xl mb-xl sticky top-0 flex h-0 items-start justify-end"><button data-testid="copy-code-button" type="button" class="focus-visible:bg-offsetPlus hover:bg-offsetPlus text-quiet  hover:text-foreground dark:hover:bg-offsetPlus font-sans focus:outline-none outline-none outline-transparent transition duration-300 ease-out select-none items-center relative group/button font-semimedium justify-center text-center items-center rounded-full cursor-pointer active:scale-[0.97] active:duration-150 active:ease-outExpo origin-center whitespace-nowrap inline-flex text-sm h-8 aspect-square"><div class="flex items-center min-w-0 gap-two justify-center"><div class="flex shrink-0 items-center justify-center size-4"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7999999999999998" stroke-linecap="round" stroke-linejoin="round" class="tabler-icon tabler-icon-copy "><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z"></path><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1"></path></svg></div></div></button></div><div class="-mt-xl"><div><div data-testid="code-language-indicator" class="text-quiet bg-offsetPlus py-xs px-sm inline-block rounded-br rounded-tl-[3px] font-thin">python</div></div><div class="pr-lg"><span><code><span><span class="token token">import</span><span> os
</span></span><span><span></span><span class="token token">from</span><span> openai </span><span class="token token">import</span><span> OpenAI
</span></span><span>
</span><span><span></span><span class="token token"># 建議從環境變數讀取您的 API 金鑰</span><span>
</span></span><span><span></span><span class="token token"># os.environ["OPENAI_API_KEY"] = "您的 OpenAI API 金鑰"</span><span>
</span></span><span><span>client </span><span class="token token operator">=</span><span> OpenAI</span><span class="token token punctuation">(</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token">def</span><span></span><span class="token token">zero_shot_sentiment_analysis</span><span class="token token punctuation">(</span><span>text</span><span class="token token punctuation">)</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token triple-quoted-string">"""
</span></span><span class="token token triple-quoted-string">    使用零樣本提示對給定文本進行情感分析。
</span><span><span class="token token triple-quoted-string">    """</span><span>
</span></span><span><span></span><span class="token token">try</span><span class="token token punctuation">:</span><span>
</span></span><span><span>        response </span><span class="token token operator">=</span><span> client</span><span class="token token punctuation">.</span><span>chat</span><span class="token token punctuation">.</span><span>completions</span><span class="token token punctuation">.</span><span>create</span><span class="token token punctuation">(</span><span>
</span></span><span><span>            model</span><span class="token token operator">=</span><span class="token token">"gpt-4o"</span><span class="token token punctuation">,</span><span>
</span></span><span><span>            messages</span><span class="token token operator">=</span><span class="token token punctuation">[</span><span>
</span></span><span><span></span><span class="token token punctuation">{</span><span>
</span></span><span><span></span><span class="token token">"role"</span><span class="token token punctuation">:</span><span></span><span class="token token">"system"</span><span class="token token punctuation">,</span><span>
</span></span><span><span></span><span class="token token">"content"</span><span class="token token punctuation">:</span><span></span><span class="token token">"你是一個專業的情感分析助理。請將使用者提供的文本分類為「正面」、「負面」或「中性」。"</span><span>
</span></span><span><span></span><span class="token token punctuation">}</span><span class="token token punctuation">,</span><span>
</span></span><span><span></span><span class="token token punctuation">{</span><span>
</span></span><span><span></span><span class="token token">"role"</span><span class="token token punctuation">:</span><span></span><span class="token token">"user"</span><span class="token token punctuation">,</span><span>
</span></span><span><span></span><span class="token token">"content"</span><span class="token token punctuation">:</span><span></span><span class="token token string-interpolation">f"請分析以下文本的情感：'</span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">text</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">'"</span><span>
</span></span><span><span></span><span class="token token punctuation">}</span><span>
</span></span><span><span></span><span class="token token punctuation">]</span><span class="token token punctuation">,</span><span>
</span></span><span><span>            temperature</span><span class="token token operator">=</span><span class="token token">0</span><span class="token token punctuation">,</span><span></span><span class="token token"># 溫度設為0以獲得更穩定、可預測的結果</span><span>
</span></span><span><span>            max_tokens</span><span class="token token operator">=</span><span class="token token">50</span><span>
</span></span><span><span></span><span class="token token punctuation">)</span><span>
</span></span><span><span>        sentiment </span><span class="token token operator">=</span><span> response</span><span class="token token punctuation">.</span><span>choices</span><span class="token token punctuation">[</span><span class="token token">0</span><span class="token token punctuation">]</span><span class="token token punctuation">.</span><span>message</span><span class="token token punctuation">.</span><span>content
</span></span><span><span></span><span class="token token">return</span><span> sentiment
</span></span><span><span></span><span class="token token">except</span><span> Exception </span><span class="token token">as</span><span> e</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token">return</span><span></span><span class="token token string-interpolation">f"發生錯誤：</span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">e</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">"</span><span>
</span></span><span>
</span><span><span></span><span class="token token"># 測試範例</span><span>
</span></span><span><span>text_1 </span><span class="token token operator">=</span><span></span><span class="token token">"這部電影的攝影和配樂真是太棒了！"</span><span>
</span></span><span><span>text_2 </span><span class="token token operator">=</span><span></span><span class="token token">"等了半小時的餐點，結果完全是冷的。"</span><span>
</span></span><span>
</span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"文本: '</span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">text_1</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">'"</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"情感分析結果: </span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">zero_shot_sentiment_analysis</span><span class="token token string-interpolation interpolation punctuation">(</span><span class="token token string-interpolation interpolation">text_1</span><span class="token token string-interpolation interpolation punctuation">)</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">\n"</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"文本: '</span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">text_2</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">'"</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"情感分析結果: </span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">zero_shot_sentiment_analysis</span><span class="token token string-interpolation interpolation punctuation">(</span><span class="token token string-interpolation interpolation">text_2</span><span class="token token string-interpolation interpolation punctuation">)</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">"</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span></span></code></span></div></div></div></pre>

## 2. 少樣本提示 (Few-Shot Prompting)

**說明：**

少樣本提示是透過在提示中提供幾個任務範例（Exemplars）來引導模型 。這些範例向模型展示了輸入和期望輸出的格式與風格，使其能夠更好地理解特定或複雜的任務要求 。這種方法在需要特定格式輸出或處理模型較不熟悉領域的問題時特別有效。[promptpanda**+1**](https://www.promptpanda.io/resources/few-shot-prompting-explained-a-guide/)

**Python 範例：**

這個範例展示如何使用少樣本提示來生成一個更嚴謹的 Python 函數。我們提供一兩個函數作為範例，引導模型學習我們期望的代碼風格（例如，包含文檔字符串和輸入驗證）。[promptpanda](https://www.promptpanda.io/resources/few-shot-prompting-explained-a-guide/)

<pre class="not-prose w-full rounded font-mono text-sm font-extralight"><div class="codeWrapper text-light selection:text-super selection:bg-super/10 bg-offset my-md relative flex flex-col rounded font-mono text-sm font-normal"><div class="translate-y-xs -translate-x-xs bottom-xl mb-xl sticky top-0 flex h-0 items-start justify-end"><button data-testid="copy-code-button" type="button" class="focus-visible:bg-offsetPlus hover:bg-offsetPlus text-quiet  hover:text-foreground dark:hover:bg-offsetPlus font-sans focus:outline-none outline-none outline-transparent transition duration-300 ease-out select-none items-center relative group/button font-semimedium justify-center text-center items-center rounded-full cursor-pointer active:scale-[0.97] active:duration-150 active:ease-outExpo origin-center whitespace-nowrap inline-flex text-sm h-8 aspect-square"><div class="flex items-center min-w-0 gap-two justify-center"><div class="flex shrink-0 items-center justify-center size-4"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7999999999999998" stroke-linecap="round" stroke-linejoin="round" class="tabler-icon tabler-icon-copy "><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z"></path><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1"></path></svg></div></div></button></div><div class="-mt-xl"><div><div data-testid="code-language-indicator" class="text-quiet bg-offsetPlus py-xs px-sm inline-block rounded-br rounded-tl-[3px] font-thin">python</div></div><div class="pr-lg"><span><code><span><span class="token token">import</span><span> os
</span></span><span><span></span><span class="token token">from</span><span> openai </span><span class="token token">import</span><span> OpenAI
</span></span><span>
</span><span><span></span><span class="token token"># os.environ["OPENAI_API_KEY"] = "您的 OpenAI API 金鑰"</span><span>
</span></span><span><span>client </span><span class="token token operator">=</span><span> OpenAI</span><span class="token token punctuation">(</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token">def</span><span></span><span class="token token">few_shot_code_generation</span><span class="token token punctuation">(</span><span class="token token punctuation">)</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token triple-quoted-string">"""
</span></span><span class="token token triple-quoted-string">    使用少樣本提示生成一個計算階乘的 Python 函數。
</span><span><span class="token token triple-quoted-string">    """</span><span>
</span></span><span><span>    prompt </span><span class="token token operator">=</span><span></span><span class="token token triple-quoted-string">"""
</span></span><span class="token token triple-quoted-string">    請根據以下範例，寫一個計算一個數階乘的 Python 函數。
</span><span class="token token triple-quoted-string">
</span><span class="token token triple-quoted-string">    範例 1:
</span><span class="token token triple-quoted-string">    \"\"\"
</span><span class="token token triple-quoted-string">    將兩個數字相加並返回結果。
</span><span class="token token triple-quoted-string">    \"\"\"
</span><span class="token token triple-quoted-string">    def add(a, b):
</span><span class="token token triple-quoted-string">        return a + b
</span><span class="token token triple-quoted-string">
</span><span class="token token triple-quoted-string">    範例 2:
</span><span class="token token triple-quoted-string">    \"\"\"
</span><span class="token token triple-quoted-string">    將第二個數字從第一個數字中減去並返回結果。
</span><span class="token token triple-quoted-string">    \"\"\"
</span><span class="token token triple-quoted-string">    def subtract(a, b):
</span><span class="token token triple-quoted-string">        return a - b
</span><span class="token token triple-quoted-string">
</span><span class="token token triple-quoted-string">    現在，請寫一個計算數字階乘的函數。
</span><span><span class="token token triple-quoted-string">    """</span><span>
</span></span><span><span></span><span class="token token">try</span><span class="token token punctuation">:</span><span>
</span></span><span><span>        response </span><span class="token token operator">=</span><span> client</span><span class="token token punctuation">.</span><span>chat</span><span class="token token punctuation">.</span><span>completions</span><span class="token token punctuation">.</span><span>create</span><span class="token token punctuation">(</span><span>
</span></span><span><span>            model</span><span class="token token operator">=</span><span class="token token">"gpt-4o"</span><span class="token token punctuation">,</span><span>
</span></span><span><span>            messages</span><span class="token token operator">=</span><span class="token token punctuation">[</span><span>
</span></span><span><span></span><span class="token token punctuation">{</span><span class="token token">"role"</span><span class="token token punctuation">:</span><span></span><span class="token token">"user"</span><span class="token token punctuation">,</span><span></span><span class="token token">"content"</span><span class="token token punctuation">:</span><span> prompt</span><span class="token token punctuation">}</span><span>
</span></span><span><span></span><span class="token token punctuation">]</span><span class="token token punctuation">,</span><span>
</span></span><span><span>            temperature</span><span class="token token operator">=</span><span class="token token">0.2</span><span class="token token punctuation">,</span><span>
</span></span><span><span>            max_tokens</span><span class="token token operator">=</span><span class="token token">200</span><span>
</span></span><span><span></span><span class="token token punctuation">)</span><span>
</span></span><span><span>        generated_code </span><span class="token token operator">=</span><span> response</span><span class="token token punctuation">.</span><span>choices</span><span class="token token punctuation">[</span><span class="token token">0</span><span class="token token punctuation">]</span><span class="token token punctuation">.</span><span>message</span><span class="token token punctuation">.</span><span>content
</span></span><span><span></span><span class="token token">return</span><span> generated_code
</span></span><span><span></span><span class="token token">except</span><span> Exception </span><span class="token token">as</span><span> e</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token">return</span><span></span><span class="token token string-interpolation">f"發生錯誤：</span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">e</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">"</span><span>
</span></span><span>
</span><span><span></span><span class="token token"># 執行並打印生成的代碼</span><span>
</span></span><span><span>generated_function </span><span class="token token operator">=</span><span> few_shot_code_generation</span><span class="token token punctuation">(</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token">"--- 生成的 Python 函數 ---"</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span>generated_function</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token"># 你可以將生成的代碼複製出來並執行，以驗證其功能</span><span>
</span></span><span><span></span><span class="token token"># exec(generated_function)</span><span>
</span></span><span><span></span><span class="token token"># print(f"5 的階乘是: {factorial(5)}")</span><span>
</span></span><span></span></code></span></div></div></div></pre>

 **關鍵差異** ：與零樣本提示相比，少樣本提示產生的函數通常更完整，可能包含如輸入驗證和文檔字符串等細節，因為模型從範例中學習到了這些良好實踐 。[promptpanda](https://www.promptpanda.io/resources/few-shot-prompting-explained-a-guide/)

## 3. 思維鏈提示 (Chain-of-Thought, CoT Prompting)

**說明：**

思維鏈（CoT）提示是一種先進的技術，它引導模型在給出最終答案之前，先生成一系列中間的推理步驟 。這種方法模仿人類解決複雜問題的思維過程，將大問題分解成一系列更小、更易於管理的部分，從而顯著提高模型在算術、常識和符號推理任務上的表現 。[linkedin**+2**](https://www.linkedin.com/pulse/recipes-all-you-need-new-paradigm-ai-prompting-paul-g-thompson-4qg5e)

**Python 範例：**

這個範例將使用 `langchain` 函式庫來對比普通提示與思維鏈提示在解決數學問題時的差異。我們會看到，僅僅加入一句「讓我們一步一步地思考」就能引導模型產生更可靠的推理過程 。[codecademy](https://www.codecademy.com/article/chain-of-thought-cot-prompting)

<pre class="not-prose w-full rounded font-mono text-sm font-extralight"><div class="codeWrapper text-light selection:text-super selection:bg-super/10 bg-offset my-md relative flex flex-col rounded font-mono text-sm font-normal"><div class="translate-y-xs -translate-x-xs bottom-xl mb-xl sticky top-0 flex h-0 items-start justify-end"><button data-testid="copy-code-button" type="button" class="focus-visible:bg-offsetPlus hover:bg-offsetPlus text-quiet  hover:text-foreground dark:hover:bg-offsetPlus font-sans focus:outline-none outline-none outline-transparent transition duration-300 ease-out select-none items-center relative group/button font-semimedium justify-center text-center items-center rounded-full cursor-pointer active:scale-[0.97] active:duration-150 active:ease-outExpo origin-center whitespace-nowrap inline-flex text-sm h-8 aspect-square"><div class="flex items-center min-w-0 gap-two justify-center"><div class="flex shrink-0 items-center justify-center size-4"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7999999999999998" stroke-linecap="round" stroke-linejoin="round" class="tabler-icon tabler-icon-copy "><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z"></path><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1"></path></svg></div></div></button></div><div class="-mt-xl"><div><div data-testid="code-language-indicator" class="text-quiet bg-offsetPlus py-xs px-sm inline-block rounded-br rounded-tl-[3px] font-thin">python</div></div><div class="pr-lg"><span><code><span><span class="token token">import</span><span> os
</span></span><span><span></span><span class="token token">from</span><span> langchain_openai </span><span class="token token">import</span><span> ChatOpenAI
</span></span><span><span></span><span class="token token">from</span><span> langchain_core</span><span class="token token punctuation">.</span><span>prompts </span><span class="token token">import</span><span> PromptTemplate
</span></span><span>
</span><span><span></span><span class="token token"># 建議從環境變數讀取您的 API 金鑰</span><span>
</span></span><span><span></span><span class="token token"># os.environ["OPENAI_API_KEY"] = "您的 OpenAI API 金鑰"</span><span>
</span></span><span>
</span><span><span></span><span class="token token"># 初始化模型</span><span>
</span></span><span><span>llm </span><span class="token token operator">=</span><span> ChatOpenAI</span><span class="token token punctuation">(</span><span>model</span><span class="token token operator">=</span><span class="token token">"gpt-4o"</span><span class="token token punctuation">,</span><span> temperature</span><span class="token token operator">=</span><span class="token token">0</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token"># --- 1. 標準提示 (沒有 CoT) ---</span><span>
</span></span><span><span>question </span><span class="token token operator">=</span><span></span><span class="token token">"小明在水果攤買了5個蘋果，之後他又買了3籃橘子，每籃有4個橘子。他總共買了多少個水果？"</span><span>
</span></span><span><span>standard_prompt </span><span class="token token operator">=</span><span> PromptTemplate</span><span class="token token punctuation">.</span><span>from_template</span><span class="token token punctuation">(</span><span class="token token">"{query}"</span><span class="token token punctuation">)</span><span>
</span></span><span><span>standard_chain </span><span class="token token operator">=</span><span> standard_prompt </span><span class="token token operator">|</span><span> llm
</span></span><span>
</span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"問題: </span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">question</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">"</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token">"--- 標準提示的回答 ---"</span><span class="token token punctuation">)</span><span>
</span></span><span><span>response_standard </span><span class="token token operator">=</span><span> standard_chain</span><span class="token token punctuation">.</span><span>invoke</span><span class="token token punctuation">(</span><span class="token token punctuation">{</span><span class="token token">"query"</span><span class="token token punctuation">:</span><span> question</span><span class="token token punctuation">}</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span>response_standard</span><span class="token token punctuation">.</span><span>content</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token">"-"</span><span></span><span class="token token operator">*</span><span></span><span class="token token">25</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token"># --- 2. 思維鏈提示 (Zero-Shot CoT) ---</span><span>
</span></span><span><span>cot_prompt_text </span><span class="token token operator">=</span><span></span><span class="token token triple-quoted-string">"""
</span></span><span class="token token triple-quoted-string">{query}
</span><span class="token token triple-quoted-string">讓我們一步一步地思考。
</span><span><span class="token token triple-quoted-string">"""</span><span>
</span></span><span><span>cot_prompt </span><span class="token token operator">=</span><span> PromptTemplate</span><span class="token token punctuation">.</span><span>from_template</span><span class="token token punctuation">(</span><span>cot_prompt_text</span><span class="token token punctuation">)</span><span>
</span></span><span><span>cot_chain </span><span class="token token operator">=</span><span> cot_prompt </span><span class="token token operator">|</span><span> llm
</span></span><span>
</span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token">"--- 思維鏈提示的回答 ---"</span><span class="token token punctuation">)</span><span>
</span></span><span><span>response_cot </span><span class="token token operator">=</span><span> cot_chain</span><span class="token token punctuation">.</span><span>invoke</span><span class="token token punctuation">(</span><span class="token token punctuation">{</span><span class="token token">"query"</span><span class="token token punctuation">:</span><span> question</span><span class="token token punctuation">}</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span>response_cot</span><span class="token token punctuation">.</span><span>content</span><span class="token token punctuation">)</span><span>
</span></span><span></span></code></span></div></div></div></pre>

## 4. 自我一致性提示 (Self-Consistency Prompting)

**說明：**

自我一致性是一種增強思維鏈提示效果的技術 。它的核心思想是：針對同一個問題，生成多個不同的推理路徑（思維鏈），然後選擇在這些路徑中出現最多次的答案作為最終結果 。這就像讓一群專家獨立思考同一個問題，然後採納共識最高的結論。這種方法可以有效減少因單一推理路徑出錯而導致的錯誤。[github**+1**](https://github.com/NirDiamant/Prompt_Engineering)

**Python 範例：**

這個範例模擬了自我一致性的過程。我們會多次向模型請求解決同一個問題，並採用不同的推理方式，然後使用 Python 的 `collections.Counter` 來統計哪個答案出現最頻繁 。[geeksforgeeks**+1**](https://www.geeksforgeeks.org/artificial-intelligence/self-consistency-prompting/)

<pre class="not-prose w-full rounded font-mono text-sm font-extralight"><div class="codeWrapper text-light selection:text-super selection:bg-super/10 bg-offset my-md relative flex flex-col rounded font-mono text-sm font-normal"><div class="translate-y-xs -translate-x-xs bottom-xl mb-xl sticky top-0 flex h-0 items-start justify-end"><button data-testid="copy-code-button" type="button" class="focus-visible:bg-offsetPlus hover:bg-offsetPlus text-quiet  hover:text-foreground dark:hover:bg-offsetPlus font-sans focus:outline-none outline-none outline-transparent transition duration-300 ease-out select-none items-center relative group/button font-semimedium justify-center text-center items-center rounded-full cursor-pointer active:scale-[0.97] active:duration-150 active:ease-outExpo origin-center whitespace-nowrap inline-flex text-sm h-8 aspect-square"><div class="flex items-center min-w-0 gap-two justify-center"><div class="flex shrink-0 items-center justify-center size-4"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7999999999999998" stroke-linecap="round" stroke-linejoin="round" class="tabler-icon tabler-icon-copy "><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z"></path><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1"></path></svg></div></div></button></div><div class="-mt-xl"><div><div data-testid="code-language-indicator" class="text-quiet bg-offsetPlus py-xs px-sm inline-block rounded-br rounded-tl-[3px] font-thin">python</div></div><div class="pr-lg"><span><code><span><span class="token token">import</span><span> os
</span></span><span><span></span><span class="token token">import</span><span> re
</span></span><span><span></span><span class="token token">from</span><span> collections </span><span class="token token">import</span><span> Counter
</span></span><span><span></span><span class="token token">from</span><span> openai </span><span class="token token">import</span><span> OpenAI
</span></span><span>
</span><span><span></span><span class="token token"># os.environ["OPENAI_API_KEY"] = "您的 OpenAI API 金鑰"</span><span>
</span></span><span><span>client </span><span class="token token operator">=</span><span> OpenAI</span><span class="token token punctuation">(</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token">def</span><span></span><span class="token token">self_consistency_prompting</span><span class="token token punctuation">(</span><span>query</span><span class="token token punctuation">,</span><span> num_responses</span><span class="token token operator">=</span><span class="token token">5</span><span class="token token punctuation">)</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token triple-quoted-string">"""
</span></span><span class="token token triple-quoted-string">    使用自我一致性提示來解決問題。
</span><span><span class="token token triple-quoted-string">    """</span><span>
</span></span><span><span>    prompt </span><span class="token token operator">=</span><span></span><span class="token token string-interpolation">f"""
</span></span><span><span class="token token string-interpolation">    問題：</span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">query</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">
</span></span><span class="token token string-interpolation">    請提供詳細的思考過程，並在最後一行以 "答案是：" 開頭給出最終答案。
</span><span><span class="token token string-interpolation">    """</span><span>
</span></span><span>  
</span><span><span>    responses </span><span class="token token operator">=</span><span></span><span class="token token punctuation">[</span><span class="token token punctuation">]</span><span>
</span></span><span><span></span><span class="token token">for</span><span> _ </span><span class="token token">in</span><span></span><span class="token token">range</span><span class="token token punctuation">(</span><span>num_responses</span><span class="token token punctuation">)</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token">try</span><span class="token token punctuation">:</span><span>
</span></span><span><span>            response </span><span class="token token operator">=</span><span> client</span><span class="token token punctuation">.</span><span>chat</span><span class="token token punctuation">.</span><span>completions</span><span class="token token punctuation">.</span><span>create</span><span class="token token punctuation">(</span><span>
</span></span><span><span>                model</span><span class="token token operator">=</span><span class="token token">"gpt-4o"</span><span class="token token punctuation">,</span><span>
</span></span><span><span>                messages</span><span class="token token operator">=</span><span class="token token punctuation">[</span><span class="token token punctuation">{</span><span class="token token">"role"</span><span class="token token punctuation">:</span><span></span><span class="token token">"user"</span><span class="token token punctuation">,</span><span></span><span class="token token">"content"</span><span class="token token punctuation">:</span><span> prompt</span><span class="token token punctuation">}</span><span class="token token punctuation">]</span><span class="token token punctuation">,</span><span>
</span></span><span><span>                temperature</span><span class="token token operator">=</span><span class="token token">0.7</span><span class="token token punctuation">,</span><span></span><span class="token token"># 使用較高的溫度以產生多樣化的推理路徑</span><span>
</span></span><span><span>                n</span><span class="token token operator">=</span><span class="token token">1</span><span>
</span></span><span><span></span><span class="token token punctuation">)</span><span>
</span></span><span><span>            responses</span><span class="token token punctuation">.</span><span>append</span><span class="token token punctuation">(</span><span>response</span><span class="token token punctuation">.</span><span>choices</span><span class="token token punctuation">[</span><span class="token token">0</span><span class="token token punctuation">]</span><span class="token token punctuation">.</span><span>message</span><span class="token token punctuation">.</span><span>content</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">except</span><span> Exception </span><span class="token token">as</span><span> e</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"請求 API 時發生錯誤: </span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">e</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">"</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">continue</span><span>
</span></span><span>
</span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token">"--- 模型的不同推理路徑 ---"</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">for</span><span> i</span><span class="token token punctuation">,</span><span> res </span><span class="token token">in</span><span></span><span class="token token">enumerate</span><span class="token token punctuation">(</span><span>responses</span><span class="token token punctuation">)</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"路徑 </span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">i</span><span class="token token string-interpolation interpolation operator">+</span><span class="token token string-interpolation interpolation">1</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">:\n</span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">res</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">\n"</span><span></span><span class="token token operator">+</span><span></span><span class="token token">"-"</span><span class="token token operator">*</span><span class="token token">15</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token"># 從每個回應中提取最終答案</span><span>
</span></span><span><span>    final_answers </span><span class="token token operator">=</span><span></span><span class="token token punctuation">[</span><span class="token token punctuation">]</span><span>
</span></span><span><span></span><span class="token token">for</span><span> res </span><span class="token token">in</span><span> responses</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token"># 使用正則表達式尋找 "答案是：" 後面的數字</span><span>
</span></span><span><span></span><span class="token token">match</span><span></span><span class="token token operator">=</span><span> re</span><span class="token token punctuation">.</span><span>search</span><span class="token token punctuation">(</span><span class="token token">r"答案是：\s*(\d+)"</span><span class="token token punctuation">,</span><span> res</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">if</span><span></span><span class="token token">match</span><span class="token token punctuation">:</span><span>
</span></span><span><span>            final_answers</span><span class="token token punctuation">.</span><span>append</span><span class="token token punctuation">(</span><span class="token token">int</span><span class="token token punctuation">(</span><span class="token token">match</span><span class="token token punctuation">.</span><span>group</span><span class="token token punctuation">(</span><span class="token token">1</span><span class="token token punctuation">)</span><span class="token token punctuation">)</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token">if</span><span></span><span class="token token">not</span><span> final_answers</span><span class="token token punctuation">:</span><span>
</span></span><span><span></span><span class="token token">return</span><span></span><span class="token token">"無法從任何回應中提取最終答案。"</span><span>
</span></span><span>
</span><span><span></span><span class="token token"># 使用 Counter 找到最一致的答案</span><span>
</span></span><span><span>    answer_counts </span><span class="token token operator">=</span><span> Counter</span><span class="token token punctuation">(</span><span>final_answers</span><span class="token token punctuation">)</span><span>
</span></span><span><span>    most_common_answer </span><span class="token token operator">=</span><span> answer_counts</span><span class="token token punctuation">.</span><span>most_common</span><span class="token token punctuation">(</span><span class="token token">1</span><span class="token token punctuation">)</span><span class="token token punctuation">[</span><span class="token token">0</span><span class="token token punctuation">]</span><span class="token token punctuation">[</span><span class="token token">0</span><span class="token token punctuation">]</span><span>
</span></span><span>  
</span><span><span></span><span class="token token">return</span><span> most_common_answer
</span></span><span>
</span><span><span></span><span class="token token"># 測試一個需要多步推理的問題</span><span>
</span></span><span><span>complex_query </span><span class="token token operator">=</span><span></span><span class="token token">"一個農場裡有雞和兔子，總共有35個頭和94隻腳。請問農場裡有多少隻兔子？"</span><span>
</span></span><span><span>final_answer </span><span class="token token operator">=</span><span> self_consistency_prompting</span><span class="token token punctuation">(</span><span>complex_query</span><span class="token token punctuation">,</span><span> num_responses</span><span class="token token operator">=</span><span class="token token">3</span><span class="token token punctuation">)</span><span>
</span></span><span>
</span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"\n--- 最終一致性答案 ---"</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"問題: </span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">complex_query</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">"</span><span class="token token punctuation">)</span><span>
</span></span><span><span></span><span class="token token">print</span><span class="token token punctuation">(</span><span class="token token string-interpolation">f"最一致的答案是: </span><span class="token token string-interpolation interpolation punctuation">{</span><span class="token token string-interpolation interpolation">final_answer</span><span class="token token string-interpolation interpolation punctuation">}</span><span class="token token string-interpolation">"</span><span class="token token punctuation">)</span><span>
</span></span><span></span></code></span></div></div></div></pre>

1. [https://mirascope.com/blog/prompt-engineering-examples](https://mirascope.com/blog/prompt-engineering-examples)
2. [https://www.geeksforgeeks.org/nlp/zero-shot-prompting/](https://www.geeksforgeeks.org/nlp/zero-shot-prompting/)
3. [https://plainenglish.io/blog/zero-shot-few-shot-and-chain-of-thought-prompt](https://plainenglish.io/blog/zero-shot-few-shot-and-chain-of-thought-prompt)
4. [https://www.promptpanda.io/resources/few-shot-prompting-explained-a-guide/](https://www.promptpanda.io/resources/few-shot-prompting-explained-a-guide/)
5. [https://www.linkedin.com/pulse/recipes-all-you-need-new-paradigm-ai-prompting-paul-g-thompson-4qg5e](https://www.linkedin.com/pulse/recipes-all-you-need-new-paradigm-ai-prompting-paul-g-thompson-4qg5e)
6. [https://www.promptingguide.ai/techniques/cot](https://www.promptingguide.ai/techniques/cot)
7. [https://www.codecademy.com/article/chain-of-thought-cot-prompting](https://www.codecademy.com/article/chain-of-thought-cot-prompting)
8. [https://github.com/NirDiamant/Prompt_Engineering](https://github.com/NirDiamant/Prompt_Engineering)
9. [https://www.geeksforgeeks.org/artificial-intelligence/self-consistency-prompting/](https://www.geeksforgeeks.org/artificial-intelligence/self-consistency-prompting/)
10. [https://python.useinstructor.com/prompting/ensembling/cosp/](https://python.useinstructor.com/prompting/ensembling/cosp/)
11. [https://arxiv.org/abs/2306.03799](https://arxiv.org/abs/2306.03799)
12. [https://arxiv.org/abs/2403.12488](https://arxiv.org/abs/2403.12488)
13. [https://www.sciencedirect.com/org/science/article/pii/S1438887124005600](https://www.sciencedirect.com/org/science/article/pii/S1438887124005600)
14. [https://www.sundeepteki.org/advice/the-definitive-guide-to-prompt-engineering-from-principles-to-production](https://www.sundeepteki.org/advice/the-definitive-guide-to-prompt-engineering-from-principles-to-production)
15. [https://arxiv.org/html/2404.01077v2](https://arxiv.org/html/2404.01077v2)
16. [https://aclanthology.org/2024.emnlp-main.1017/](https://aclanthology.org/2024.emnlp-main.1017/)
17. [https://thegradient.pub/prompting/](https://thegradient.pub/prompting/)
18. [https://www.youtube.com/watch?v=RL0cmE0dAF0](https://www.youtube.com/watch?v=RL0cmE0dAF0)
19. [https://realpython.com/practical-prompt-engineering/](https://realpython.com/practical-prompt-engineering/)
20. [https://platform.openai.com/docs/guides/prompt-engineering](https://platform.openai.com/docs/guides/prompt-engineering)
21. [https://www.geeksforgeeks.org/artificial-intelligence/instruction-prompting/](https://www.geeksforgeeks.org/artificial-intelligence/instruction-prompting/)
22. [https://www.helicone.ai/blog/chain-of-thought-prompting](https://www.helicone.ai/blog/chain-of-thought-prompting)
23. [https://python.langchain.com/docs/how_to/few_shot_examples/](https://python.langchain.com/docs/how_to/few_shot_examples/)

---

Other Prompt Paradigms
