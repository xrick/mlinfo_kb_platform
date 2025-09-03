| State                  | Action                                                                 | Next State              |
|-------------------------|------------------------------------------------------------------------|-------------------------|
| OnReceiveMsg            | 1. Extract Keyword<br>2. CompareSentence                               | 1. OnResponseMsg (if keyword matched)<br>2. OnGenFunnelChat (if keyword not matched) |
| OnResponseMsg           | 1. Do DataQuery<br>2. Generate MD Content                             | 1. OnDataQuery → OnGenMDContent (if need internal data query)<br>2. OnGenFunnelChat (if no need internal data query) |
| OnGenFunnelChat         | Generate Messages to guide customers to our product                   | OnGenMDContent          |
| OnGenMDContent          | Generate raw data (e.g., JSON) to markdown content                    | OnGenMDContent          |
| OnDataQuery             | Perform internal data query                                           | OnQueriedDataProcessing |
| OnQueriedDataProcessing | Perform queried data postprocessing                                   | OnSendFront             |
| OnSendFront             | Send data (markdown text) to browser                                  | OnWaitMsg               |
| OnWaitMsg               | Wait for next message                                                 | OnReceiveMsg            |
