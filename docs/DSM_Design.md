| State                   | Action                                              | Next State                                                                                                                |
| ----------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| OnReceiveMsg            | 1. Extract Keyword `<br>`2. CompareSentence       | 1. OnResponseMsg (if keyword matched)`<br>`2. OnGenFunnelChat (if keyword not matched)                                  |
| OnResponseMsg           | 1. Do DataQuery `<br>`2. Generate MD Content      | 1. OnDataQuery → OnGenMDContent (if need internal data query)`<br>`2. OnGenFunnelChat (if no need internal data query) |
| OnGenFunnelChat         | Generate Messages to guide customers to our product | OnGenMDContent                                                                                                            |
| OnGenMDContent          | Generate raw data (e.g., JSON) to markdown content  | OnGenMDContent                                                                                                            |
| OnDataQuery             | Perform internal data query                         | OnQueriedDataProcessing                                                                                                   |
| OnQueriedDataProcessing | Perform queried data postprocessing                 | OnSendFront                                                                                                               |
| OnSendFront             | Send data (markdown text) to browser                | OnWaitMsg                                                                                                                 |
| OnWaitMsg               | Wait for next message                               | OnReceiveMsg                                                                                                              |


{

"OnReceiveMsg": {

"description":"接收用戶消息狀態",

"actions": [

"ExtractKeyword",

"CompareSentence"

    ],

"next_states": {

"keyword_matched":"OnResponseMsg",

"keyword_not_matched":"OnGenFunnelChat"

    }

    },

"OnResponseMsg": {

"description":"回應消息狀態",

"actions": [

"DataQuery",

"GenerateMDContent"

    ],

"next_states": {

"need_data_query":"OnDataQuery",

"no_data_query":"OnGenFunnelChat"

    }

    },

"OnGenFunnelChat": {

"description":"生成漏斗式聊天狀態",

"actions": [

"Generate Messages to guide customers to our product"

    ],

"next_states": {

"default":"OnGenMDContent"

    }

    },

"OnGenMDContent": {

"description":"生成 Markdown 內容狀態",

"actions": [

"GenerateMDContent"

    ],

"next_states": {

"default":"OnGenMDContent"

    }

    },

"OnDataQuery": {

"description":"執行內部數據查詢狀態",

"actions": [

"DataQuery"

    ],

"next_states": {

"default":"OnQueriedDataProcessing"

    }

    },

"OnQueriedDataProcessing": {

"description":"查詢數據後處理狀態",

"actions": [

"DataPostprocessing"

    ],

"next_states": {

"default":"OnSendFront"

    }

    },

"OnSendFront": {

"description":"發送數據到前端狀態",

"actions": [

"SendDataToFront"

    ],

"next_states": {

"default":"OnWaitMsg"

    }

    },

"OnWaitMsg": {

"description":"等待下一條消息狀態",

"actions": [

"Wait for next message"

    ],

"next_states": {

"default":"OnReceiveMsg"

    }

    }

    }
