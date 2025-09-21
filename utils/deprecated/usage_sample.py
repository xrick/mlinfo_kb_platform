# 使用範例
from markdown_table_parser import MarkdownTableParser, fix_markdown_table

# 範例1：快速修正表格
broken_table = """
| Name | Age | City
|------|-----
| Alice | 25 |
| Bob | 30 | LA | Extra |
"""

fixed = fix_markdown_table(broken_table)
print("修正後的表格：")
print(fixed)

# 範例2：詳細的錯誤和警告資訊
parser = MarkdownTableParser()
fixed, errors, warnings = parser.parse_and_fix(broken_table)

print("\n錯誤：", errors)
print("警告：", warnings)

# 範例3：驗證表格
is_valid, validation_errors = parser.validate_markdown_table(fixed)
print("\n修正後的表格是否有效：", is_valid)