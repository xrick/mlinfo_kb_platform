import json
import pandas as pd
from prettytable import PrettyTable
from ..base_service import BaseService
from ...RAG.DB.MilvusQuery import MilvusQuery
from ...RAG.DB.DuckDBQuery import DuckDBQuery
from ...RAG.LLM.LLMInitializer import LLMInitializer
from .multichat import MultichatManager, ChatTemplateManager
from .multichat.funnel_manager import FunnelConversationManager, FunnelQueryType, FunnelFlowType
import logging
import re
from typing import Dict, Any

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 全域變數：存儲所有可用的modelname (動態從數據庫獲取)
AVAILABLE_MODELNAMES = []

def _get_available_modelnames_from_db():
    """從數據庫動態獲取可用的modelname"""
    try:
        from config import DB_PATH
        import duckdb
        
        conn = duckdb.connect(str(DB_PATH))
        # 排除測試資料和空值，只獲取有效的modelname
        result = conn.execute("""
            SELECT DISTINCT modelname 
            FROM nbtypes 
            WHERE modelname IS NOT NULL 
              AND modelname != '' 
              AND modelname != 'Test Model'
            ORDER BY modelname
        """).fetchall()
        conn.close()
        
        modelnames = [row[0] for row in result]
        logging.info(f"從數據庫獲取到的modelname: {len(modelnames)} 個")
        return modelnames
    except Exception as e:
        logging.error(f"獲取數據庫modelname失敗: {e}")
        # 如果數據庫查詢失敗，返回默認值
        return [
            'AB819-S: FP6', 'AG958', 'AG958P', 'AG958V', 'AHP819: FP7R2',
            'AHP839', 'AHP958', 'AKK839', 'AMD819-S: FT6', 'AMD819: FT6',
            'APX819: FP7R2', 'APX839', 'APX958', 'ARB819-S: FP7R2', 'ARB839'
        ]

# 初始化時從數據庫獲取可用的modelname
AVAILABLE_MODELNAMES = _get_available_modelnames_from_db()

# 全域變數：存儲所有可用的modeltype (動態從數據庫獲取)
AVAILABLE_MODELTYPES = []

def _get_available_modeltypes_from_db():
    """從數據庫動態獲取可用的modeltype"""
    try:
        from config import DB_PATH
        import duckdb
        
        conn = duckdb.connect(str(DB_PATH))
        result = conn.execute('SELECT DISTINCT modeltype FROM nbtypes ORDER BY modeltype').fetchall()
        conn.close()
        
        modeltypes = [row[0] for row in result]
        logging.info(f"從數據庫獲取到的modeltype: {modeltypes}")
        return modeltypes
    except Exception as e:
        logging.error(f"獲取數據庫modeltype失敗: {e}")
        # 如果數據庫查詢失敗，返回默認值
        return ['819', '839', '928', '958', '960', 'AC01']

# 初始化時從數據庫獲取可用的modeltype
AVAILABLE_MODELTYPES = _get_available_modeltypes_from_db()

'''
[
    'modeltype', 'version', 'modelname', 'mainboard', 'devtime',
    'pm', 'structconfig', 'lcd', 'touchpanel', 'iointerface', 
    'ledind', 'powerbutton', 'keyboard', 'webcamera', 'touchpad', 
    'fingerprint', 'audio', 'battery', 'cpu', 'gpu', 'memory', 
    'lcdconnector', 'storage', 'wifislot', 'thermal', 'tpm', 'rtc', 
    'wireless', 'lan', 'bluetooth', 'softwareconfig', 'ai', 'accessory', 
    'certfications', 'otherfeatures'
]
'''
class SalesAssistantService(BaseService):
    def __init__(self):
        # 初始化 LLM
        self.llm_initializer = LLMInitializer()
        self.llm = self.llm_initializer.get_llm()
        
        self.milvus_query = MilvusQuery(collection_name="sales_notebook_specs")
        
        # 使用config中的DB_PATH確保路徑正確
        from config import DB_PATH
        self.duckdb_query = DuckDBQuery(db_file=str(DB_PATH))
        
        self.prompt_template = self._load_prompt_template("sales_rag_app/libs/services/sales_assistant/prompts/sales_prompt.txt")
        
        # 載入關鍵字配置
        self.intent_keywords = self._load_intent_keywords("sales_rag_app/libs/services/sales_assistant/prompts/query_keywords.json")
        
        # 初始化多輪對話管理器
        self.multichat_manager = MultichatManager()
        self.chat_template_manager = ChatTemplateManager()
        
        # 初始化漏斗對話管理器
        self.funnel_manager = FunnelConversationManager()
        
        # ★ 修正點 1：修正 spec_fields 列表，使其與 .xlsx 檔案的標題列完全一致
        self.spec_fields = [
            'modeltype', 'version', 'modelname', 'mainboard', 'devtime',
            'pm', 'structconfig', 'lcd', 'touchpanel', 'iointerface', 
            'ledind', 'powerbutton', 'keyboard', 'webcamera', 'touchpad', 
            'fingerprint', 'audio', 'battery', 'cpu', 'gpu', 'memory', 
            'lcdconnector', 'storage', 'wifislot', 'thermal', 'tpm', 'rtc', 
            'wireless', 'lan', 'bluetooth', 'softwareconfig', 'ai', 'accessory', 
            'certfications', 'otherfeatures'
        ]

    def _load_prompt_template(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_intent_keywords(self, path: str) -> dict:
        """
        載入查詢意圖關鍵字配置
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logging.info(f"成功載入關鍵字配置: {list(config.get('intent_keywords', {}).keys())}")
                return config.get('intent_keywords', {})
        except FileNotFoundError:
            logging.error(f"關鍵字配置文件不存在: {path}")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"關鍵字配置文件格式錯誤: {e}")
            return {}
        except Exception as e:
            logging.error(f"載入關鍵字配置時發生錯誤: {e}")
            return {}

    def get_intent_keywords(self) -> dict:
        """
        獲取當前載入的關鍵字配置
        """
        return self.intent_keywords

    def add_intent_keyword(self, intent_name: str, keyword: str) -> bool:
        """
        為指定意圖添加關鍵字
        """
        try:
            if intent_name in self.intent_keywords:
                if keyword not in self.intent_keywords[intent_name]["keywords"]:
                    self.intent_keywords[intent_name]["keywords"].append(keyword)
                    logging.info(f"為意圖 '{intent_name}' 添加關鍵字: {keyword}")
                    return True
                else:
                    logging.warning(f"關鍵字 '{keyword}' 已存在於意圖 '{intent_name}' 中")
                    return False
            else:
                logging.error(f"意圖 '{intent_name}' 不存在")
                return False
        except Exception as e:
            logging.error(f"添加關鍵字時發生錯誤: {e}")
            return False

    def remove_intent_keyword(self, intent_name: str, keyword: str) -> bool:
        """
        從指定意圖中移除關鍵字
        """
        try:
            if intent_name in self.intent_keywords:
                if keyword in self.intent_keywords[intent_name]["keywords"]:
                    self.intent_keywords[intent_name]["keywords"].remove(keyword)
                    logging.info(f"從意圖 '{intent_name}' 移除關鍵字: {keyword}")
                    return True
                else:
                    logging.warning(f"關鍵字 '{keyword}' 不存在於意圖 '{intent_name}' 中")
                    return False
            else:
                logging.error(f"意圖 '{intent_name}' 不存在")
                return False
        except Exception as e:
            logging.error(f"移除關鍵字時發生錯誤: {e}")
            return False

    def save_intent_keywords(self, path: str = None) -> bool:
        """
        保存關鍵字配置到檔案
        """
        try:
            if path is None:
                path = "sales_rag_app/libs/services/sales_assistant/prompts/query_keywords.json"
            
            config = {"intent_keywords": self.intent_keywords}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logging.info(f"關鍵字配置已保存到: {path}")
            return True
        except Exception as e:
            logging.error(f"保存關鍵字配置時發生錯誤: {e}")
            return False

    def reload_intent_keywords(self, path: str = None) -> bool:
        """
        重新載入關鍵字配置
        """
        try:
            if path is None:
                path = "sales_rag_app/libs/services/sales_assistant/prompts/query_keywords.json"
            
            new_keywords = self._load_intent_keywords(path)
            if new_keywords:
                self.intent_keywords = new_keywords
                logging.info("關鍵字配置重新載入成功")
                return True
            else:
                logging.error("重新載入關鍵字配置失敗")
                return False
        except Exception as e:
            logging.error(f"重新載入關鍵字配置時發生錯誤: {e}")
            return False

    def _create_beautiful_markdown_table(self, comparison_table: list | dict, model_names: list) -> str:
        """
        支援 dict of lists 且自動轉置為「型號為欄，規格為列」的 markdown 表格
        """
        try:
            # 如果是 dict of lists 格式，且有 "Model" 或 "Device Model" 欄位，則自動轉置
            if isinstance(comparison_table, dict):
                # 檢查是否有模型欄位
                model_key = None
                for key in comparison_table.keys():
                    if key.lower() in ["model", "device model", "modelname", "model_type"]:
                        model_key = key
                        break
                
                if model_key:
                    models = comparison_table[model_key]
                    spec_keys = [k for k in comparison_table.keys() if k != model_key]
                    # 產生 list of dicts 格式
                    new_table = []
                    for spec in spec_keys:
                        row = {"feature": spec}
                        for idx, model in enumerate(models):
                            value = comparison_table[spec][idx] if idx < len(comparison_table[spec]) else "N/A"
                            row[model] = value
                        new_table.append(row)
                    comparison_table = new_table
                    model_names = models
                else:
                    # 如果沒有明確的模型欄位，嘗試從其他欄位推斷
                    # 假設第一個欄位是模型名稱
                    first_key = list(comparison_table.keys())[0]
                    if isinstance(comparison_table[first_key], list):
                        models = comparison_table[first_key]
                        spec_keys = [k for k in comparison_table.keys() if k != first_key]
                        new_table = []
                        for spec in spec_keys:
                            row = {"feature": spec}
                            for idx, model in enumerate(models):
                                value = comparison_table[spec][idx] if idx < len(comparison_table[spec]) else "N/A"
                                row[model] = value
                            new_table.append(row)
                        comparison_table = new_table
                        model_names = models
                    else:
                        # 處理簡單的字典格式：{"特征": "对比", "AG958": "v1.0", "APX958": "v2.0"}
                        logging.info("檢測到簡單字典格式，轉換為 list of dicts")
                        keys = list(comparison_table.keys())
                        if len(keys) >= 2:
                            # 第一個鍵通常是特徵名稱，其他鍵是模型名稱
                            feature_key = keys[0]
                            model_keys = keys[1:]
                            
                            # 創建單行表格
                            row = {"feature": comparison_table[feature_key]}
                            for model_key in model_keys:
                                row[model_key] = comparison_table[model_key]
                            
                            comparison_table = [row]
                            model_names = model_keys

            # 確保 comparison_table 是 list of dicts 格式
            if not isinstance(comparison_table, list):
                logging.error(f"comparison_table 格式不正確: {type(comparison_table)}")
                return "表格格式錯誤"

            # 產生 markdown 表格
            header = "| **規格項目** |" + "".join([f" **{name}** |" for name in model_names])
            separator = "| --- |" + " --- |" * len(model_names)
            rows = []
            for row in comparison_table:
                if not isinstance(row, dict):
                    logging.error(f"表格行格式不正確: {type(row)}")
                    continue
                    
                feature = row.get("feature", "N/A")
                row_str = f"| **{feature}** |"
                for model_name in model_names:
                    value = row.get(model_name, "N/A")
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    row_str += f" {value_str} |"
                rows.append(row_str)
            table_lines = [header, separator] + rows
            return "\n".join(table_lines)
        except Exception as e:
            logging.error(f"創建美化表格失敗: {e}", exc_info=True)
            return "表格生成失敗"

    def _create_simple_markdown_table(self, comparison_table: list, model_names: list) -> str:
        """
        創建簡單的 markdown 表格作為備用
        """
        try:
            # 創建標題行
            header = "| **規格項目** |"
            separator = "| --- |"
            
            for name in model_names:
                header += f" **{name}** |"
                separator += " --- |"
            
            # 創建數據行
            rows = []
            for row in comparison_table:
                feature = row.get("feature", "N/A")
                row_str = f"| {feature} |"
                for model_name in model_names:
                    value = row.get(model_name, "N/A")
                    row_str += f" {value} |"
                rows.append(row_str)
            
            # 組合表格
            table_lines = [header, separator] + rows
            return "\n".join(table_lines)
            
        except Exception as e:
            logging.error(f"創建簡單表格也失敗: {e}")
            return "表格生成失敗"

    def _format_response_with_beautiful_table(self, answer_summary: str | dict, comparison_table: list, model_names: list) -> dict:
        """
        格式化回應，包含美化的 markdown 表格
        """
        logging.info(f"_format_response_with_beautiful_table 被調用")
        logging.info(f"answer_summary 類型: {type(answer_summary)}, 值: {answer_summary}")
        logging.info(f"comparison_table 類型: {type(comparison_table)}, 值: {comparison_table}")
        logging.info(f"model_names: {model_names}")
        
        try:
            # 如果 answer_summary 是字典，保持其字典格式
            if isinstance(answer_summary, dict):
                logging.info("answer_summary 是字典格式，保持字典格式")
                # 創建美化的 markdown 表格
                beautiful_table = self._create_beautiful_markdown_table(comparison_table, model_names)
                
                # 檢查表格是否創建成功
                if beautiful_table == "表格格式錯誤" or beautiful_table == "表格生成失敗":
                    # 如果美化表格失敗，嘗試創建簡單表格
                    logging.warning("美化表格創建失敗，嘗試簡單表格")
                    simple_table = self._create_simple_markdown_table(comparison_table, model_names)
                    
                    result = {
                        "answer_summary": answer_summary,  # 保持字典格式
                        "comparison_table": comparison_table,
                        "beautiful_table": simple_table
                    }
                    logging.info(f"美化表格失敗，使用簡單表格，返回結果: {result}")
                    return result
                
                result = {
                    "answer_summary": answer_summary,  # 保持字典格式
                    "comparison_table": comparison_table,
                    "beautiful_table": beautiful_table
                }
                logging.info(f"字典格式處理成功，返回結果: {result}")
                return result
            
            # 如果 comparison_table 是字典格式，先轉換為 list of dicts 格式
            if isinstance(comparison_table, dict):
                logging.info("檢測到字典格式的 comparison_table，正在轉換為 list of dicts 格式")
                converted_table = self._convert_dict_to_list_of_dicts(comparison_table, answer_summary)
                if converted_table:
                    # 創建美化的 markdown 表格
                    beautiful_table = self._create_beautiful_markdown_table(converted_table, model_names)
                    
                    # 不將表格添加到 answer_summary 中，讓前端處理
                    result = {
                        "answer_summary": answer_summary,  # 保持原始格式
                        "comparison_table": converted_table,  # 返回轉換後的表格
                        "beautiful_table": beautiful_table
                    }
                    logging.info(f"字典格式轉換成功，返回結果: {result}")
                    return result
                else:
                    # 如果轉換失敗，使用改進的字典表格創建方法
                    beautiful_table = self._create_simple_table_from_dict_improved(comparison_table, answer_summary)
                    
                    # 不將表格添加到 answer_summary 中，讓前端處理
                    result = {
                        "answer_summary": answer_summary,  # 保持原始格式
                        "comparison_table": comparison_table,  # 保持原始格式
                        "beautiful_table": beautiful_table
                    }
                    logging.info(f"字典格式轉換失敗，使用備用方法，返回結果: {result}")
                    return result
            
            # 創建美化的 markdown 表格
            beautiful_table = self._create_beautiful_markdown_table(comparison_table, model_names)
            
            # 檢查表格是否創建成功
            if beautiful_table == "表格格式錯誤" or beautiful_table == "表格生成失敗":
                # 如果美化表格失敗，嘗試創建簡單表格
                logging.warning("美化表格創建失敗，嘗試簡單表格")
                simple_table = self._create_simple_markdown_table(comparison_table, model_names)
                
                # 不將表格添加到 answer_summary 中，讓前端處理
                result = {
                    "answer_summary": answer_summary,  # 保持原始格式
                    "comparison_table": comparison_table,
                    "beautiful_table": simple_table
                }
                logging.info(f"美化表格失敗，使用簡單表格，返回結果: {result}")
                return result
            
            # 不將表格添加到 answer_summary 中，讓前端處理
            result = {
                "answer_summary": answer_summary,  # 保持原始格式
                "comparison_table": comparison_table,
                "beautiful_table": beautiful_table
            }
            logging.info(f"標準處理成功，返回結果: {result}")
            return result
            
        except Exception as e:
            logging.error(f"格式化回應失敗: {e}", exc_info=True)
            # 返回基本的錯誤回應
            result = {
                "answer_summary": f"{answer_summary}\n\n表格生成失敗，請稍後再試。",
                "comparison_table": comparison_table,
                "beautiful_table": "表格生成失敗"
            }
            logging.info(f"發生異常，返回錯誤結果: {result}")
            return result

    def _convert_dict_to_list_of_dicts(self, comparison_dict: dict, answer_summary=None) -> list:
        """
        將字典格式的比較表格轉換為 list of dicts 格式
        """
        try:
            if not comparison_dict:
                logging.warning("comparison_dict 為空")
                return []
            
            logging.info(f"開始轉換字典格式，輸入數據: {comparison_dict}")
            
            # 檢查是否包含 main_differences 結構
            if answer_summary and isinstance(answer_summary, dict) and 'main_differences' in answer_summary:
                logging.info("檢測到 main_differences 結構")
                # 使用 main_differences 中的 category 作為 feature names
                main_differences = answer_summary['main_differences']
                converted_table = []
                
                for diff in main_differences:
                    if isinstance(diff, dict):
                        category = diff.get('category', '未知項目')
                        row = {"feature": category}
                        
                        # 從 comparison_dict 中提取對應的值
                        for model_name in comparison_dict.keys():
                            if model_name != "Feature":  # 跳過 Feature 欄位
                                # 找到對應的索引
                                if "Feature" in comparison_dict:
                                    try:
                                        feature_index = comparison_dict["Feature"].index(category)
                                        if model_name in comparison_dict and feature_index < len(comparison_dict[model_name]):
                                            row[model_name] = comparison_dict[model_name][feature_index]
                                        else:
                                            row[model_name] = "N/A"
                                    except ValueError:
                                        row[model_name] = "N/A"
                                else:
                                    row[model_name] = "N/A"
                        
                        converted_table.append(row)
                
                logging.info(f"main_differences 轉換結果: {converted_table}")
                return converted_table
            
            # 處理標準字典格式：第一個鍵包含特徵名稱，其他鍵是模型名稱
            keys = list(comparison_dict.keys())
            logging.info(f"字典鍵: {keys}")
            
            if len(keys) >= 2:
                # 檢查第一個鍵是否包含特徵名稱列表
                first_key = keys[0]
                logging.info(f"第一個鍵: {first_key}, 值類型: {type(comparison_dict[first_key])}")
                
                # ★ 修正點：檢查第一個鍵是否是 "Model" 或 "modelname"
                if first_key.lower() in ["model", "modelname"] and isinstance(comparison_dict[first_key], list):
                    logging.info(f"檢測到 {first_key} 作為第一個鍵，調整轉換邏輯")
                    models = comparison_dict[first_key]
                    spec_keys = keys[1:]  # 其他鍵都是規格項目
                    
                    logging.info(f"模型列表: {models}")
                    logging.info(f"規格項目: {spec_keys}")
                    
                    converted_table = []
                    for spec_key in spec_keys:
                        row = {"feature": spec_key}
                        for i, model in enumerate(models):
                            if i < len(comparison_dict[spec_key]):
                                # 清理規格值，移除末尾的模型名稱
                                value = comparison_dict[spec_key][i]
                                if isinstance(value, str) and f" - {model}" in value:
                                    value = value.replace(f" - {model}", "").strip()
                                row[model] = value
                            else:
                                row[model] = "N/A"
                        converted_table.append(row)
                    
                    logging.info(f"{first_key} 鍵格式轉換結果: {converted_table}")
                    return converted_table
                
                elif isinstance(comparison_dict[first_key], list):
                    features = comparison_dict[first_key]
                    model_names = keys[1:]  # 其他鍵都是模型名稱
                    
                    logging.info(f"特徵列表: {features}")
                    logging.info(f"模型名稱: {model_names}")
                    
                    converted_table = []
                    for i, feature in enumerate(features):
                        row = {"feature": feature}
                        for model_name in model_names:
                            if i < len(comparison_dict[model_name]):
                                row[model_name] = comparison_dict[model_name][i]
                            else:
                                row[model_name] = "N/A"
                        converted_table.append(row)
                    
                    logging.info(f"標準字典格式轉換結果: {converted_table}")
                    return converted_table
            
            # 處理嵌套結構：主要差异 -> [{'型号': 'AG958', '特性': '16.1英寸', ...}, ...]
            for main_key, main_value in comparison_dict.items():
                if isinstance(main_value, list) and len(main_value) > 0:
                    # 檢查是否為模型規格列表
                    if isinstance(main_value[0], dict):
                        logging.info("檢測到嵌套結構")
                        
                        # 特殊處理：如果第一個字典包含 "Model" 和 "Specification" 鍵
                        if "Model" in main_value[0] and "Specification" in main_value[0]:
                            logging.info("檢測到 Model/Specification 格式")
                            converted_table = []
                            for item in main_value:
                                if isinstance(item, dict) and "Model" in item and "Specification" in item:
                                    # 創建一行顯示規格
                                    spec_row = {"feature": "Memory Specification", item["Model"]: item["Specification"]}
                                    converted_table.append(spec_row)
                            logging.info(f"Model/Specification 格式轉換結果: {converted_table}")
                            return converted_table
                        
                        # 提取所有可能的規格項目
                        all_specs = set()
                        for model_spec in main_value:
                            if isinstance(model_spec, dict):
                                all_specs.update(model_spec.keys())
                        
                        # 排除模型名稱相關的欄位
                        model_name_keys = {'型号', 'model', 'modelname', 'device_model'}
                        spec_keys = [key for key in all_specs if key not in model_name_keys]
                        
                        converted_table = []
                        for spec_key in spec_keys:
                            row = {"feature": spec_key}
                            for model_spec in main_value:
                                if isinstance(model_spec, dict):
                                    # 嘗試找到模型名稱
                                    model_name = None
                                    for name_key in model_name_keys:
                                        if name_key in model_spec:
                                            model_name = model_spec[name_key]
                                            break
                                    
                                    if not model_name:
                                        # 如果沒有找到模型名稱，使用索引
                                        model_name = f"Model_{main_value.index(model_spec) + 1}"
                                    
                                    # 獲取規格值
                                    value = model_spec.get(spec_key, "N/A")
                                    row[model_name] = value
                            
                            converted_table.append(row)
                        
                        logging.info(f"嵌套結構轉換結果: {converted_table}")
                        return converted_table
            
            # 標準處理：假設第一個欄位是 Feature，其他欄位是模型名稱
            if "Feature" in comparison_dict:
                logging.info("檢測到 Feature 欄位")
                features = comparison_dict["Feature"]
                model_names = [k for k in comparison_dict.keys() if k != "Feature"]
                
                converted_table = []
                for i, feature in enumerate(features):
                    row = {"feature": feature}
                    for model_name in model_names:
                        if i < len(comparison_dict[model_name]):
                            row[model_name] = comparison_dict[model_name][i]
                        else:
                            row[model_name] = "N/A"
                    converted_table.append(row)
                
                logging.info(f"Feature 欄位轉換結果: {converted_table}")
                return converted_table
            
            logging.warning("無法識別字典格式，返回空列表")
            return []
            
        except Exception as e:
            logging.error(f"轉換字典格式失敗: {e}")
            return []

    def _create_simple_table_from_dict(self, comparison_dict: dict) -> str:
        """
        從字典格式創建簡單的 markdown 表格
        """
        try:
            if not comparison_dict:
                return "無比較數據"
            
            # 找到模型名稱欄位
            model_key = None
            for key in comparison_dict.keys():
                if key.lower() in ["model", "device model", "modelname", "model_type"]:
                    model_key = key
                    break
            
            if not model_key:
                # 如果沒有找到模型欄位，使用第一個欄位
                model_key = list(comparison_dict.keys())[0]
            
            models = comparison_dict[model_key]
            spec_keys = [k for k in comparison_dict.keys() if k != model_key]
            
            if not models or not spec_keys:
                return "數據格式不完整"
            
            # 創建表格 - 使用模型名稱作為列標題
            header = "| **規格項目** |" + "".join([f" **{model}** |" for model in models])
            separator = "| --- |" + " --- |" * len(models)
            
            rows = []
            for spec in spec_keys:
                row_str = f"| **{spec}** |"
                for idx, model in enumerate(models):
                    value = comparison_dict[spec][idx] if idx < len(comparison_dict[spec]) else "N/A"
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    row_str += f" {value_str} |"
                rows.append(row_str)
            
            table_lines = [header, separator] + rows
            return "\n".join(table_lines)
            
        except Exception as e:
            logging.error(f"創建簡單表格失敗: {e}")
            return "表格生成失敗"

    def _fix_json_format(self, json_content: str) -> str:
        """
        修復常見的 JSON 格式問題
        """
        try:
            fixed = json_content.strip()
            
            # 1. 移除 JSON 後面的額外內容
            # 找到最後一個完整的 JSON 物件
            brace_count = 0
            last_complete_pos = -1
            
            for i, char in enumerate(fixed):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_complete_pos = i
                        break
            
            if last_complete_pos != -1:
                fixed = fixed[:last_complete_pos + 1]
            
            # 2. 修復常見的引號問題
            fixed = fixed.replace("'", '"')  # 單引號改雙引號
            
            # 3. 修復未轉義的引號
            # 處理 answer_summary 中的引號問題
            fixed = re.sub(r'"answer_summary"\s*:\s*"([^"]*?)(例如|比如|如下|建議|結論|總結|具體)："([^"]*?)"([^"]*?)"', 
                          r'"answer_summary": "\1\2：\\"\3\\"\4"', fixed)
            
            # 4. 修復多餘的逗號
            fixed = re.sub(r',\s*}', '}', fixed)  # 移除物件結尾的多餘逗號
            fixed = re.sub(r',\s*]', ']', fixed)  # 移除陣列結尾的多餘逗號
            
            # 5. 修復換行符和空格
            fixed = re.sub(r'\n+', ' ', fixed)  # 換行符替換為空格
            fixed = re.sub(r'\s+', ' ', fixed)  # 多重空格合併
            
            return fixed
            
        except Exception as e:
            logging.error(f"JSON 格式修復失敗: {e}")
            return json_content
    
    def _extract_partial_json(self, json_content: str) -> dict:
        """
        從不完整的 JSON 中提取部分有效內容
        """
        try:
            result = {}
            
            # 提取 answer_summary
            summary_match = re.search(r'"answer_summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_content)
            if summary_match:
                result["answer_summary"] = summary_match.group(1).replace('\\"', '"')
            
            # 提取 comparison_table
            table_match = re.search(r'"comparison_table"\s*:\s*(\[.*?\])', json_content, re.DOTALL)
            if table_match:
                try:
                    table_content = table_match.group(1)
                    # 嘗試修復表格內容
                    fixed_table = self._fix_json_format(table_content)
                    result["comparison_table"] = json.loads(fixed_table)
                except:
                    logging.warning("無法解析 comparison_table，使用空陣列")
                    result["comparison_table"] = []
            
            # 如果沒有找到任何內容，返回空字典
            if not result:
                return None
                
            return result
            
        except Exception as e:
            logging.error(f"部分 JSON 提取失敗: {e}")
            return None

    def _create_simple_table_from_dict_improved(self, comparison_dict: dict, answer_summary=None) -> str:
        """
        改進的字典格式表格創建，更好地處理複雜的數據結構，支持 feature name 作為 row header
        """
        try:
            if not comparison_dict:
                return "無比較數據"

            # 檢查是否包含 main_differences 結構
            feature_names = None
            if answer_summary and isinstance(answer_summary, dict) and 'main_differences' in answer_summary:
                feature_names = [d.get('category', f'規格{i+1}') for i, d in enumerate(answer_summary['main_differences'])]

            # 標準處理
            model_names = list(comparison_dict.keys())
            # If feature_names is not found, fallback to generic
            if not feature_names:
                # Use the length of the first value as feature count
                feature_count = len(next(iter(comparison_dict.values())))
                feature_names = [f'規格 {i+1}' for i in range(feature_count)]

            # Create table header
            header = "| **規格項目** |" + "".join([f" **{model}** |" for model in model_names])
            separator = "| --- |" + " --- |" * len(model_names)
            rows = []
            for idx, feature in enumerate(feature_names):
                row_str = f"| **{feature}** |"
                for model in model_names:
                    value = comparison_dict[model][idx] if idx < len(comparison_dict[model]) else "N/A"
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    row_str += f" {value_str} |"
                rows.append(row_str)
            table_lines = [header, separator] + rows
            return "\n".join(table_lines)
        except Exception as e:
            logging.error(f"創建改進表格失敗: {e}")
            return "表格生成失敗"

    def _create_table_from_main_differences(self, comparison_dict: dict) -> str:
        """
        從 main_differences 結構創建表格
        """
        try:
            # 提取 main_differences 數據
            if isinstance(comparison_dict, str):
                # 如果是字符串，嘗試解析
                import ast
                try:
                    comparison_dict = ast.literal_eval(comparison_dict)
                except:
                    return "無法解析數據格式"
            
            main_differences = comparison_dict.get('main_differences', [])
            if not main_differences:
                return "無主要差異數據"
            
            # 創建表格
            header = "| **比較項目** | **AG958** | **APX958** |"
            separator = "| --- | --- | --- |"
            
            rows = []
            for diff in main_differences:
                if isinstance(diff, dict):
                    category = diff.get('category', '未知項目')
                    ag958_value = diff.get('ag958', 'N/A')
                    apx958_value = diff.get('apx958', 'N/A')
                    
                    # 格式化值
                    ag958_str = str(ag958_value)[:50] + "..." if len(str(ag958_value)) > 50 else str(ag958_value)
                    apx958_str = str(apx958_value)[:50] + "..." if len(str(apx958_value)) > 50 else str(apx958_value)
                    
                    row_str = f"| **{category}** | {ag958_str} | {apx958_str} |"
                    rows.append(row_str)
            
            table_lines = [header, separator] + rows
            return "\n".join(table_lines)
            
        except Exception as e:
            logging.error(f"從 main_differences 創建表格失敗: {e}")
            return "表格生成失敗"

    def _check_query_contains_modelname(self, query: str) -> tuple[bool, list]:
        """
        檢查查詢中是否包含有效的modelname
        返回: (是否包含modelname, 找到的modelname列表)
        """
        found_modelnames = []
        query_lower = query.lower()
        
        # 改进：使用更严格的匹配逻辑
        for modelname in AVAILABLE_MODELNAMES:
            modelname_lower = modelname.lower()
            # 使用单词边界匹配，避免部分匹配
            if re.search(r'\b' + re.escape(modelname_lower) + r'\b', query_lower):
                found_modelnames.append(modelname)
        
        # 如果没有找到完全匹配，检查是否有相似的模型名称
        if not found_modelnames:
            # 提取查询中可能的模型名称模式
            potential_models = re.findall(r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?::\s*[A-Z]+\d+)?', query)
            logging.info(f"查询中发现的潜在模型名称: {potential_models}")
            
            # 检查这些潜在模型是否在可用列表中
            for potential_model in potential_models:
                if potential_model in AVAILABLE_MODELNAMES:
                    found_modelnames.append(potential_model)
        
        logging.info(f"查询验证结果 - 查询: '{query}', 找到的模型名称: {found_modelnames}")
        return len(found_modelnames) > 0, found_modelnames

    def _check_query_contains_modeltype(self, query: str) -> tuple[bool, list]:
        """
        檢查查詢中是否包含有效的modeltype
        返回: (是否包含modeltype, 找到的modeltype列表)
        """
        found_modeltypes = []
        query_lower = query.lower()
        
        # 檢查數據庫中存在的modeltype
        for modeltype in AVAILABLE_MODELTYPES:
            if modeltype.lower() in query_lower:
                found_modeltypes.append(modeltype)
        
        # 如果沒有找到匹配，檢查是否查詢了不存在的數字系列
        if not found_modeltypes:
            import re
            # 尋找查詢中的數字模式 (如656, 777等)
            potential_series = re.findall(r'\b\d{3,4}\b', query)
            if potential_series:
                # 檢查是否為不存在的系列
                non_existent_series = [s for s in potential_series if s not in AVAILABLE_MODELTYPES]
                if non_existent_series:
                    # 記錄查詢了不存在的系列
                    logging.warning(f"查詢了不存在的系列: {non_existent_series}")
                    # 這裡不返回True，但可以在上層處理這種情況
        
        return len(found_modeltypes) > 0, found_modeltypes

    def _get_models_by_type(self, modeltype: str) -> list:
        """
        根據modeltype獲取所有相關的modelname
        """
        try:
            # 使用DuckDB直接查詢該modeltype的所有modelname
            sql_query = "SELECT DISTINCT modelname FROM nbtypes WHERE modeltype = ?"
            
            results = self.duckdb_query.query_with_params(sql_query, [modeltype])
            
            if results:
                modelnames = [record[0] for record in results]
                logging.info(f"根據modeltype '{modeltype}' 找到的modelname: {modelnames}")
                return modelnames
            else:
                logging.warning(f"未找到modeltype '{modeltype}' 的modelname")
                return []
                
        except Exception as e:
            logging.error(f"查詢modeltype '{modeltype}' 相關modelname時發生錯誤: {e}")
            return []

    def _parse_query_intent(self, query: str) -> dict:
        """
        解析用户查询意图
        返回包含modelname、modeltype、intent的字典
        """
        try:
            logging.info(f"開始解析查詢意圖: {query}")
            
            result = {
                "modelnames": [],
                "modeltypes": [],
                "intent": "general",  # 默认意图
                "query_type": "unknown"  # 查询类型
            }
            
            # 1. 检查是否包含modelname
            contains_modelname, found_modelnames = self._check_query_contains_modelname(query)
            if contains_modelname:
                result["modelnames"] = found_modelnames
                result["query_type"] = "specific_model"
            
            # 2. 检查是否包含modeltype
            contains_modeltype, found_modeltypes = self._check_query_contains_modeltype(query)
            if contains_modeltype:
                result["modeltypes"] = found_modeltypes
                if result["query_type"] == "unknown":
                    result["query_type"] = "model_type"
            
            # 3. 解析查询意图 - 使用配置檔案中的關鍵字
            query_lower = query.lower()
            
            # 使用配置檔案中的關鍵字來檢查意圖
            for intent_name, intent_config in self.intent_keywords.items():
                keywords = intent_config.get("keywords", [])
                if any(keyword.lower() in query_lower for keyword in keywords):
                    result["intent"] = intent_name
                    logging.info(f"檢測到意圖 '{intent_name}': {intent_config.get('description', '')}")
                    break
            
            logging.info(f"查詢意圖解析結果: {result}")
            return result
            
        except Exception as e:
            logging.error(f"解析查詢意圖時發生錯誤: {e}")
            return {
                "modelnames": [],
                "modeltypes": [],
                "intent": "general",
                "query_type": "unknown"
            }

    def _get_data_by_query_type(self, query_intent: dict) -> tuple[list, list]:
        """
        根据查询类型获取数据
        返回 (context_list_of_dicts, target_modelnames)
        """
        try:
            query_type = query_intent["query_type"]
            modelnames = query_intent["modelnames"]
            modeltypes = query_intent["modeltypes"]
            
            logging.info(f"根據查詢類型 '{query_type}' 獲取數據")
            
            if query_type == "specific_model":
                # 单个或多个具体型号查询
                if not modelnames:
                    raise ValueError("未找到有效的模型名称")
                
                # 验证模型名称是否在白名单中
                valid_modelnames = []
                for modelname in modelnames:
                    if modelname in AVAILABLE_MODELNAMES:
                        valid_modelnames.append(modelname)
                    else:
                        logging.warning(f"模型名称 '{modelname}' 不在白名单中")
                
                if not valid_modelnames:
                    raise ValueError(f"所有模型名称都不在白名单中: {modelnames}")
                
                # 使用DuckDB查询具体型号数据
                placeholders = ', '.join(['?'] * len(valid_modelnames))
                sql_query = f"SELECT * FROM nbtypes WHERE modelname IN ({placeholders})"
                
                full_specs_records = self.duckdb_query.query_with_params(sql_query, valid_modelnames)
                
                if not full_specs_records:
                    raise ValueError(f"未找到型号为 {valid_modelnames} 的数据")
                
                # 转换为字典格式
                context_list_of_dicts = [dict(zip(self.spec_fields, record)) for record in full_specs_records]
                
                logging.info(f"成功获取 {len(context_list_of_dicts)} 条具体型号数据")
                return context_list_of_dicts, valid_modelnames
                
            elif query_type == "model_type":
                # 型号系列查询
                if not modeltypes:
                    raise ValueError("未找到有效的型号系列")
                
                # 只取第一个型号系列
                modeltype = modeltypes[0]
                logging.info(f"查询型号系列: {modeltype}")
                
                # 获取该系列的所有型号
                target_modelnames = self._get_models_by_type(modeltype)
                
                if not target_modelnames:
                    raise ValueError(f"未找到型号系列 '{modeltype}' 的相关型号")
                
                # 使用DuckDB查询该系列所有型号数据
                placeholders = ', '.join(['?'] * len(target_modelnames))
                sql_query = f"SELECT * FROM nbtypes WHERE modelname IN ({placeholders})"
                
                full_specs_records = self.duckdb_query.query_with_params(sql_query, target_modelnames)
                
                if not full_specs_records:
                    raise ValueError(f"未找到型号系列 '{modeltype}' 的数据")
                
                # 转换为字典格式
                context_list_of_dicts = [dict(zip(self.spec_fields, record)) for record in full_specs_records]
                
                logging.info(f"成功获取型号系列 '{modeltype}' 的 {len(context_list_of_dicts)} 条数据")
                return context_list_of_dicts, target_modelnames
                
            else:
                raise ValueError(f"不支持的查询类型: {query_type}")
                
        except Exception as e:
            logging.error(f"获取数据时发生错误: {e}")
            raise

    async def _handle_funnel_choice(self, query: str, funnel_choice: str, session_id: str):
        """
        處理漏斗選擇的邏輯
        """
        logging.info(f"處理漏斗選擇: {funnel_choice}")
        
        if funnel_choice == "series_comparison":
            # 系列規格比較流程
            logging.info("用戶選擇系列規格比較流程")
            
            # 重新分類查詢以進行系列比較
            async for response in self._process_series_comparison(query):
                yield response
                
        elif funnel_choice == "purpose_recommendation":
            # 用途導向推薦流程
            logging.info("用戶選擇用途導向推薦流程")
            
            # 啟動多輪對話問卷
            multichat_response = {
                "type": "multichat_start",
                "message": "我將通過幾個問題來了解您的需求，為您推薦最適合的筆電。",
                "session_id": session_id or "generated_session_id"
            }
            yield f"data: {json.dumps(multichat_response, ensure_ascii=False)}\n\n"
            
        else:
            # 未知選擇，返回錯誤
            error_response = {
                "type": "error",
                "message": f"未知的漏斗選擇: {funnel_choice}"
            }
            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"

    async def _process_series_comparison(self, query: str):
        """
        處理系列比較的邏輯
        """
        logging.info(f"開始系列比較流程，查詢: {query}")
        
        # 使用現有的 RAG 流程進行系列比較
        # 步驟1：解析查詢意圖
        query_intent = self._parse_query_intent(query)
        logging.info(f"系列比較查詢意圖解析結果: {query_intent}")
        
        # 步驟2：根據查詢類型獲取精確資料
        try:
            context_list_of_dicts, target_modelnames = self._get_data_by_query_type(query_intent)
            logging.info(f"獲取到的上下文資料數量: {len(context_list_of_dicts)}")
            logging.info(f"目標型號: {target_modelnames}")
            
            if not context_list_of_dicts:
                # 沒有找到相關資料
                no_data_response = {
                    "answer_summary": "很抱歉，沒有找到相關的筆電規格資料。請檢查您的查詢是否包含有效的型號或系列名稱。",
                    "comparison_table": []
                }
                yield f"data: {json.dumps(no_data_response, ensure_ascii=False)}\n\n"
                return
            
            # 步驟3：構建提示詞並使用LLM生成回應
            context_str = "\n".join([f"型號: {item['modelname']}\n規格: {json.dumps(item, ensure_ascii=False, indent=2)}" for item in context_list_of_dicts])
            
            # 構建意圖信息
            intent_info = f"""查詢類型: {query_intent['query_type']}
目標型號: {target_modelnames}
"""
            
            # 構建最終提示詞
            final_prompt = self.prompt_template.replace("{context}", context_str).replace("{query}", query)
            final_prompt = final_prompt.replace("[QUERY INTENT ANALYSIS]", intent_info)
            
            logging.info("開始調用LLM生成回應")
            
            llm_response = self.llm.invoke(final_prompt)
            logging.info("LLM回應生成完成")
            
            # 步驟4：解析並格式化LLM回應
            structured_response = self._parse_llm_response(llm_response.content)
            logging.info("LLM回應解析完成")
            
            yield f"data: {json.dumps(structured_response, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logging.error(f"系列比較處理過程中發生錯誤: {e}", exc_info=True)
            error_response = {
                "answer_summary": f"處理系列比較時發生錯誤: {str(e)}",
                "comparison_table": []
            }
            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"

    def _should_list_all_models(self, query: str) -> bool:
        """
        檢查是否應該列出所有型號和系列
        只有明確要求列出所有機型的查詢才會觸發
        """
        query_lower = query.lower()
        
        # 明確的列表請求關鍵字
        list_keywords = [
            "列出所有", "列出全部", "所有的nb", "所有的筆電", "所有機型", "所有系列",
            "你們賣的", "你們有的", "可以選擇的", "有哪些型號", "有哪些系列",
            "請列出", "給我看", "展示所有", "所有型號", "全部型號", "全部機型"
        ]
        
        # 檢查是否包含列表請求關鍵字
        for keyword in list_keywords:
            if keyword in query_lower:
                logging.info(f"檢測到型號列表請求關鍵字: {keyword}")
                return True
        
        return False

    async def chat_stream(self, query: str, **kwargs):
        """
        新的RAG流程：
        1. 解析用户查询意图（modelname、modeltype、intent）
        2. 根据查询类型获取精确数据
        3. 将数据和查询意图传递给LLM
        """
        try:
            logging.info(f"開始新的RAG流程，查詢: {query}")
            
            # 提取額外參數
            funnel_choice = kwargs.get("funnel_choice")
            session_id = kwargs.get("session_id")
            
            # 步驟0a：處理漏斗選擇
            if funnel_choice:
                logging.info(f"檢測到漏斗選擇: {funnel_choice}, 會話ID: {session_id}")
                async for response in self._handle_funnel_choice(query, funnel_choice, session_id):
                    yield response
                return
            
            # 步驟0：檢查是否應該列出所有型號和系列
            if self._should_list_all_models(query):
                logging.info("檢測到型號列表請求，返回所有可用型號")
                available_types_str = "\n".join([f"- {modeltype}" for modeltype in AVAILABLE_MODELTYPES])
                available_models_str = "\n".join([f"- {model}" for model in AVAILABLE_MODELNAMES])
                
                list_message = f"可用的系列包括：\n{available_types_str}\n\n可用的型號包括：\n{available_models_str}\n\n請重新提問，例如：'比較 958 系列的 CPU 性能' 或 '比較 AB819-S: FP6 和 AG958 的 CPU 性能'"
                
                list_response = {
                    "answer_summary": list_message,
                    "comparison_table": []
                }
                yield f"data: {json.dumps(list_response, ensure_ascii=False)}\n\n"
                return
            
            # 步驟1：檢查是否應該啟動漏斗對話（最高優先級）
            should_trigger_funnel, funnel_query_type = self.funnel_manager.should_trigger_funnel(query)
            
            if should_trigger_funnel:
                logging.info(f"檢測到漏斗對話觸發條件，查詢類型: {funnel_query_type.value}")
                try:
                    session_id, funnel_question = self.funnel_manager.start_funnel_session(query)
                    
                    # 格式化漏斗問題回應
                    funnel_response = {
                        "type": "funnel_question",
                        "session_id": session_id,
                        "question": {
                            "question_id": funnel_question.question_id,
                            "question_text": funnel_question.question_text,
                            "options": funnel_question.options
                        },
                        "context": funnel_question.context,
                        "message": "請選擇最符合您需求的選項，我將為您提供更精準的協助。"
                    }
                    
                    yield f"data: {json.dumps(funnel_response, ensure_ascii=False)}\n\n"
                    return
                    
                except Exception as e:
                    logging.error(f"啟動漏斗對話失敗: {e}")
                    # 如果漏斗對話啟動失敗，繼續檢查傳統的多輪對話
            
            # 步驟2：檢查是否應該啟動傳統多輪對話導引
            should_start_multichat, detected_scenario = self.multichat_manager.should_activate_multichat(query)
            
            # 擴展商務和筆電相關的觸發條件
            business_keywords = ["商務", "辦公", "工作", "企業", "商用", "業務", "職場", "公司", "文書處理", "文書", "處理"]
            laptop_keywords = ["筆電", "筆記本", "筆記型電腦", "laptop", "notebook", "電腦", "NB"]
            introduction_keywords = ["介紹", "推薦", "建議", "選擇", "挑選", "適合", "需要"]
            
            # 檢查是否為商務筆電相關查詢
            is_business_laptop_query = (
                any(bk in query for bk in business_keywords) and 
                any(lk in query for lk in laptop_keywords)
            ) or (
                any(lk in query for lk in laptop_keywords) and 
                any(ik in query for ik in introduction_keywords)
            )
            
            # 如果商務筆電查詢但沒有檢測到場景，設定為business
            if is_business_laptop_query and not detected_scenario:
                detected_scenario = "business"
            
            if should_start_multichat or is_business_laptop_query:
                logging.info(f"檢測到模糊查詢或商務筆電查詢，場景類型: {detected_scenario}，直接啟動一次性問卷模式")
                try:
                    # 所有MultiChat查詢都使用一次性問卷模式，並傳遞場景資訊
                    logging.info(f"使用一次性問卷模式，場景: {detected_scenario}")
                    all_questions_response = self.get_all_questions(query, scenario=detected_scenario)
                    yield f"data: {json.dumps(all_questions_response, ensure_ascii=False)}\n\n"
                    return
                    
                except Exception as e:
                    logging.error(f"啟動多輪對話失敗: {e}")
                    # 如果多輪對話啟動失敗，繼續使用原有流程
            
            # 步驟2：解析查詢意圖（只有在不觸發MultiChat時才執行）
            query_intent = self._parse_query_intent(query)
            logging.info(f"查詢意圖解析結果: {query_intent}")
            
            # 步驟3：檢查是否有有效的查詢類型
            if query_intent["query_type"] == "unknown":
                # 檢查是否查詢了不存在的系列
                import re
                potential_series = re.findall(r'\b\d{3,4}\b', query)
                non_existent_series = [s for s in potential_series if s not in AVAILABLE_MODELTYPES]
                
                if non_existent_series:
                    # 提供友善的錯誤訊息，告知不存在的系列
                    available_types_str = "、".join(AVAILABLE_MODELTYPES)
                    unknown_message = f"很抱歉，目前沒有 {non_existent_series[0]} 系列的筆電資料。\n\n目前可查詢的系列包括：{available_types_str}\n\n您可以嘗試：\n- 詢問現有系列的規格，例如「請比較958系列的筆電」\n- 查看特定型號，例如「AG958的規格如何」\n- 或者問我「請列出所有NB型號」來查看完整選項"
                else:
                    # 如果到這裡還是unknown，說明這是一個無法識別的查詢
                    # 但不是明確的型號列表請求，也不觸發MultiChat
                    # 這種情況比較少見，提供通用幫助
                    unknown_message = "很抱歉，我無法理解您的查詢。請提供更具體的問題，例如：\n- 詢問特定型號的規格\n- 比較不同型號的性能\n- 或者問我「請列出所有NB型號」來查看可用選項"
                
                unknown_response = {
                    "answer_summary": unknown_message,
                    "comparison_table": []
                }
                yield f"data: {json.dumps(unknown_response, ensure_ascii=False)}\n\n"
                return
            
            # 步驟4：根據查詢類型獲取精確資料
            try:
                context_list_of_dicts, target_modelnames = self._get_data_by_query_type(query_intent)
                logging.info(f"成功获取数据，型号数量: {len(target_modelnames)}")
                logging.info(f"目标型号: {target_modelnames}")
                
            except ValueError as e:
                # 数据获取失败，返回错误信息
                error_message = str(e)
                error_obj = {
                    "answer_summary": error_message,
                    "comparison_table": []
                }
                yield f"data: {json.dumps(error_obj, ensure_ascii=False)}\n\n"
                return
            
            # 步骤2.5：检查数据可用性
            query_intent["query"] = query  # 添加原始查询到意图信息中
            has_data, missing_data_info = self._check_data_availability(context_list_of_dicts, target_modelnames, query_intent)
            
            if not has_data:
                # 如果没有相关数据，直接返回"並無登記資料"
                missing_info_str = "、".join(missing_data_info) if missing_data_info else "相關資料"
                no_data_message = f"抱歉，{missing_info_str}並無登記資料。"
                
                no_data_response = {
                    "answer_summary": no_data_message,
                    "comparison_table": []
                }
                yield f"data: {json.dumps(no_data_response, ensure_ascii=False)}\n\n"
                return
            
            # 步骤3：构建增强的上下文，包含查询意图信息
            enhanced_context = {
                "data": context_list_of_dicts,
                "query_intent": query_intent,
                "target_modelnames": target_modelnames
            }
            
            context_str = json.dumps(enhanced_context, indent=2, ensure_ascii=False)
            logging.info("成功构建增强上下文，包含查询意图信息")
            
            # 步骤4：构建提示并请求LLM
            # 构建包含查询意图信息的prompt
            intent_info = f"""
[QUERY INTENT ANALYSIS]
Based on the query intent analysis:
- Query Type: {query_intent['query_type']}
- Intent: {query_intent['intent']} 
- Target Models: {', '.join(target_modelnames)}

Focus your analysis on the specific intent and target models identified above.
"""
            
            # 構建最終提示詞
            final_prompt = self.prompt_template.replace("{context}", context_str).replace("{query}", query)
            # 在prompt中添加查询意图信息
            final_prompt = final_prompt.replace("[QUERY INTENT ANALYSIS]", intent_info)
            
            logging.info("\n=== 最終傳送給 LLM 的提示 (Final Prompt) ===\n" + final_prompt + "\n========================================")
            
            # 直接調用 LLM
            response_str = self.llm_initializer.invoke(final_prompt)
            logging.info(f"\n=== 從 LLM 收到的原始回應 ===\n{response_str}\n=============================")
            
            # 步骤5：解析并返回JSON
            try:
                # 首先檢查是否有 <think> 標籤，如果有則提取 </think> 之後的內容
                think_end = response_str.find("</think>")
                if think_end != -1:
                    # 提取 </think> 之後的內容
                    cleaned_response_str = response_str[think_end + 8:].strip()
                    logging.info(f"提取 </think> 之後的內容: {cleaned_response_str}")
                else:
                    # 如果沒有 <think> 標籤，使用原始回應
                    cleaned_response_str = response_str
                
                # 在清理後的內容中尋找 JSON
                json_start = cleaned_response_str.find("{")
                json_end = cleaned_response_str.rfind("}")
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_content = cleaned_response_str[json_start:json_end+1]
                    logging.info(f"提取的 JSON 內容: {json_content}")
                    
                    # 嘗試解析 JSON - 改進的錯誤處理
                    try:
                        parsed_json = json.loads(json_content)
                    except json.JSONDecodeError as json_error:
                        logging.warning(f"JSON 解析失敗: {json_error}")
                        
                        # 嘗試修復常見的 JSON 格式問題
                        fixed_json_content = self._fix_json_format(json_content)
                        logging.info(f"嘗試修復後的 JSON: {fixed_json_content}")
                        
                        try:
                            parsed_json = json.loads(fixed_json_content)
                            logging.info("JSON 修復成功")
                        except json.JSONDecodeError as second_error:
                            logging.error(f"JSON 修復後仍然失敗: {second_error}")
                            # 如果修復失敗，嘗試提取部分 JSON
                            parsed_json = self._extract_partial_json(json_content)
                            if not parsed_json:
                                raise json_error
                    
                    # ★ 修正點：處理 LLM 返回的嵌套格式
                    # 檢查是否是嵌套格式：{"answer_summary": {"best_model": "...", "comparison_table": {...}}}
                    if "answer_summary" in parsed_json and isinstance(parsed_json["answer_summary"], dict):
                        nested_answer = parsed_json["answer_summary"]
                        logging.info(f"檢測到嵌套格式的 answer_summary: {nested_answer}")
                        
                        # 檢查嵌套的 answer_summary 是否包含 comparison_table
                        if "comparison_table" in nested_answer:
                            # 提取 reasoning 或 best_model 作為 answer_summary 的內容
                            if "reasoning" in nested_answer:
                                answer_content = nested_answer["reasoning"]
                            elif "best_model" in nested_answer:
                                best_model = nested_answer["best_model"]
                                answer_content = f"根據分析，{best_model} 是最適合的選擇。"
                            else:
                                # 如果沒有 reasoning 或 best_model，使用整個嵌套結構的字符串表示
                                answer_content = json.dumps(nested_answer, ensure_ascii=False)
                            
                            # 轉換為標準格式
                            converted_json = {
                                "answer_summary": answer_content,
                                "comparison_table": nested_answer["comparison_table"]
                            }
                            
                            logging.info(f"轉換後的標準格式: {converted_json}")
                            parsed_json = converted_json
                    
                    # 檢查是否已經是正確的格式
                    if "answer_summary" in parsed_json and "comparison_table" in parsed_json:
                        # 使用兩步驟策略處理LLM回應
                        logging.info("開始使用兩步驟策略處理LLM回應")
                        processed_response = self._process_llm_response_robust(parsed_json, context_list_of_dicts, target_modelnames, query)
                        
                        logging.info(f"兩步驟策略處理完成 - answer_summary: {processed_response.get('answer_summary', '')}")
                        logging.info(f"兩步驟策略處理完成 - comparison_table: {processed_response.get('comparison_table', '')}")
                        yield f"data: {json.dumps(processed_response, ensure_ascii=False)}\n\n"
                        return
                    else:
                        logging.error("LLM回應格式不正確，缺少必要欄位")
                        fallback_response = self._generate_fallback_response(query, context_list_of_dicts, target_modelnames)
                        yield f"data: {json.dumps(fallback_response, ensure_ascii=False)}\n\n"
                        return
                else:
                    logging.error("無法從LLM回應中提取JSON")
                    fallback_response = self._generate_fallback_response(query, context_list_of_dicts, target_modelnames)
                    yield f"data: {json.dumps(fallback_response, ensure_ascii=False)}\n\n"
                    return
                    
            except json.JSONDecodeError as e:
                logging.error(f"JSON解析失敗: {e}")
                fallback_response = self._generate_fallback_response(query, context_list_of_dicts, target_modelnames)
                yield f"data: {json.dumps(fallback_response, ensure_ascii=False)}\n\n"
                return
            except Exception as e:
                logging.error(f"處理LLM回應時發生錯誤: {e}")
                fallback_response = self._generate_fallback_response(query, context_list_of_dicts, target_modelnames)
                yield f"data: {json.dumps(fallback_response, ensure_ascii=False)}\n\n"
                return
                
        except Exception as e:
            logging.error(f"chat_stream 發生錯誤: {e}", exc_info=True)
            error_obj = {
                "answer_summary": f"處理您的查詢時發生錯誤: {str(e)}",
                "comparison_table": []
            }
            yield f"data: {json.dumps(error_obj, ensure_ascii=False)}\n\n"

    def _validate_llm_response(self, parsed_json, target_modelnames):
        """
        驗證LLM回答是否包含正確的模型名稱
        """
        try:
            logging.info(f"開始驗證LLM回答，目標模型名稱: {target_modelnames}")
            
            # 定義無效的品牌和GPU型號列表
            invalid_brands = ["Acer", "ASUS", "Lenovo", "Dell", "MSI", "Razer", "NVIDIA", "Nvidia"]
            invalid_gpu_models = ["RTX", "GTX", "RTX 3060", "RTX 3070", "RTX 3080", "RTX 3090", "RTX 4060", "RTX 4070", "RTX 4080", "RTX 4090", "GTX 1650", "GTX 1660"]
            
            # 創建模型名稱的變體列表（處理冒號等格式差異）
            def get_model_variants(model_name):
                variants = [model_name]
                # 添加沒有冒號的版本
                if ":" in model_name:
                    variants.append(model_name.replace(":", ""))
                # 添加有冒號的版本
                else:
                    # 嘗試添加冒號
                    parts = model_name.split()
                    if len(parts) >= 2:
                        variants.append(f"{parts[0]}: {' '.join(parts[1:])}")
                return variants
            
            target_model_variants = []
            for model_name in target_modelnames:
                target_model_variants.extend(get_model_variants(model_name))
            
            logging.info(f"目標模型名稱變體: {target_model_variants}")
            
            # 檢查answer_summary中是否包含正確的模型名稱
            answer_summary = parsed_json.get("answer_summary", "")
            logging.info(f"檢查answer_summary: {answer_summary}")
            
            if answer_summary:
                # 首先檢查是否包含任何目標模型名稱或其變體
                has_valid_model = False
                for model_variant in target_model_variants:
                    if model_variant in answer_summary:
                        has_valid_model = True
                        logging.info(f"找到有效模型名稱變體: {model_variant}")
                        break
                
                # 如果没有找到有效模型名称，检查是否有其他可能的模型名称
                if not has_valid_model:
                    # 根据目标模型名称是否包含特殊符号来选择正则表达式
                    potential_models = []
                    
                    for target_model in target_modelnames:
                        if ":" in target_model:
                            # 如果目标模型包含冒号，使用匹配冒号格式的正则表达式
                            pattern = r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?:\s*:\s*[A-Z]+\d+[A-Z]*)'
                            matches = re.findall(pattern, answer_summary)
                            potential_models.extend(matches)
                            
                            # 也匹配没有冒号的版本 - 修复正则表达式以匹配完整的模型名称
                            pattern_no_colon = r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?:\s+[A-Z]+\d+[A-Z]*\d*)'
                            matches_no_colon = re.findall(pattern_no_colon, answer_summary)
                            potential_models.extend(matches_no_colon)
                        else:
                            # 如果目标模型不包含冒号，使用简单格式的正则表达式
                            pattern = r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?'
                            matches = re.findall(pattern, answer_summary)
                            potential_models.extend(matches)
                    
                    # 去重
                    potential_models = list(set(potential_models))
                    logging.info(f"在answer_summary中找到的潜在模型名称: {potential_models}")
                    
                    for potential_model in potential_models:
                        # 检查是否是目标模型的变体
                        is_valid_variant = False
                        for model_variant in target_model_variants:
                            if potential_model == model_variant:
                                is_valid_variant = True
                                logging.info(f"找到有效模型名称变体: {potential_model} -> {model_variant}")
                                break
                        
                        if not is_valid_variant and potential_model not in AVAILABLE_MODELNAMES:
                            # 检查是否是已知的无效模型名称
                            known_invalid_models = ["M20W", "A520", "R7 5900HS", "Ryzen 7 958", "Ryzen 9 7640H"]
                            if potential_model not in known_invalid_models:
                                logging.warning(f"LLM回答包含不存在的模型名称: {potential_model}")
                                return False
                
                # 检查无效品牌 - 改进：避免将模型名称中的字母组合误认为品牌
                for brand in invalid_brands:
                    # 使用单词边界匹配，避免将模型名称中的字母组合误认为品牌
                    if re.search(r'\b' + re.escape(brand) + r'\b', answer_summary):
                        logging.warning(f"LLM回答包含无效品牌: {brand}")
                        return False
                
                # 检查无效GPU型号
                for gpu_model in invalid_gpu_models:
                    if gpu_model in answer_summary:
                        logging.warning(f"LLM回答包含无效GPU型号: {gpu_model}")
                        return False
                
                # 如果包含正确的模型名称，即使有其他内容也认为有效
                if has_valid_model:
                    logging.info("LLM回答包含正确的模型名称，验证通过")
                    return True
                else:
                    logging.warning("LLM回答中未找到任何目标模型名称")
                    return False
            
            # 检查comparison_table中的模型名称
            comparison_table = parsed_json.get("comparison_table", [])
            logging.info(f"检查comparison_table: {comparison_table}")
            
            if isinstance(comparison_table, list) and comparison_table:
                # 检查表格中的模型名称
                for row in comparison_table:
                    if isinstance(row, dict):
                        # 检查是否包含正确的模型名称作为键
                        for model_variant in target_model_variants:
                            if model_variant in row:
                                logging.info(f"在comparison_table中找到有效模型名称变体: {model_variant}")
                                return True
                        
                        # 检查是否包含错误的模型名称
                        for key in row.keys():
                            if key != "feature" and key not in target_model_variants:
                                # 检查是否包含常见错误模型名称
                                invalid_models = ["A520", "M20W", "R7 5900HS", "Ryzen 7 958", "Ryzen 9 7640H"]
                                for invalid_model in invalid_models:
                                    if invalid_model in key:
                                        logging.warning(f"LLM回答包含无效模型名称: {invalid_model}")
                                        return False
                        
                        # 检查值中是否包含无效GPU型号
                        for value in row.values():
                            if isinstance(value, str):
                                for gpu_model in invalid_gpu_models:
                                    if gpu_model in value:
                                        logging.warning(f"LLM回答包含无效GPU型号: {gpu_model}")
                                        return False
            
            # 如果comparison_table是字典格式
            elif isinstance(comparison_table, dict):
                # 检查字典中的模型名称
                for key in comparison_table.keys():
                    if key != "modelname" and key not in target_model_variants:
                        # 检查是否是模式匹配的无效模型名称
                        if re.match(r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?:\s*:\s*[A-Z]+\d+)?', key):
                            if key not in AVAILABLE_MODELNAMES:
                                logging.warning(f"LLM回答包含不存在的模型名称: {key}")
                                return False
                
                # 检查是否包含正确的模型名称
                for model_variant in target_model_variants:
                    if model_variant in comparison_table:
                        logging.info(f"在comparison_table字典中找到有效模型名称变体: {model_variant}")
                        return True
            
            # 如果没有找到任何目标模型名称，认为无效
            logging.warning("LLM回答中未找到任何目标模型名称")
            return False
            
        except Exception as e:
            logging.error(f"驗證LLM回應時發生錯誤: {e}")
            return False

    def _validate_llm_response_separated(self, parsed_json, target_modelnames):
        """
        分离验证：answer_summary和comparison_table独立验证
        返回验证结果字典，包含每个部分的验证状态
        """
        try:
            logging.info(f"開始分離驗證LLM回答，目標模型名稱: {target_modelnames}")
            
            # 定义无效的品牌和GPU型号列表
            invalid_brands = ["Acer", "ASUS", "Lenovo", "Dell", "MSI", "Razer", "NVIDIA", "Nvidia"]
            # 更新無效 GPU 型號列表，移除一些可能有效的型號
            invalid_gpu_models = ["GTX 1650", "GTX 1660", "RTX 3060", "RTX 3070", "RTX 3080", "RTX 3090"]
            
            # 创建模型名称的变体列表
            def get_model_variants(model_name):
                variants = [model_name]
                if ":" in model_name:
                    variants.append(model_name.replace(":", ""))
                else:
                    parts = model_name.split()
                    if len(parts) >= 2:
                        variants.append(f"{parts[0]}: {' '.join(parts[1:])}")
                return variants
            
            target_model_variants = []
            for model_name in target_modelnames:
                target_model_variants.extend(get_model_variants(model_name))
            
            logging.info(f"目標模型名稱變體: {target_model_variants}")
            
            # 步骤1：验证answer_summary
            summary_valid = False
            answer_summary = parsed_json.get("answer_summary", "")
            
            if answer_summary:
                logging.info(f"驗證answer_summary: {answer_summary}")
                
                # 處理 answer_summary 可能是字典格式的情況
                if isinstance(answer_summary, dict):
                    # 將字典轉換為字符串進行驗證
                    answer_summary_str = json.dumps(answer_summary, ensure_ascii=False)
                    logging.info(f"answer_summary 是字典格式，轉換為字符串: {answer_summary_str}")
                else:
                    answer_summary_str = str(answer_summary)
                
                # 检查是否包含正确的模型名称
                has_valid_model = False
                for model_variant in target_model_variants:
                    if model_variant in answer_summary_str:
                        has_valid_model = True
                        logging.info(f"在answer_summary中找到有效模型名稱變體: {model_variant}")
                        break
                
                # 如果没有找到直接匹配，使用正则表达式查找
                if not has_valid_model:
                    potential_models = []
                    for target_model in target_modelnames:
                        if ":" in target_model:
                            pattern = r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?:\s*:\s*[A-Z]+\d+[A-Z]*)'
                            matches = re.findall(pattern, answer_summary_str)
                            potential_models.extend(matches)
                            
                            pattern_no_colon = r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?:\s+[A-Z]+\d+[A-Z]*\d*)'
                            matches_no_colon = re.findall(pattern_no_colon, answer_summary_str)
                            potential_models.extend(matches_no_colon)
                        else:
                            pattern = r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?'
                            matches = re.findall(pattern, answer_summary_str)
                            potential_models.extend(matches)
                    
                    potential_models = list(set(potential_models))
                    logging.info(f"在answer_summary中找到的潜在模型名称: {potential_models}")
                    
                    for potential_model in potential_models:
                        for model_variant in target_model_variants:
                            if potential_model == model_variant:
                                has_valid_model = True
                                logging.info(f"通過正則表達式找到有效模型名称变体: {potential_model}")
                                break
                        if has_valid_model:
                            break
                
                # 检查无效品牌（使用单词边界）
                has_invalid_brand = False
                for brand in invalid_brands:
                    if re.search(r'\b' + re.escape(brand) + r'\b', answer_summary_str):
                        logging.warning(f"answer_summary包含无效品牌: {brand}")
                        has_invalid_brand = True
                        break
                
                # 检查无效GPU型号 - 改進：只檢查完全匹配的無效型號
                has_invalid_gpu = False
                for gpu_model in invalid_gpu_models:
                    # 使用單詞邊界匹配，避免部分匹配
                    if re.search(r'\b' + re.escape(gpu_model) + r'\b', answer_summary_str):
                        logging.warning(f"answer_summary包含无效GPU型号: {gpu_model}")
                        has_invalid_gpu = True
                        break
                
                # 改進驗證邏輯：如果包含正確的模型名稱，即使有無效內容也認為有效
                if has_valid_model:
                    summary_valid = True
                    logging.info("answer_summary驗證通過（包含正確模型名稱）")
                elif not has_invalid_brand and not has_invalid_gpu:
                    # 如果沒有無效內容，也認為有效
                    summary_valid = True
                    logging.info("answer_summary驗證通過（無無效內容）")
                else:
                    logging.warning("answer_summary驗證失敗")
            
            # 步骤2：验证comparison_table
            table_valid = False
            comparison_table = parsed_json.get("comparison_table", [])
            
            if comparison_table:
                logging.info(f"驗證comparison_table: {comparison_table}")
                
                # 检查表格格式和内容
                if isinstance(comparison_table, list) and comparison_table:
                    # 检查是否包含正确的模型名称作为键
                    has_valid_model_in_table = False
                    has_invalid_content = False
                    
                    for row in comparison_table:
                        if isinstance(row, dict):
                            # 检查是否包含正确的模型名称
                            for model_variant in target_model_variants:
                                if model_variant in row:
                                    has_valid_model_in_table = True
                                    logging.info(f"在comparison_table中找到有效模型名称变体: {model_variant}")
                                    break
                            
                            # 检查是否包含错误的模型名称
                            for key in row.keys():
                                if key != "feature" and key not in target_model_variants:
                                    invalid_models = ["A520", "M20W", "R7 5900HS", "Ryzen 7 958", "Ryzen 9 7640H"]
                                    for invalid_model in invalid_models:
                                        if invalid_model in key:
                                            logging.warning(f"comparison_table包含无效模型名称: {invalid_model}")
                                            has_invalid_content = True
                                            break
                            
                            # 检查值中是否包含无效GPU型号
                            for value in row.values():
                                if isinstance(value, str):
                                    for gpu_model in invalid_gpu_models:
                                        if re.search(r'\b' + re.escape(gpu_model) + r'\b', value):
                                            logging.warning(f"comparison_table包含无效GPU型号: {gpu_model}")
                                            has_invalid_content = True
                                            break
                    
                    if has_valid_model_in_table and not has_invalid_content:
                        table_valid = True
                        logging.info("comparison_table驗證通過")
                    else:
                        logging.warning("comparison_table驗證失敗")
                
                elif isinstance(comparison_table, dict):
                    # 字典格式的验证
                    has_valid_model_in_table = False
                    has_invalid_content = False
                    
                    # ★ 修正點：檢查第一個鍵是否是 "Model" 或 "modelname"
                    keys = list(comparison_table.keys())
                    if keys and keys[0].lower() in ["model", "modelname"] and isinstance(comparison_table[keys[0]], list):
                        # 第一個鍵是 Model 或 modelname，包含模型名稱列表
                        models = comparison_table[keys[0]]
                        logging.info(f"檢測到 {keys[0]} 鍵格式，模型列表: {models}")
                        
                        # 檢查模型名稱是否包含目標模型
                        for model in models:
                            for model_variant in target_model_variants:
                                if model == model_variant:
                                    has_valid_model_in_table = True
                                    logging.info(f"在comparison_table字典中找到有效模型名称: {model}")
                                    break
                            if has_valid_model_in_table:
                                break
                        
                        # 檢查其他鍵是否包含無效內容
                        for key in keys[1:]:  # 跳過 Model/modelname 鍵
                            if key.lower() in ["model", "modelname", "device_model"]:
                                continue  # 跳過模型名稱相關的鍵
                            
                            # 檢查值中是否包含無效GPU型號
                            if isinstance(comparison_table[key], list):
                                for value in comparison_table[key]:
                                    if isinstance(value, str):
                                        for gpu_model in invalid_gpu_models:
                                            if re.search(r'\b' + re.escape(gpu_model) + r'\b', value):
                                                logging.warning(f"comparison_table包含无效GPU型号: {gpu_model}")
                                                has_invalid_content = True
                                                break
                    else:
                        # 標準字典格式驗證
                        for key in comparison_table.keys():
                            if key != "modelname" and key not in target_model_variants:
                                if re.match(r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?:\s*:\s*[A-Z]+\d+)?', key):
                                    if key not in AVAILABLE_MODELNAMES:
                                        logging.warning(f"comparison_table包含不存在的模型名称: {key}")
                                        has_invalid_content = True
                        
                        for model_variant in target_model_variants:
                            if model_variant in comparison_table:
                                has_valid_model_in_table = True
                                logging.info(f"在comparison_table字典中找到有效模型名称变体: {model_variant}")
                                break
                    
                    if has_valid_model_in_table and not has_invalid_content:
                        table_valid = True
                        logging.info("comparison_table字典格式驗證通過")
                    else:
                        logging.warning("comparison_table字典格式驗證失敗")
            
            # 返回分离验证结果
            validation_result = {
                "summary_valid": summary_valid,
                "table_valid": table_valid,
                "answer_summary": answer_summary if summary_valid else None,
                "comparison_table": comparison_table if table_valid else None
            }
            
            logging.info(f"分離驗證結果: summary_valid={summary_valid}, table_valid={table_valid}")
            return validation_result
            
        except Exception as e:
            logging.error(f"分離驗證LLM回應時發生錯誤: {e}")
            return {
                "summary_valid": False,
                "table_valid": False,
                "answer_summary": None,
                "comparison_table": None
            }

    def _generate_fallback_response(self, query, context_list_of_dicts, target_modelnames):
        """
        生成備用回應，基於實際數據創建比較表格
        """
        try:
            # 檢查是否有實際數據
            if not context_list_of_dicts:
                # 如果沒有數據，說明查詢的模型不存在
                potential_models = re.findall(r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?::\s*[A-Z]+\d+)?', query)
                if potential_models:
                    error_message = f"抱歉，您查詢的模型 '{', '.join(potential_models)}' 在我们的數據庫中不存在。"
                    error_message += f"\n\n可用的模型包括：\n"
                    for model in AVAILABLE_MODELNAMES:
                        error_message += f"- {model}\n"
                    error_message += f"\n請使用正確的模型名稱重新查詢。"
                    
                    return {
                        "answer_summary": error_message,
                        "comparison_table": []
                    }
                else:
                    return {
                        "answer_summary": "抱歉，無法找到相關的產品數據。請檢查您的查詢。",
                        "comparison_table": []
                    }
            
            # 根據查詢類型決定要比較的特徵
            if "遊戲" in query or "gaming" in query.lower():
                features = [
                    ("CPU Model", "cpu"),
                    ("GPU Model", "gpu"), 
                    ("Thermal Design", "thermal"),
                    ("Memory Type", "memory"),
                    ("Storage Type", "storage")
                ]
            elif "電池" in query or "續航" in query or "battery" in query.lower():
                features = [
                    ("Battery Capacity", "battery"),
                    ("Battery Life", "battery"),
                    ("Charging Speed", "battery")
                ]
            elif "輕便" in query or "重量" in query or "weight" in query.lower() or "portable" in query.lower():
                features = [
                    ("Weight", "structconfig"),
                    ("Dimensions", "structconfig"),
                    ("Form Factor", "structconfig"),
                    ("Material", "structconfig")
                ]
            elif "cpu" in query.lower() or "處理器" in query:
                features = [
                    ("CPU Model", "cpu"),
                    ("CPU Architecture", "cpu"),
                    ("CPU TDP", "cpu")
                ]
            elif "gpu" in query.lower() or "顯卡" in query:
                features = [
                    ("GPU Model", "gpu"),
                    ("GPU Memory", "gpu"),
                    ("GPU Power", "gpu")
                ]
            else:
                # 通用比較
                features = [
                    ("CPU Model", "cpu"),
                    ("GPU Model", "gpu"),
                    ("Memory Type", "memory"),
                    ("Storage Type", "storage"),
                    ("Battery Capacity", "battery")
                ]
            
            # 構建比較表格
            comparison_table = []
            for feature_name, data_field in features:
                row = {"feature": feature_name}
                for model_name in target_modelnames:
                    # 找到對應模型的數據
                    model_data = next((item for item in context_list_of_dicts if item.get("modelname") == model_name), None)
                    if model_data:
                        field_data = model_data.get(data_field, "")
                        # 提取關鍵信息
                        if data_field == "cpu":
                            # 提取CPU型號
                            cpu_match = re.search(r"Ryzen™\s+\d+\s+\d+[A-Z]*[HS]*", field_data)
                            row[model_name] = cpu_match.group(0) if cpu_match else "N/A"
                        elif data_field == "gpu":
                            # 提取GPU型號
                            gpu_match = re.search(r"AMD Radeon™\s+[A-Z0-9]+[A-Z]*", field_data)
                            row[model_name] = gpu_match.group(0) if gpu_match else "N/A"
                        elif data_field == "memory":
                            # 提取記憶體類型
                            memory_match = re.search(r"DDR\d+", field_data)
                            row[model_name] = memory_match.group(0) if memory_match else "N/A"
                        elif data_field == "storage":
                            # 提取儲存類型
                            storage_match = re.search(r"M\.2.*?PCIe.*?NVMe", field_data)
                            row[model_name] = storage_match.group(0) if storage_match else "N/A"
                        elif data_field == "battery":
                            # 提取電池容量
                            battery_match = re.search(r"(\d+\.?\d*)\s*Wh", field_data)
                            row[model_name] = f"{battery_match.group(1)}Wh" if battery_match else "N/A"
                        elif data_field == "thermal":
                            # 提取散熱設計
                            thermal_match = re.search(r"(\d+)W", field_data)
                            row[model_name] = f"{thermal_match.group(1)}W" if thermal_match else "N/A"
                        elif data_field == "structconfig":
                            # 提取結構配置信息
                            if feature_name == "Weight":
                                weight_match = re.search(r"Weight:\s*(\d+)\s*g", field_data)
                                if weight_match:
                                    weight_g = int(weight_match.group(1))
                                    weight_kg = weight_g / 1000
                                    row[model_name] = f"{weight_g}g ({weight_kg:.1f}kg)"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Dimensions":
                                dim_match = re.search(r"Dimension:\s*([\d\.]+\s*×\s*[\d\.]+\s*×\s*[\d\.]+\s*mm)", field_data)
                                row[model_name] = dim_match.group(1) if dim_match else "N/A"
                            elif feature_name == "Form Factor":
                                form_match = re.search(r"Form:\s*([^\n]+)", field_data)
                                row[model_name] = form_match.group(1) if form_match else "N/A"
                            elif feature_name == "Material":
                                material_match = re.search(r"Material[^:]*:\s*([^\n]+)", field_data)
                                row[model_name] = material_match.group(1) if material_match else "N/A"
                            else:
                                row[model_name] = "N/A"
                        else:
                            row[model_name] = "N/A"
                    else:
                        row[model_name] = "N/A"
                comparison_table.append(row)
            
            # 生成摘要
            if "輕便" in query or "重量" in query or "weight" in query.lower() or "portable" in query.lower():
                # 提取重量信息進行比較
                weights = {}
                for model_name in target_modelnames:
                    model_data = next((item for item in context_list_of_dicts if item.get("modelname") == model_name), None)
                    if model_data:
                        structconfig = model_data.get("structconfig", "")
                        weight_match = re.search(r"Weight:\s*(\d+)\s*g", structconfig)
                        if weight_match:
                            weights[model_name] = int(weight_match.group(1))
                
                if len(weights) >= 2:
                    # 找到最輕的型號
                    lightest_model = min(weights.keys(), key=lambda x: weights[x])
                    lightest_weight = weights[lightest_model]
                    heaviest_model = max(weights.keys(), key=lambda x: weights[x])
                    heaviest_weight = weights[heaviest_model]
                    
                    if lightest_weight < heaviest_weight:
                        weight_diff = heaviest_weight - lightest_weight
                        summary = f"根據重量比較，{lightest_model} 最輕便，重量為 {lightest_weight}g ({lightest_weight/1000:.1f}kg)，比 {heaviest_model} 輕 {weight_diff}g。"
                    else:
                        summary = f"根據提供的数据，{len(target_modelnames)} 个型号的重量相同或相近。"
                else:
                    summary = f"根据提供的数据，比较了 {len(target_modelnames)} 个笔电型号的重量规格。"
            elif "遊戲" in query or "gaming" in query.lower():
                summary = f"根据实际数据，{target_modelnames[0]} 系列包含 {len(target_modelnames)} 个游戏笔记型电脑型号，各有不同的性能配置。"
            else:
                summary = f"根据提供的数据，比较了 {len(target_modelnames)} 个笔电型号的规格。"
            
            # 使用美化表格格式化回應
            formatted_response = self._format_response_with_beautiful_table(
                summary,
                comparison_table,
                target_modelnames
            )
            
            return formatted_response
            
        except Exception as e:
            logging.error(f"生成備用回應時發生錯誤: {e}")
            return {
                "answer_summary": "抱歉，處理數據時發生錯誤。",
                "comparison_table": []
            }

    def _process_llm_response(self, parsed_json, context_list_of_dicts, target_modelnames):
        """
        處理LLM回應並生成最終結果
        """
        try:
            # 提取模型名稱
            model_names = []
            for item in context_list_of_dicts:
                model_name = item.get('modelname', 'Unknown')
                if model_name not in model_names:
                    model_names.append(model_name)
            
            # 檢查comparison_table格式並修正
            comparison_table = parsed_json.get("comparison_table", [])
            if isinstance(comparison_table, dict):
                # 轉換字典格式為列表格式
                comparison_table = self._convert_dict_to_list_of_dicts(comparison_table)
            
            # 使用美化表格格式化回應
            formatted_response = self._format_response_with_beautiful_table(
                parsed_json.get("answer_summary", ""),
                comparison_table,
                model_names
            )
            
            logging.info(f"LLM回答处理成功，answer_summary: {parsed_json.get('answer_summary', '')}")
            return formatted_response
            
        except Exception as e:
            logging.error(f"處理LLM回應時發生錯誤: {e}")
            return {
                "answer_summary": "抱歉，AI 回應的格式不正確，無法解析。",
                "comparison_table": []
            }

    def _process_llm_response_robust(self, parsed_json, context_list_of_dicts, target_modelnames, query):
        """
        更稳健的响应处理：使用两步骤策略
        优先使用LLM的answer_summary，即使comparison_table有问题
        """
        try:
            logging.info("開始使用兩步驟策略處理LLM回應")
            
            # 步骤1：分离验证
            validation_result = self._validate_llm_response_separated(parsed_json, target_modelnames)
            
            # 步骤2：优先使用LLM的answer_summary
            if validation_result["summary_valid"]:
                answer_summary = validation_result["answer_summary"]
                logging.info(f"使用LLM的answer_summary: {answer_summary}")
            else:
                # 生成备用summary
                answer_summary = self._generate_fallback_summary(query, context_list_of_dicts, target_modelnames)
                logging.info(f"使用備用answer_summary: {answer_summary}")
            
            # 步骤3：处理comparison_table
            if validation_result["table_valid"]:
                comparison_table = validation_result["comparison_table"]
                logging.info(f"使用LLM的comparison_table: {comparison_table}")
            else:
                # 生成备用table
                comparison_table = self._generate_fallback_table(context_list_of_dicts, target_modelnames, query)
                logging.info(f"使用備用comparison_table: {comparison_table}")
            
            # 步骤4：格式化最终响应
            formatted_response = self._format_response_with_beautiful_table(
                answer_summary,
                comparison_table,
                target_modelnames
            )
            
            logging.info(f"兩步驟策略處理完成 - answer_summary: {formatted_response.get('answer_summary', '')}")
            return formatted_response
            
        except Exception as e:
            logging.error(f"兩步驟策略處理失敗: {e}")
            # 如果两步骤策略失败，回退到原来的方法
            return self._process_llm_response(parsed_json, context_list_of_dicts, target_modelnames)

    def _generate_fallback_summary(self, query, context_list_of_dicts, target_modelnames):
        """
        生成备用的answer_summary
        """
        try:
            # 首先检查数据可用性
            query_intent = {
                "intent": "general",
                "query": query
            }
            
            # 根据查询内容确定意图
            query_lower = query.lower()
            if "螢幕" in query or "顯示" in query or "screen" in query_lower:
                query_intent["intent"] = "display"
            elif "電池" in query or "續航" in query or "battery" in query_lower:
                query_intent["intent"] = "battery"
            elif "cpu" in query_lower or "處理器" in query:
                query_intent["intent"] = "cpu"
            elif "gpu" in query_lower or "顯卡" in query:
                query_intent["intent"] = "gpu"
            elif "輕便" in query or "重量" in query or "weight" in query_lower:
                query_intent["intent"] = "portability"
            
            # 检查数据可用性
            has_data, missing_data_info = self._check_data_availability(context_list_of_dicts, target_modelnames, query_intent)
            
            if not has_data:
                # 如果没有相关数据，返回"並無登記資料"
                missing_info_str = "、".join(missing_data_info) if missing_data_info else "相關資料"
                return f"抱歉，{missing_info_str}並無登記資料。"
            
            # 根据查询类型生成不同的摘要
            if "螢幕" in query or "顯示" in query or "screen" in query_lower:
                if len(target_modelnames) > 1:
                    return f"根據提供的数据，{len(target_modelnames)}个型号的螢幕規格比較如下。"
                else:
                    return f"根據提供的数据，{target_modelnames[0]}的螢幕規格如下。"
            elif "電池" in query or "續航" in query or "battery" in query_lower:
                if len(target_modelnames) > 1:
                    return f"根據提供的数据，{len(target_modelnames)}个型号的電池規格比較如下。"
                else:
                    return f"根據提供的数据，{target_modelnames[0]}的電池規格如下。"
            elif "cpu" in query_lower or "處理器" in query:
                if len(target_modelnames) > 1:
                    return f"根據提供的数据，{len(target_modelnames)}个型号的CPU規格比較如下。"
                else:
                    return f"根據提供的数据，{target_modelnames[0]}的CPU規格如下。"
            elif "gpu" in query_lower or "顯卡" in query:
                if len(target_modelnames) > 1:
                    return f"根據提供的数据，{len(target_modelnames)}个型号的GPU規格比較如下。"
                else:
                    return f"根據提供的数据，{target_modelnames[0]}的GPU規格如下。"
            elif "輕便" in query or "重量" in query or "weight" in query_lower:
                if len(target_modelnames) > 1:
                    return f"根據提供的数据，{len(target_modelnames)}个型号的重量和便攜性比較如下。"
                else:
                    return f"根據提供的数据，{target_modelnames[0]}的重量和便攜性規格如下。"
            else:
                # 通用摘要
                if len(target_modelnames) > 1:
                    return f"根據提供的数据，{len(target_modelnames)}个型号的規格比較如下。"
                else:
                    return f"根據提供的数据，{target_modelnames[0]}的規格如下。"
                    
        except Exception as e:
            logging.error(f"生成備用summary失敗: {e}")
            return f"根據提供的数据，比較了 {len(target_modelnames)} 个笔电型号的规格。"

    def _check_data_availability(self, context_list_of_dicts, target_modelnames, query_intent):
        """
        检查查询特性的数据可用性
        返回 (has_data, missing_data_info)
        """
        try:
            intent = query_intent.get("intent", "general")
            query_lower = query_intent.get("query", "").lower()
            
            # 根据意图确定要检查的数据字段
            data_fields = []
            if intent == "display" or "螢幕" in query_lower or "顯示" in query_lower:
                data_fields = ["lcd"]
            elif intent == "cpu" or "cpu" in query_lower or "處理器" in query_lower:
                data_fields = ["cpu"]
            elif intent == "gpu" or "gpu" in query_lower or "顯卡" in query_lower:
                data_fields = ["gpu"]
            elif intent == "memory" or "記憶體" in query_lower or "內存" in query_lower:
                data_fields = ["memory"]
            elif intent == "storage" or "硬碟" in query_lower or "硬盤" in query_lower:
                data_fields = ["storage"]
            elif intent == "battery" or "電池" in query_lower or "續航" in query_lower:
                data_fields = ["battery"]
            elif intent == "portability" or "重量" in query_lower or "輕便" in query_lower:
                data_fields = ["structconfig"]
            elif intent == "connectivity" or "接口" in query_lower:
                data_fields = ["iointerface"]
            else:
                # 通用检查，检查主要字段
                data_fields = ["cpu", "gpu", "memory", "storage", "battery"]
            
            # 检查每个目标型号的数据
            missing_data_info = []
            has_valid_data = False
            
            for model_name in target_modelnames:
                model_data = next((item for item in context_list_of_dicts if item.get("modelname") == model_name), None)
                if model_data:
                    model_has_data = False
                    for field in data_fields:
                        field_value = model_data.get(field, "")
                        # 检查字段是否有有效数据
                        if field_value and field_value.strip() and field_value.lower() not in ["", "null", "none", "nan", "nodata", "n/a"]:
                            model_has_data = True
                            break
                    
                    if not model_has_data:
                        missing_data_info.append(f"{model_name} 的 {', '.join(data_fields)} 資料")
                    else:
                        has_valid_data = True
                else:
                    missing_data_info.append(f"{model_name} 的完整資料")
            
            # 如果没有找到任何有效数据
            if not has_valid_data:
                return False, missing_data_info
            
            return True, missing_data_info
            
        except Exception as e:
            logging.error(f"檢查數據可用性時發生錯誤: {e}")
            return False, ["數據檢查失敗"]

    def _generate_fallback_table(self, context_list_of_dicts, target_modelnames, query):
        """
        生成备用的comparison_table
        """
        try:
            # 根据查询类型决定要比较的特征
            if "螢幕" in query or "顯示" in query or "screen" in query.lower():
                features = [
                    ("Display Size", "lcd"),
                    ("Resolution", "lcd"),
                    ("Refresh Rate", "lcd"),
                    ("Panel Type", "lcd")
                ]
            elif "電池" in query or "續航" in query or "battery" in query.lower():
                features = [
                    ("Battery Capacity", "battery"),
                    ("Battery Life", "battery"),
                    ("Charging Speed", "battery")
                ]
            elif "cpu" in query.lower() or "處理器" in query:
                features = [
                    ("CPU Model", "cpu"),
                    ("CPU Architecture", "cpu"),
                    ("CPU TDP", "cpu")
                ]
            elif "gpu" in query.lower() or "顯卡" in query:
                features = [
                    ("GPU Model", "gpu"),
                    ("GPU Memory", "gpu"),
                    ("GPU Power", "gpu")
                ]
            elif "輕便" in query or "重量" in query or "weight" in query.lower():
                features = [
                    ("Weight", "structconfig"),
                    ("Dimensions", "structconfig"),
                    ("Form Factor", "structconfig")
                ]
            else:
                # 通用比较
                features = [
                    ("CPU Model", "cpu"),
                    ("GPU Model", "gpu"),
                    ("Memory Type", "memory"),
                    ("Storage Type", "storage"),
                    ("Battery Capacity", "battery")
                ]
            
            # 构建比较表格
            comparison_table = []
            for feature_name, data_field in features:
                row = {"feature": feature_name}
                for model_name in target_modelnames:
                    # 找到对应模型的数据
                    model_data = next((item for item in context_list_of_dicts if item.get("modelname") == model_name), None)
                    if model_data:
                        field_data = model_data.get(data_field, "")
                        # 提取关键信息
                        if data_field == "cpu":
                            # 根据特征名称提取不同的CPU信息
                            if feature_name == "CPU Model":
                                # 提取第一个CPU型号
                                cpu_match = re.search(r"Ryzen™\s+\d+\s+\d+[A-Z]*[HS]*", field_data)
                                row[model_name] = cpu_match.group(0) if cpu_match else "N/A"
                            elif feature_name == "CPU Architecture":
                                # 提取架构信息
                                arch_match = re.search(r"AMD\s+([^,]+)", field_data)
                                row[model_name] = arch_match.group(1).strip() if arch_match else "N/A"
                            elif feature_name == "CPU TDP":
                                # 提取TDP信息
                                tdp_match = re.search(r"TDP:\s*(\d+W)", field_data)
                                row[model_name] = tdp_match.group(1) if tdp_match else "N/A"
                            else:
                                # 默认提取第一个CPU型号
                                cpu_match = re.search(r"Ryzen™\s+\d+\s+\d+[A-Z]*[HS]*", field_data)
                                row[model_name] = cpu_match.group(0) if cpu_match else "N/A"
                        elif data_field == "gpu":
                            # 根据特征名称提取不同的GPU信息
                            if feature_name == "GPU Model":
                                # 提取第一个GPU型号
                                gpu_match = re.search(r"AMD Radeon™\s+[A-Z0-9]+[A-Z]*", field_data)
                                row[model_name] = gpu_match.group(0) if gpu_match else "N/A"
                            elif feature_name == "GPU Memory":
                                # 提取显存信息
                                memory_match = re.search(r"(\d+GB)\s+GDDR\d+", field_data)
                                row[model_name] = memory_match.group(1) if memory_match else "N/A"
                            elif feature_name == "GPU Power":
                                # 提取功耗信息
                                power_match = re.search(r"(\d+W)", field_data)
                                row[model_name] = power_match.group(1) if power_match else "N/A"
                            else:
                                # 默认提取第一个GPU型号
                                gpu_match = re.search(r"AMD Radeon™\s+[A-Z0-9]+[A-Z]*", field_data)
                                row[model_name] = gpu_match.group(0) if gpu_match else "N/A"
                        elif data_field == "memory":
                            # 提取内存类型
                            memory_match = re.search(r"DDR\d+", field_data)
                            row[model_name] = memory_match.group(0) if memory_match else "N/A"
                        elif data_field == "storage":
                            # 提取存储类型
                            storage_match = re.search(r"M\.2.*?PCIe.*?NVMe", field_data)
                            row[model_name] = storage_match.group(0) if storage_match else "N/A"
                        elif data_field == "battery":
                            # 提取电池容量
                            battery_match = re.search(r"(\d+\.?\d*)\s*Wh", field_data)
                            row[model_name] = f"{battery_match.group(1)}Wh" if battery_match else "N/A"
                        elif data_field == "lcd":
                            # 提取屏幕信息
                            if "FHD" in field_data:
                                row[model_name] = "FHD 1920×1080"
                            elif "QHD" in field_data:
                                row[model_name] = "QHD 2560×1440"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "structconfig":
                            # 提取重量信息
                            weight_match = re.search(r"Weight:\s*(\d+)\s*g", field_data)
                            if weight_match:
                                weight_g = int(weight_match.group(1))
                                row[model_name] = f"{weight_g}g ({weight_g/1000:.1f}kg)"
                            else:
                                row[model_name] = "N/A"
                        else:
                            row[model_name] = "N/A"
                    else:
                        row[model_name] = "N/A"
                
                comparison_table.append(row)
            
            return comparison_table
            
        except Exception as e:
            logging.error(f"生成備用table失敗: {e}")
            return []
    
    async def process_multichat_response(self, session_id: str, user_choice: str, user_input: str = ""):
        """
        處理多輪對話回應
        
        Args:
            session_id: 會話ID
            user_choice: 使用者選擇
            user_input: 使用者額外輸入
            
        Returns:
            處理結果（字典格式）
        """
        try:
            logging.info(f"處理多輪對話回應: session_id={session_id}, choice={user_choice}")
            
            # 獲取會話狀態
            if session_id not in self.multichat_manager.active_sessions:
                return {"error": "會話不存在或已過期"}
            
            session = self.multichat_manager.active_sessions[session_id]
            
            # 處理數字選擇轉換為option_id
            current_feature_id = session.chat_chain.features_order[session.current_step]
            current_feature = self.multichat_manager.nb_features[current_feature_id]
            
            # 如果是數字選擇，轉換為option_id
            actual_choice = user_choice
            if user_choice.isdigit():
                choice_index = int(user_choice) - 1
                if 0 <= choice_index < len(current_feature.options):
                    actual_choice = current_feature.options[choice_index].option_id
            
            # 處理使用者回應
            result = self.multichat_manager.process_feature_response(session_id, actual_choice, user_input)
            
            # 根據結果類型返回不同格式
            if result["action"] == "continue":
                # 繼續對話，返回下一個問題
                formatted_question = self.chat_template_manager.format_question(
                    result["next_question"],
                    result["current_step"] + 1,
                    result["total_steps"]
                )
                
                return {
                    "type": "multichat_continue",
                    "content": formatted_question,
                    "current_step": result["current_step"],
                    "total_steps": result["total_steps"]
                }
                
            elif result["action"] == "complete":
                # 對話完成，執行最終查詢
                logging.info("多輪對話完成，執行最終查詢")
                
                # 構建基於收集偏好的查詢意圖
                enhanced_query = result["enhanced_query"]
                preferences_summary = result["collected_preferences"]
                
                # 基於偏好構建query_intent
                query_intent = self._build_query_intent_from_multichat(result)
                
                # 執行查詢
                final_result = await self._execute_multichat_query(query_intent, preferences_summary, enhanced_query)
                
                # 清理會話
                del self.multichat_manager.active_sessions[session_id]
                
                return {
                    "type": "multichat_complete",
                    "content": final_result,
                    "enhanced_query": enhanced_query,
                    "preferences": preferences_summary
                }
            
        except Exception as e:
            logging.error(f"處理多輪對話回應失敗: {e}")
            return {"error": f"處理失敗: {str(e)}"}
    
    async def process_funnel_choice(self, session_id: str, choice_id: str) -> Dict[str, Any]:
        """
        處理漏斗對話選項選擇（API 端點使用）
        
        Args:
            session_id: 漏斗會話ID
            choice_id: 使用者選擇的選項ID
            
        Returns:
            處理結果
        """
        try:
            logging.info(f"處理漏斗選項選擇: session_id={session_id}, choice_id={choice_id}")
            
            # 處理使用者選擇
            funnel_result = self.funnel_manager.process_funnel_choice(session_id, choice_id)
            
            if "error" in funnel_result:
                return {"error": funnel_result["error"]}
            
            # 根據選擇的流程類型執行相應的處理
            if funnel_result["action"] == "route_to_flow":
                target_flow = FunnelFlowType(funnel_result["target_flow"])
                original_query = funnel_result["original_query"]
                user_choice = funnel_result["user_choice"]
                
                logging.info(f"路由到專業流程: {target_flow.value}")
                
                if target_flow == FunnelFlowType.SERIES_COMPARISON_FLOW:
                    # 系列比較流程：直接執行比較
                    return await self._execute_series_comparison_flow(original_query, user_choice)
                    
                elif target_flow == FunnelFlowType.PURPOSE_RECOMMENDATION_FLOW:
                    # 用途推薦流程：進入用途導向的多輪對話
                    return await self._execute_purpose_recommendation_flow(original_query, user_choice)
                    
                else:
                    return {"error": f"不支援的流程類型: {target_flow.value}"}
            
            return {"error": "未知的處理結果"}
            
        except Exception as e:
            logging.error(f"處理漏斗選項選擇失敗: {e}")
            return {"error": f"處理失敗: {str(e)}"}
    
    async def execute_specialized_flow(self, flow_type: str, original_query: str, user_choice: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行專業化流程（API 端點使用）
        
        Args:
            flow_type: 流程類型
            original_query: 原始查詢
            user_choice: 使用者選擇
            
        Returns:
            執行結果
        """
        try:
            logging.info(f"執行專業化流程: flow_type={flow_type}, query={original_query}")
            
            if flow_type == "series_comparison_flow":
                return await self._execute_series_comparison_flow(original_query, user_choice)
            elif flow_type == "purpose_recommendation_flow":
                return await self._execute_purpose_recommendation_flow(original_query, user_choice)
            else:
                return {"error": f"不支援的流程類型: {flow_type}"}
                
        except Exception as e:
            logging.error(f"執行專業化流程失敗: {e}")
            return {"error": f"執行失敗: {str(e)}"}
    
    async def get_funnel_question(self, query: str) -> Dict[str, Any]:
        """
        獲取 Funnel Conversation 問題（API 端點使用）
        
        Args:
            query: 使用者查詢
            
        Returns:
            Funnel 問題
        """
        try:
            logging.info(f"獲取 Funnel 問題: {query}")
            
            # 檢查是否應該觸發漏斗對話
            should_trigger_funnel, funnel_query_type = self.funnel_manager.should_trigger_funnel(query)
            
            if should_trigger_funnel:
                session_id, funnel_question = self.funnel_manager.start_funnel_session(query)
                
                return {
                    "type": "funnel_question",
                    "session_id": session_id,
                    "question": {
                        "question_id": funnel_question.question_id,
                        "question_text": funnel_question.question_text,
                        "options": funnel_question.options
                    },
                    "context": funnel_question.context,
                    "message": "請選擇最符合您需求的選項，我將為您提供更精準的協助。"
                }
            else:
                return {"error": "此查詢不需要漏斗對話"}
                
        except Exception as e:
            logging.error(f"獲取 Funnel 問題失敗: {e}")
            return {"error": f"獲取問題失敗: {str(e)}"}
    
    async def process_funnel_response(self, session_id: str, choice_id: str) -> Dict[str, Any]:
        """
        處理漏斗對話回應
        
        Args:
            session_id: 漏斗會話ID
            choice_id: 使用者選擇的選項ID
            
        Returns:
            處理結果
        """
        try:
            logging.info(f"處理漏斗回應: session_id={session_id}, choice_id={choice_id}")
            
            # 處理使用者選擇
            funnel_result = self.funnel_manager.process_funnel_choice(session_id, choice_id)
            
            if "error" in funnel_result:
                return {"error": funnel_result["error"]}
            
            # 根據選擇的流程類型執行相應的處理
            if funnel_result["action"] == "route_to_flow":
                target_flow = FunnelFlowType(funnel_result["target_flow"])
                original_query = funnel_result["original_query"]
                user_choice = funnel_result["user_choice"]
                
                logging.info(f"路由到專業流程: {target_flow.value}")
                
                if target_flow == FunnelFlowType.SERIES_COMPARISON_FLOW:
                    # 系列比較流程：直接執行比較
                    return await self._execute_series_comparison_flow(original_query, user_choice)
                    
                elif target_flow == FunnelFlowType.PURPOSE_RECOMMENDATION_FLOW:
                    # 用途推薦流程：進入用途導向的多輪對話
                    return await self._execute_purpose_recommendation_flow(original_query, user_choice)
                    
                else:
                    return {"error": f"不支援的流程類型: {target_flow.value}"}
            
            return {"error": "未知的處理結果"}
            
        except Exception as e:
            logging.error(f"處理漏斗回應失敗: {e}")
            return {"error": f"處理失敗: {str(e)}"}
    
    async def _execute_series_comparison_flow(self, original_query: str, user_choice: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行系列比較流程
        
        Args:
            original_query: 原始查詢
            user_choice: 使用者選擇
            
        Returns:
            比較結果
        """
        try:
            logging.info(f"執行系列比較流程: {original_query}")
            
            # 解析查詢意圖，專注於系列比較
            query_intent = self._parse_query_intent(original_query)
            
            # 如果沒有檢測到系列，嘗試從查詢中提取
            if not query_intent["modeltypes"]:
                import re
                series_match = re.search(r'\b(819|839|958)\b', original_query)
                if series_match:
                    query_intent["modeltypes"] = [series_match.group(1)]
                    query_intent["query_type"] = "model_type"
            
            # 獲取該系列的所有資料
            if query_intent["modeltypes"]:
                series_name = query_intent["modeltypes"][0]
                logging.info(f"比較系列: {series_name}")
                
                # 獲取該系列的所有機型資料
                context_list_of_dicts, target_modelnames = self._get_data_by_query_type(query_intent)
                
                if not context_list_of_dicts or not target_modelnames:
                    return {
                        "type": "series_comparison_result",
                        "error": f"找不到 {series_name} 系列的機型資料"
                    }
                
                # 直接生成 Markdown 表格，避免複雜的 LLM 調用
                markdown_table = self._generate_basic_specs_table(target_modelnames)
                
                # 生成簡單的總結
                summary = f"以下是 {series_name} 系列共 {len(target_modelnames)} 個機型的詳細規格比較："
                
                return {
                    "type": "series_comparison_result",
                    "summary": summary,
                    "comparison_table": markdown_table,
                    "detailed_comparison": f"已為您比較 {series_name} 系列的所有機型規格。",
                    "series_name": series_name,
                    "model_count": len(target_modelnames),
                    "models": target_modelnames
                }
                
            else:
                return {
                    "type": "series_comparison_result",
                    "error": "無法識別要比較的系列"
                }
                
        except Exception as e:
            logging.error(f"執行系列比較流程失敗: {e}")
            return {
                "type": "series_comparison_result",
                "error": f"系列比較失敗: {str(e)}"
            }
    
    def _generate_markdown_table(self, comparison_data: list, modelnames: list) -> str:
        """
        生成 Markdown 格式的比較表格
        
        Args:
            comparison_data: 比較資料
            modelnames: 機型名稱列表
            
        Returns:
            Markdown 表格字串
        """
        try:
            if not comparison_data:
                # 如果沒有比較資料，生成基本的規格表格
                return self._generate_basic_specs_table(modelnames)
            
            # 生成 Markdown 表格
            headers = ["規格項目"] + modelnames
            markdown = "| " + " | ".join(headers) + " |\n"
            markdown += "|" + "|".join(["---"] * len(headers)) + "|\n"
            
            for row in comparison_data:
                if isinstance(row, dict):
                    # 處理字典格式的資料
                    feature = row.get("feature", "未知規格")
                    values = [feature]
                    for model in modelnames:
                        values.append(str(row.get(model, "N/A")))
                    markdown += "| " + " | ".join(values) + " |\n"
                elif isinstance(row, list):
                    # 處理列表格式的資料
                    markdown += "| " + " | ".join([str(item) for item in row]) + " |\n"
            
            return markdown
            
        except Exception as e:
            logging.error(f"生成 Markdown 表格失敗: {e}")
            return "表格生成失敗"
    
    def _generate_basic_specs_table(self, modelnames: list) -> str:
        """
        生成基本的規格表格
        
        Args:
            modelnames: 機型名稱列表
            
        Returns:
            基本規格表格的 Markdown 字串
        """
        try:
            # 使用現有的 duckdb_query 實例，避免連接衝突
            if not hasattr(self, 'duckdb_query') or not self.duckdb_query:
                return "資料庫連接不可用"
            
            # 獲取指定機型的基本規格 - 選擇更簡潔的欄位
            placeholders = ",".join(["?"] * len(modelnames))
            query = f"""
                SELECT 
                    modelname,
                    SUBSTRING(cpu, 1, 100) as cpu_short,
                    SUBSTRING(gpu, 1, 100) as gpu_short,
                    SUBSTRING(memory, 1, 50) as memory_short,
                    SUBSTRING(storage, 1, 80) as storage_short,
                    SUBSTRING(lcd, 1, 80) as lcd_short
                FROM nbtypes 
                WHERE modelname IN ({placeholders})
                ORDER BY modelname
            """
            
            # 使用現有的 duckdb_query 執行查詢
            result = self.duckdb_query.query_with_params(query, modelnames)
            
            if not result:
                return "無法獲取機型規格資訊"
            
            # 調試：查看查詢結果格式
            logging.info(f"查詢結果格式: {len(result)} 行")
            for i, row in enumerate(result):
                logging.info(f"第 {i+1} 行: {row}")
            
            # 生成表格
            headers = ["機型", "CPU", "GPU", "記憶體", "儲存", "螢幕"]
            markdown = "| " + " | ".join(headers) + " |\n"
            markdown += "|" + "|".join(["---"] * len(headers)) + "|\n"
            
            for row in result:
                # 處理每個欄位的文本，確保正確換行和格式
                formatted_row = []
                for i, item in enumerate(row):
                    if item is None:
                        formatted_row.append("N/A")
                    else:
                        # 將長文本進行適當的換行處理
                        text = str(item).strip()
                        # 移除多餘的空白字符
                        text = ' '.join(text.split())
                        # 對於長文本，在適當位置添加換行
                        if len(text) > 40:
                            # 在句號或逗號後添加換行
                            text = text.replace('. ', '.<br>').replace(', ', ',<br>')
                        formatted_row.append(text)
                
                markdown += "| " + " | ".join(formatted_row) + " |\n"
            
            return markdown
            
        except Exception as e:
            logging.error(f"生成基本規格表格失敗: {e}")
            # 返回一個簡單的錯誤表格
            return f"| 機型 | 狀態 |\n| --- | --- |\n| {' | '.join(modelnames)} | 資料載入失敗 |"
    
    async def _execute_purpose_recommendation_flow(self, original_query: str, user_choice: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行用途推薦流程
        
        Args:
            original_query: 原始查詢
            user_choice: 使用者選擇
            
        Returns:
            推薦流程啟動結果
        """
        try:
            logging.info(f"執行用途推薦流程: {original_query}")
            
            # 從原始查詢中識別用途場景
            purpose_scenario = self._identify_purpose_scenario(original_query)
            
            # 啟動用途導向的多輪對話
            all_questions_response = self.get_all_questions(original_query, scenario=purpose_scenario)
            
            # 添加流程識別資訊
            all_questions_response["flow_type"] = "purpose_recommendation"
            all_questions_response["purpose_scenario"] = purpose_scenario
            all_questions_response["original_choice"] = user_choice
            
            return {
                "type": "purpose_recommendation_start",
                "content": all_questions_response,
                "original_query": original_query,
                "purpose_info": {
                    "scenario": purpose_scenario,
                    "flow_description": "根據您的用途需求，請回答以下問題以獲得個性化推薦"
                }
            }
            
        except Exception as e:
            logging.error(f"執行用途推薦流程失敗: {e}")
            return {"error": f"用途推薦流程啟動失敗: {str(e)}"}
    
    def _identify_purpose_scenario(self, query: str) -> str:
        """
        從查詢中識別用途場景
        
        Args:
            query: 使用者查詢
            
        Returns:
            場景類型
        """
        query_lower = query.lower()
        
        # 場景關鍵字映射
        scenario_keywords = {
            "gaming": ["遊戲", "gaming", "電競", "遊戲用", "玩遊戲", "game", "fps", "moba"],
            "business": ["商務", "辦公", "工作", "企業", "商用", "業務", "職場", "公司", "文書處理"],
            "creation": ["創作", "設計", "繪圖", "影片編輯", "剪輯", "photoshop", "3d建模"],
            "study": ["學習", "學生", "讀書", "課業", "上課", "study", "student", "教育"]
        }
        
        # 檢查各個場景的關鍵字
        for scenario, keywords in scenario_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                logging.info(f"識別用途場景: {scenario}")
                return scenario
        
        # 預設場景
        return "general"
    
    def _build_query_intent_from_multichat(self, multichat_result: dict) -> dict:
        """從多輪對話結果構建查詢意圖"""
        preferences = multichat_result.get("collected_preferences", {})
        
        query_intent = {
            "modelnames": [],
            "modeltypes": AVAILABLE_MODELTYPES.copy(),  # 預設包含所有系列
            "intents": [],
            "primary_intent": "multichat_guided",
            "query_type": "model_type",
            "confidence_score": 0.95,
            "multichat_enhanced": True
        }
        
        # 根據GPU偏好調整系列範圍
        if "gpu" in preferences:
            gpu_pref = preferences["gpu"]["selected_option"]
            if "遊戲級" in gpu_pref or "創作級" in gpu_pref:
                query_intent["modeltypes"] = ["958"]  # 高效能GPU通常在958系列
            elif "內建顯卡" in gpu_pref:
                query_intent["modeltypes"] = ["819", "839"]  # 內建顯卡通常在819/839系列
        
        return query_intent
    
    async def _execute_multichat_query(self, query_intent: dict, preferences_summary: dict, enhanced_query: str):
        """執行多輪對話引導的查詢"""
        try:
            # 根據query_intent獲取資料
            context_list_of_dicts, target_modelnames = self._get_data_by_query_type(query_intent)
            
            # 構建包含偏好的上下文
            preferences_text = "\n".join([
                f"- {feature_name}: {pref_data['selected_option']}"
                for feature_name, pref_data in preferences_summary.items()
                if pref_data.get('selected_option') and 'no_preference' not in pref_data.get('selected_option', '')
            ])
            
            # 構建專用於多輪對話的提示模板
            multichat_prompt = f"""
根據用戶通過多輪對話明確表達的需求偏好：
{preferences_text}

請基於以下資訊提供精準的筆電推薦：
- 所有偏好都已通過系統性問答收集
- 推薦應嚴格符合用戶明確表達的偏好
- 重點說明推薦機型如何滿足用戶的具體需求

{self.prompt_template}
"""
            
            # 調用LLM
            response_str = await self.llm.ainvoke(
                f"{multichat_prompt}\n\n使用者查詢: {enhanced_query}\n\n筆電資料:\n{json.dumps(context_list_of_dicts, ensure_ascii=False, indent=2)}"
            )
            
            # 解析並返回結果
            return {
                "answer_summary": response_str,
                "comparison_table": []
            }
            
        except Exception as e:
            logging.error(f"執行多輪對話查詢失敗: {e}")
            return {
                "answer_summary": "很抱歉，處理您的查詢時發生錯誤。請稍後重試。",
                "comparison_table": []
            }
    
    def get_all_questions(self, query: str = "", scenario: str = None) -> dict:
        """
        獲取所有多輪對話問題，用於一次性展示
        
        Args:
            query: 使用者原始查詢
            scenario: 場景類型 ("business", "gaming", "creation", "study", "general")
            
        Returns:
            包含所有問題的字典
        """
        try:
            logging.info(f"開始獲取所有多輪對話問題，場景: {scenario}")
            
            # 根據場景生成對話鍊
            if scenario and scenario != "general":
                try:
                    chat_chain = self.multichat_manager.chat_generator.get_chain_by_scenario(scenario)
                    logging.info(f"使用場景特定對話鍊: {scenario}")
                except Exception as e:
                    logging.warning(f"無法獲取場景特定對話鍊 {scenario}: {e}，使用隨機對話鍊")
                    chat_chain = self.multichat_manager.chat_generator.get_random_chain("random")
            else:
                chat_chain = self.multichat_manager.chat_generator.get_random_chain("random")
            
            # 構建所有問題
            all_questions = []
            for step, feature_id in enumerate(chat_chain.features_order):
                feature = self.multichat_manager.nb_features[feature_id]
                
                question_data = {
                    "step": step + 1,
                    "feature_id": feature_id,
                    "question": feature.question_template,
                    "options": [
                        {
                            "option_id": opt.option_id,
                            "label": opt.label,
                            "description": opt.description
                        } for opt in feature.options
                    ]
                }
                all_questions.append(question_data)
            
            response = {
                "type": "multichat_all_questions",
                "message": "請回答以下所有問題，我們將為您推薦最適合的筆電。",
                "questions": all_questions,
                "total_questions": len(all_questions)
            }
            
            logging.info(f"成功獲取 {len(all_questions)} 個問題")
            return response
            
        except Exception as e:
            logging.error(f"獲取所有問題失敗: {e}")
            return {
                "type": "error",
                "message": "獲取問題列表時發生錯誤，請稍後重試。"
            }
    
    async def process_all_questions_response(self, answers: dict) -> dict:
        """
        處理用戶對所有問題的回答
        
        Args:
            answers: 包含所有問題答案的字典 {feature_id: option_id}
            
        Returns:
            推薦結果
        """
        try:
            logging.info(f"開始處理所有問題的回答: {answers}")
            
            # 構建偏好總結
            preferences_summary = {}
            db_filters = {}
            
            for feature_id, option_id in answers.items():
                if feature_id in self.multichat_manager.nb_features:
                    feature = self.multichat_manager.nb_features[feature_id]
                    
                    # 找到對應的選項
                    selected_option = None
                    for option in feature.options:
                        if option.option_id == option_id:
                            selected_option = option
                            break
                    
                    if selected_option:
                        preferences_summary[feature_id] = {
                            "feature_name": feature.name,
                            "selected_option": selected_option.label,
                            "description": selected_option.description
                        }
                        
                        # 合併資料庫篩選條件
                        if selected_option.db_filter:
                            db_filters.update(selected_option.db_filter)
            
            # 生成增強查詢
            preferences_text = "\n".join([
                f"- {pref_data['feature_name']}: {pref_data['selected_option']}"
                for pref_data in preferences_summary.values()
                if 'no_preference' not in pref_data.get('selected_option', '')
            ])
            
            enhanced_query = f"根據以下偏好條件：{preferences_text}，請推薦適合的筆電"
            
            # 查詢相關資料
            try:
                # 這裡可以根據db_filters來查詢資料庫
                # 目前先使用基本查詢獲取所有筆電數據
                logging.info("開始查詢筆電規格數據")
                
                # 使用正確的SQL查詢方法
                full_specs_records = self.duckdb_query.query("SELECT * FROM nbtypes")
                
                if not full_specs_records:
                    logging.warning("未查詢到任何筆電數據")
                    return {
                        "type": "error",
                        "message": "目前沒有可用的筆電數據，請稍後重試。"
                    }
                
                # 轉換為字典格式
                full_context_list = [dict(zip(self.spec_fields, record)) for record in full_specs_records]
                logging.info(f"成功查詢到 {len(full_context_list)} 筆筆電數據")
                
                # 優化數據傳輸：只選擇核心規格欄位，減少數據大小
                core_fields = ['modeltype', 'modelname', 'cpu', 'gpu', 'memory', 'storage', 'lcd', 'battery']
                
                # 過濾並簡化數據
                filtered_laptops = []
                for laptop in full_context_list:
                    # 創建簡化的筆電資料
                    simplified_laptop = {}
                    for field in core_fields:
                        if field in laptop:
                            simplified_laptop[field] = laptop[field]
                    simplified_laptop['modelname'] = laptop.get('modelname', 'Unknown')
                    filtered_laptops.append(simplified_laptop)
                
                # 限制發送的筆電數量以避免數據過大 - 只發送前5筆
                limited_laptops = filtered_laptops[:5]
                logging.info(f"優化後發送 {len(limited_laptops)} 筆簡化筆電數據到LLM")
                
                # 直接構建推薦提示，嚴格要求輸出格式
                multichat_prompt = f"""
根據用戶需求：{preferences_text}

重要指示：
- 直接提供推薦結果，不要包含任何思考過程
- 不要使用「我會分析」、「讓我看看」、「首先」、「接下來」等詞語
- 不要包含分析步驟或解釋過程

輸出格式（嚴格遵守）：
每行格式：機型名稱 - 推薦原因

有效機型名稱僅限：AG958, AG958P, AG958V, APX958, AHP958, AKK839, ARB839, AB819-S: FP6, AMD819-S: FT6, AMD819: FT6, APX819: FP7R2, APX839, AHP819: FP7R2, AHP839, ARB819-S: FP7R2

正確範例：
APX958 - 高性能處理器和顯卡配置，適合專業工作需求
AG958P - 均衡的性能配置，適合日常辦公和學習
AHP958 - 旗艦級配置，適合高端應用需求

現在請直接提供推薦（只輸出機型和原因）：
"""
                
                # 調用LLM - 使用簡化的數據
                response_str = await self.llm.ainvoke(
                    f"{multichat_prompt}\n\n使用者查詢: {enhanced_query}\n\n可用筆電機型 (已精簡核心規格):\n{json.dumps(limited_laptops, ensure_ascii=False, indent=2)}"
                )
                
                # 輸出驗證和清理機制
                def validate_and_clean_response(raw_response: str) -> str:
                    """驗證並清理LLM回應，確保輸出品質"""
                    # 移除多餘的空白行和空格
                    cleaned_response = '\n'.join(line.strip() for line in raw_response.split('\n') if line.strip())
                    
                    # 如果回應太短或明顯是錯誤格式，直接返回空字符串觸發fallback
                    if len(cleaned_response) < 10:
                        logging.warning("LLM回應過短，將使用fallback")
                        return ""
                    
                    # 檢查是否包含思考過程指標詞
                    thinking_indicators = [
                        '我會分析', '讓我看看', '首先我需要', '接下來我會', '然後分析',
                        '分析一下', '考慮以下', '檢查規格', '從中挑選', '我的任務是',
                        '根據提供的', '將會推薦', '需要分析', '讓我們分析', '開始分析',
                        '可以看出', '讓我檢查', '我來分析', '分析這些機型'
                    ]
                    
                    # 如果回應主要是思考過程，觸發fallback
                    if any(indicator in cleaned_response for indicator in thinking_indicators):
                        thinking_count = sum(1 for indicator in thinking_indicators if indicator in cleaned_response)
                        if thinking_count >= 2:  # 多個思考指標表明這是思考過程
                            logging.warning(f"檢測到思考過程回應 (指標數: {thinking_count})，將使用fallback")
                            return ""
                    
                    # 驗證是否包含有效的機型名稱
                    valid_models = [
                        'AG958', 'AG958P', 'AG958V', 'APX958', 'AHP958', 'AKK839', 'ARB839',
                        'AB819-S: FP6', 'AMD819-S: FT6', 'AMD819: FT6', 'APX819: FP7R2', 
                        'APX839', 'AHP819: FP7R2', 'AHP839', 'ARB819-S: FP7R2'
                    ]
                    
                    found_valid_models = [model for model in valid_models if model in cleaned_response]
                    if not found_valid_models:
                        logging.warning("回應中未發現有效機型名稱，將使用fallback")
                        return ""
                    
                    logging.info(f"驗證通過，發現有效機型: {found_valid_models}")
                    return cleaned_response
                
                # 驗證LLM回應
                validated_response = validate_and_clean_response(response_str)
                if not validated_response:
                    # 如果驗證失敗，直接觸發fallback
                    raise ValueError("LLM回應驗證失敗")
                
                response_str = validated_response
                
                # 解析LLM回應並生成markdown表格
                try:
                    # 有效機型名稱列表（與prompt中一致）
                    valid_model_names = [
                        'AG958', 'AG958P', 'AG958V', 'APX958', 'AHP958', 'AKK839', 'ARB839',
                        'AB819-S: FP6', 'AMD819-S: FT6', 'AMD819: FT6', 'APX819: FP7R2', 
                        'APX839', 'AHP819: FP7R2', 'AHP839', 'ARB819-S: FP7R2'
                    ]
                    
                    # 思考過程關鍵字（用於過濾）
                    thinking_keywords = [
                        '我會', '讓我', '首先', '接下來', '然後', '分析', '看看', '考慮', 
                        '檢查', '搭下來', '從中挑選', '我的任務', '根據提供', '將會', 
                        '需要分析', '讓我們', '開始分析', '可以看出'
                    ]
                    
                    # 解析回應內容
                    lines = response_str.strip().split('\n')
                    recommendations = []
                    
                    logging.info(f"LLM 原始回應: {response_str}")
                    
                    for line in lines:
                        line = line.strip()
                        if not line or '-' not in line:
                            continue
                        
                        # 檢查是否包含思考過程關鍵字
                        if any(keyword in line for keyword in thinking_keywords):
                            logging.warning(f"過濾思考過程文字: {line}")
                            continue
                        
                        # 解析機型名稱和推薦原因
                        parts = line.split('-', 1)
                        if len(parts) == 2:
                            model_name = parts[0].strip()
                            reason = parts[1].strip()
                            
                            # 驗證機型名稱是否有效
                            if model_name in valid_model_names:
                                recommendations.append({
                                    "model_name": model_name,
                                    "reason": reason
                                })
                                logging.info(f"有效推薦已添加: {model_name} - {reason}")
                            else:
                                logging.warning(f"無效機型名稱被過濾: {model_name}")
                    
                    logging.info(f"解析完成，共找到 {len(recommendations)} 個有效推薦")
                    
                    # 生成標準 Markdown 表格
                    if recommendations:
                        # 過濾出有效的推薦機型（必須有 model_name）
                        valid_recommendations = [
                            rec for rec in recommendations 
                            if rec.get('model_name', '').strip()
                        ]
                        
                        if valid_recommendations:
                            # 建立簡化的雙欄 Markdown 表格格式
                            markdown_lines = []
                            
                            # 表格標題（移除綜合分析推薦欄位）
                            header = "| 推薦機型 | 推薦原因 |"
                            separator = "| --- | --- |"
                            markdown_lines.append(header)
                            markdown_lines.append(separator)
                            
                            # 添加有效的推薦機型行
                            for rec in valid_recommendations:
                                model_name = rec.get('model_name', '').strip()
                                reason = rec.get('reason', '').strip()
                                
                                # 清理內容，改用短橫線替代管線符號
                                clean_model = model_name.replace('\n', ' ').replace('|', '-')
                                clean_reason = reason.replace('\n', ' ').replace('|', '-')
                                
                                row = f"| {clean_model} | {clean_reason} |"
                                markdown_lines.append(row)
                            
                            # 生成最終的 markdown 表格
                            markdown_table = "\n".join(markdown_lines)
                            
                            logging.info(f"成功生成推薦表格，包含 {len(valid_recommendations)} 個有效推薦")
                            
                            return {
                                "type": "multichat_complete",
                                "message": "根據您的需求偏好，我們為您推薦以下筆電：",
                                "enhanced_query": enhanced_query,
                                "preferences_summary": preferences_summary,
                                "recommendations": markdown_table,
                                "db_filters": db_filters,
                                "is_table_format": True
                            }
                        else:
                            # 沒有有效推薦時不顯示表格
                            logging.warning("沒有有效的推薦機型，不生成表格")
                            return {
                                "type": "multichat_complete",
                                "message": "抱歉，根據您的需求條件，目前沒有合適的機型推薦。請嘗試調整您的需求條件。",
                                "enhanced_query": enhanced_query,
                                "preferences_summary": preferences_summary,
                                "recommendations": "",
                                "db_filters": db_filters,
                                "is_table_format": False
                            }
                    else:
                        raise ValueError("無法解析推薦內容")
                        
                except Exception as e:
                    logging.warning(f"表格生成失敗，使用智能fallback推薦: {e}")
                    
                    # 智能fallback推薦策略
                    fallback_recommendations = []
                    preferences_lower = preferences_text.lower()
                    
                    # 根據關鍵字提供智能推薦
                    if any(keyword in preferences_lower for keyword in ['文書處理', '文書', '處理', 'office', '辦公軟體', 'word', 'excel', 'ppt', '商務', 'business', '辦公', '輕薄', '攜帶']):
                        fallback_recommendations = [
                            ('AKK839', '輕薄商務機型，適合文書處理，長續航力'),
                            ('ARB839', '專業商務配置，文書處理效率高，穩定可靠'),
                            ('AB819-S: FP6', '超薄設計，商務辦公首選，適合文書處理')
                        ]
                    elif any(keyword in preferences_lower for keyword in ['遊戲', 'gaming', '顯卡', 'gpu', '高效能']):
                        fallback_recommendations = [
                            ('AG958P', '高效能遊戲筆電，搭載強勁GPU'),
                            ('APX958', '頂級遊戲配置，適合專業玩家'),
                            ('AHP958', '平衡性能與攜帶性的遊戲機型')
                        ]
                    elif any(keyword in preferences_lower for keyword in ['性價比', '預算', '經濟', '入門']):
                        fallback_recommendations = [
                            ('AMD819: FT6', '高性價比選擇，性能穩定'),
                            ('AMD819-S: FT6', '經濟實用型，適合日常使用'),
                            ('APX819: FP7R2', '入門級高效能配置')
                        ]
                    else:
                        # 通用推薦
                        fallback_recommendations = [
                            ('AG958', '全方位高效能機型'),
                            ('AKK839', '商務辦公優選'),
                            ('AMD819: FT6', '性價比推薦機型')
                        ]
                    
                    # 生成fallback表格
                    fallback_table_lines = [
                        "| 推薦機型 | 推薦原因 |",
                        "| --- | --- |"
                    ]
                    
                    for model, reason in fallback_recommendations:
                        fallback_table_lines.append(f"| {model} | {reason} |")
                    
                    fallback_table = '\n'.join(fallback_table_lines)
                    
                    return {
                        "type": "multichat_complete", 
                        "message": "根據您的需求偏好，我們為您推薦以下筆電：",
                        "enhanced_query": enhanced_query,
                        "preferences_summary": preferences_summary,
                        "recommendations": fallback_table,
                        "db_filters": db_filters,
                        "is_table_format": True
                    }
                
            except Exception as e:
                logging.error(f"查詢推薦資料失敗: {e}", exc_info=True)
                return {
                    "type": "error",
                    "message": f"查詢推薦資料時發生錯誤: {str(e)}。請檢查資料庫連接或稍後重試。"
                }
                
        except Exception as e:
            logging.error(f"處理所有問題回答失敗: {e}", exc_info=True)
            return {
                "type": "error",
                "message": f"處理您的回答時發生錯誤: {str(e)}。請重新填寫問卷或稍後重試。"
            }