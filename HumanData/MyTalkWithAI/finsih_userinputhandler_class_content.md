role: you are a experienced, professional, well-known python programmer, please help to accomplish the followng task:

Description
讓我們回執行實際動作的Action上面，我們用一個例子來說明問題:

1. user input:請幫我介紹較為輕便容易攜帶的筆電

2. MGFD_SYS pass the message to UserInputHander，同時系統目前狀態轉為OnReceiveMsg.

3. 第一個問題出現:

a. UserInputHandler中必須具備extract keywords的能力，最直覺的模式就是以json 格式建立如以下的資料:

{

"輕便" : {

"同意詞":["重量較輕","容易攜帶"] ,

"metadata" : {"regex" : "補充與輕便相關同義字的regular expreesion",

"重量區間":"nodata"

}

}

這是我目前設計最直覺、容易使用、易於填加新屬性的表示法

請你針業這個表示法設計使用它的函式，函式功能如下：

def ChkKeyword(input sentence):

//your implmentation

return {"ret:yes", "kw":"輕便","區間":"nodata"} #yes 表示偵測到與輕便相關的詞
class UserInputHandler:
    def process_input(self, input_data: str) -> Dict[str, Any]:
        """處理用戶輸入"""
        pass
    
    def validate_input(self, input_data: str) -> bool:
        """驗證用戶輸入"""
        pass
    
    def parse_input(self, input_data: str) -> Dict[str, Any]:
        """解析用戶輸入"""
        pass
    
    def route_input(self, parsed_input: Dict[str, Any]) -> str:
        """路由用戶輸入"""
        pass