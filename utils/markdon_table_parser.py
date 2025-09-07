import re
from typing import List, Tuple, Optional, Dict
from enum import Enum

class Alignment(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"

class MarkdownTableParser:
    """Markdown 表格解析器，具備錯誤檢測和自動修正功能"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def parse_and_fix(self, markdown_text: str) -> Tuple[str, List[str], List[str]]:
        """
        解析並修正 Markdown 表格
        
        Args:
            markdown_text: Markdown 表格文字
            
        Returns:
            (修正後的表格, 錯誤列表, 警告列表)
        """
        self.errors = []
        self.warnings = []
        
        # 預處理：移除前後空白
        lines = [line.strip() for line in markdown_text.strip().split('\n') if line.strip()]
        
        if not lines:
            self.errors.append("輸入為空")
            return "", self.errors, self.warnings
        
        # 檢測並修正表格
        table_data = self._detect_table_structure(lines)
        if not table_data:
            return "", self.errors, self.warnings
        
        # 修正表格
        fixed_table = self._fix_table(table_data)
        
        # 生成修正後的 Markdown
        return self._generate_markdown(fixed_table), self.errors, self.warnings
    
    def _detect_table_structure(self, lines: List[str]) -> Optional[Dict]:
        """檢測表格結構"""
        if len(lines) < 2:
            self.errors.append("表格至少需要兩行（標題行和分隔行）")
            return None
        
        # 尋找可能的標題行和分隔行
        header_idx = -1
        separator_idx = -1
        
        for i, line in enumerate(lines):
            if self._is_separator_line(line):
                separator_idx = i
                header_idx = i - 1 if i > 0 else -1
                break
        
        if separator_idx == -1:
            # 嘗試修正：假設第二行應該是分隔行
            if len(lines) >= 2:
                self.warnings.append("未找到有效的分隔行，嘗試自動生成")
                header_idx = 0
                separator_idx = 1
                # 根據標題行生成分隔行
                header_cells = self._parse_cells(lines[0])
                separator = self._generate_separator_line(len(header_cells))
                lines.insert(1, separator)
            else:
                self.errors.append("無法識別表格結構")
                return None
        
        if header_idx == -1:
            self.errors.append("缺少標題行")
            return None
        
        # 解析表格
        header_line = lines[header_idx]
        separator_line = lines[separator_idx]
        body_lines = lines[separator_idx + 1:]
        
        return {
            'header': self._parse_cells(header_line),
            'separator': separator_line,
            'alignments': self._parse_alignments(separator_line),
            'body': [self._parse_cells(line) for line in body_lines if self._is_table_line(line)]
        }
    
    def _is_table_line(self, line: str) -> bool:
        """檢查是否為表格行"""
        return '|' in line
    
    def _is_separator_line(self, line: str) -> bool:
        """檢查是否為分隔行"""
        if '|' not in line:
            return False
        
        cells = self._parse_cells(line)
        if not cells:
            return False
        
        # 檢查每個單元格是否符合分隔符格式
        separator_pattern = re.compile(r'^:?-+:?$')
        return all(separator_pattern.match(cell.strip()) for cell in cells)
    
    def _parse_cells(self, line: str) -> List[str]:
        """解析表格單元格"""
        # 移除首尾的管道符號
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        # 分割單元格
        cells = [cell.strip() for cell in line.split('|')]
        return cells
    
    def _parse_alignments(self, separator_line: str) -> List[Alignment]:
        """解析對齊方式"""
        cells = self._parse_cells(separator_line)
        alignments = []
        
        for cell in cells:
            cell = cell.strip()
            if cell.startswith(':') and cell.endswith(':'):
                alignments.append(Alignment.CENTER)
            elif cell.endswith(':'):
                alignments.append(Alignment.RIGHT)
            else:
                alignments.append(Alignment.LEFT)
        
        return alignments
    
    def _fix_table(self, table_data: Dict) -> Dict:
        """修正表格數據"""
        if not table_data:
            return table_data
        
        # 確定列數（以標題行為準）
        num_columns = len(table_data['header'])
        
        # 修正對齊方式數量
        if len(table_data['alignments']) != num_columns:
            self.warnings.append(f"對齊符號數量不匹配，已自動修正")
            # 補充或截斷對齊方式
            if len(table_data['alignments']) < num_columns:
                table_data['alignments'].extend([Alignment.LEFT] * (num_columns - len(table_data['alignments'])))
            else:
                table_data['alignments'] = table_data['alignments'][:num_columns]
        
        # 修正每一行的列數
        fixed_body = []
        for i, row in enumerate(table_data['body']):
            if len(row) != num_columns:
                self.warnings.append(f"第 {i+3} 行的列數不正確，已自動修正")
                if len(row) < num_columns:
                    # 補充空單元格
                    row.extend([''] * (num_columns - len(row)))
                else:
                    # 截斷多餘的單元格
                    row = row[:num_columns]
            fixed_body.append(row)
        
        table_data['body'] = fixed_body
        return table_data
    
    def _generate_separator_line(self, num_columns: int, alignments: Optional[List[Alignment]] = None) -> str:
        """生成分隔行"""
        if alignments is None:
            alignments = [Alignment.LEFT] * num_columns
        
        separators = []
        for alignment in alignments:
            if alignment == Alignment.CENTER:
                separators.append(':---:')
            elif alignment == Alignment.RIGHT:
                separators.append('---:')
            else:
                separators.append('---')
        
        return '| ' + ' | '.join(separators) + ' |'
    
    def _generate_markdown(self, table_data: Dict) -> str:
        """生成修正後的 Markdown 表格"""
        if not table_data:
            return ""
        
        lines = []
        
        # 生成標題行
        header_line = '| ' + ' | '.join(table_data['header']) + ' |'
        lines.append(header_line)
        
        # 生成分隔行
        separator_line = self._generate_separator_line(len(table_data['header']), table_data['alignments'])
        lines.append(separator_line)
        
        # 生成內容行
        for row in table_data['body']:
            body_line = '| ' + ' | '.join(row) + ' |'
            lines.append(body_line)
        
        return '\n'.join(lines)
    
    def validate_markdown_table(self, markdown_text: str) -> Tuple[bool, List[str]]:
        """
        驗證 Markdown 表格是否有效
        
        Returns:
            (是否有效, 錯誤訊息列表)
        """
        errors = []
        lines = [line.strip() for line in markdown_text.strip().split('\n') if line.strip()]
        
        if len(lines) < 2:
            errors.append("表格至少需要兩行")
            return False, errors
        
        # 檢查是否有分隔行
        has_separator = False
        separator_idx = -1
        for i, line in enumerate(lines):
            if self._is_separator_line(line):
                has_separator = True
                separator_idx = i
                break
        
        if not has_separator:
            errors.append("缺少分隔行")
            return False, errors
        
        if separator_idx == 0:
            errors.append("分隔行不能是第一行")
            return False, errors
        
        # 檢查列數一致性
        header_cells = self._parse_cells(lines[separator_idx - 1])
        num_columns = len(header_cells)
        
        for i, line in enumerate(lines):
            if i == separator_idx:
                continue
            if self._is_table_line(line):
                cells = self._parse_cells(line)
                if len(cells) != num_columns:
                    errors.append(f"第 {i+1} 行的列數（{len(cells)}）與標題行（{num_columns}）不一致")
        
        return len(errors) == 0, errors


def fix_markdown_table(markdown_text: str) -> str:
    """
    便利函數：直接修正 Markdown 表格
    
    Args:
        markdown_text: 需要修正的 Markdown 表格
        
    Returns:
        修正後的 Markdown 表格
    """
    parser = MarkdownTableParser()
    fixed, errors, warnings = parser.parse_and_fix(markdown_text)
    
    if errors:
        print("錯誤：")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("警告：")
        for warning in warnings:
            print(f"  - {warning}")
    
    return fixed