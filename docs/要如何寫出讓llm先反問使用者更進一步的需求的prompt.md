<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 要如何寫出讓llm先反問使用者更進一步的需求的prompt

撰寫讓大型語言模型（LLM）主動反問使用者需求的prompt，可以明確指示模型「請先提出相關問題以確認我的需求再進行回答」或「在回答前請詢問我更詳細的需求」等語句，讓互動更具釐清性。[^5]

## 操作重點

**有效提示語設計方法**

- 直接在prompt中加上類似「請先詢問我本次需求細節，並在我回覆後再進行回答」或「在開始回答前，先針對本任務主動提出3個需釐清的問題」。[^5]
- 可進一步指定提問的面向或數量，例如：「請用蘇格拉底式提問，幫助我釐清問題本質」、「在回答前請列出你認為最關鍵的三個追問」等，促使LLM自動反問。[^6]

**典型Prompt範例**
> 請扮演一位顧問，在回答任何要求前，務必先對我的需求提出三個後續釐清問題，等我回覆後再繼續你的分析。

> 你現在是設計師。遇到任務時，請先詢問我的設計用途、預算以及期待效果，確認細節後才開始給建議。

## 深入技巧

- 在prompt中用「從現在起，請你主動提出問題直到你有足夠資訊」這類連續式引導語，可促使LLM採多輪反問。[^6][^5]
- 配合角色指定、明確目標描述、格式要求，能讓模型在反問階段聚焦專業領域，不偏離主題。[^3][^4]

良好的反問式prompt設計有助於獲得更精準和客製化的AI答覆，也提升互動品質。
<span style="display:none">[^1][^10][^2][^7][^8][^9]</span>

<div style="text-align: center">⁂</div>

[^1]: https://vocus.cc/article/68a5a35cfd89780001ed90d0

[^2]: https://edge.aif.tw/application-react-prompting/

[^3]: https://vocus.cc/article/662e6517fd89780001353848

[^4]: https://www.threads.com/@peter_career_hack/post/DMb6TxENSuD/%E6%A0%B8%E5%BF%83%E6%8A%80%E8%A1%93%E4%BA%8C%E7%B5%90%E6%A7%8B%E5%8C%96%E8%88%87%E8%A7%92%E8%89%B2%E5%B0%8E%E5%90%91-prompt%E8%A6%81%E8%AE%93-llm-%E8%BC%B8%E5%87%BA%E6%9B%B4%E5%8F%AF%E6%8E%A7%E5%8F%AF%E9%A0%90%E6%B8%AC%E5%BE%9E%E8%A7%92%E8%89%B2%E8%A8%AD%E8%A8%88%E9%96%8B%E5%A7%8B%E6%98%AF%E6%9C%80%E7%A9%A9%E5%AE%9A%E7%9A%84%E5%81%9A%E6%B3%95%E6%AF%94%E8%B5%B7%E7%9B%B4%E6%8E%A5%E8%AA%AA%E5%B9%AB%E6%88%91%E6%95%B4%E7%90%86%E9%87%8D%E9%BB%9E%E6%9B%B4%E5%A5%BD%E7%9A%84%E6%96%B9%E5%BC%8F%E6%98%AF%E4%BD%A0%E6%98%AF%E4%B8%80%E4%BD%8D%E8%B3%87%E6%B7%B1%E6%9C%83%E8%AD%B0%E5%8A%A9%E7%90%86%E8%AB%8B%E4%BE%9D%E4%BB%A5%E4%B8%8B

[^5]: https://www.aiposthub.com/ai26prompts/

[^6]: https://hackmd.io/@4S8mEx0XRga0zuLJleLbMQ/HkuqTgFUJx

[^7]: https://www.accucrazy.com/prompt-engineering-info/

[^8]: https://solwen.ai/posts/what-is-prompt-engineering

[^9]: https://blog.infuseai.io/提問-prompt-的藝術-如何引導ai準確回答你的需求-d45fc79576d7

[^10]: https://blog.csdn.net/lyy2017175913/article/details/140170242

