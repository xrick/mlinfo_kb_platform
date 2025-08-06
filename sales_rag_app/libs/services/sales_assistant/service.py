import json
import pandas as pd
from ..base_service import BaseService
from ...RAG.DB.MilvusQuery import MilvusQuery
from ...RAG.DB.DuckDBQuery import DuckDBQuery
from ...RAG.LLM.LLMInitializer import LLMInitializer
from .entity_recognition import EntityRecognitionSystem
from .clarification_manager import ClarificationManager
from .parent_child_retriever import ParentChildRetriever
from .multichat import MultichatManager, ChatTemplateManager
import logging
import re

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 全域變數：存儲所有可用的modelname
AVAILABLE_MODELNAMES = [
    'AB819-S: FP6',
    'AG958',
    'AG958P',
    'AG958V',
    'AHP819: FP7R2',
    'AHP839',
    'AHP958',
    'AKK839',
    'AMD819-S: FT6',
    'AMD819: FT6',
    'APX819: FP7R2',
    'APX839',
    'APX958',
    'ARB819-S: FP7R2',
    'ARB839'
]

# 全域變數：存儲所有可用的modeltype
AVAILABLE_MODELTYPES = [
    '819',
    '839',
    '958'
]

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
        self.duckdb_query = DuckDBQuery(db_file="sales_rag_app/db/sales_specs.db")
        self.prompt_template = self._load_prompt_template("sales_rag_app/libs/services/sales_assistant/prompts/sales_prompt.txt")
        
        # 載入關鍵字配置
        self.intent_keywords = self._load_intent_keywords("sales_rag_app/libs/services/sales_assistant/prompts/query_keywords.json")
        
        # 初始化實體識別系統
        self.entity_recognizer = EntityRecognitionSystem()
        
        # 初始化澄清對話管理器
        self.clarification_manager = ClarificationManager()
        
        # 初始化多輪對話管理器
        self.multichat_manager = MultichatManager()
        self.chat_template_manager = ChatTemplateManager()
        
        # 初始化 Parent-Child 檢索系統 (替代三層意圖檢測)
        self.parent_child_retriever = ParentChildRetriever(
            duckdb_query_instance=self.duckdb_query,
            cache_dir="sales_rag_app/libs/services/sales_assistant/parent_child_cache"
        )
        
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
        增強版 JSON 格式修復，處理更多邊界情況
        """
        try:
            fixed = json_content.strip()
            
            # 1. 移除 JSON 前面的多餘內容（如思考過程）
            json_start = fixed.find('{')
            if json_start > 0:
                fixed = fixed[json_start:]
            
            # 2. 找到最後一個完整的 JSON 物件
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
            
            # 3. 修復常見的引號問題
            fixed = fixed.replace("'", '"')  # 單引號改雙引號
            
            # 4. 修復未轉義的引號（更全面的處理）
            # 處理各種內容中的引號問題
            fixed = self._fix_quotes_in_content(fixed)
            
            # 5. 修復多餘的逗號
            fixed = re.sub(r',\s*}', '}', fixed)  # 移除物件結尾的多餘逗號
            fixed = re.sub(r',\s*]', ']', fixed)  # 移除陣列結尾的多餘逗號
            
            # 6. 修復換行符和空格（保留必要的格式）
            fixed = re.sub(r'\n+', ' ', fixed)  # 換行符替換為空格
            fixed = re.sub(r'\s+', ' ', fixed)  # 多重空格合併
            
            # 7. 修復缺少的引號
            fixed = self._fix_missing_quotes(fixed)
            
            # 8. 修復不完整的結構
            fixed = self._fix_incomplete_structure(fixed)
            
            return fixed
            
        except Exception as e:
            logging.error(f"JSON 格式修復失敗: {e}")
            return json_content
    
    def _fix_quotes_in_content(self, content: str) -> str:
        """
        修復內容中的引號問題
        """
        try:
            # 處理 answer_summary 中的引號
            content = re.sub(r'"answer_summary"\s*:\s*"([^"]*?)(例如|比如|如下|建議|結論|總結|具體)："([^"]*?)"([^"]*?)"', 
                            r'"answer_summary": "\1\2：\\"\3\\"\4"', content)
            
            # 處理表格內容中的引號
            content = re.sub(r'("feature"\s*:\s*"[^"]*?)(")', r'\1\\"', content)
            
            # 處理模型名稱中的冒號（如 "APX819: FP7R2"）
            content = re.sub(r'("(?:AB819-S|AHP819|APX819|ARB819-S|AMD819): [^"]*?")', 
                            lambda m: m.group(1).replace(': ', '\\: '), content)
            
            return content
            
        except Exception as e:
            logging.error(f"修復引號時發生錯誤: {e}")
            return content
    
    def _fix_missing_quotes(self, content: str) -> str:
        """
        修復缺少的引號
        """
        try:
            # 修復鍵值對中缺少引號的情況
            content = re.sub(r'(\w+)(\s*:\s*")', r'"\1"\2', content)
            
            # 修復值中缺少引號的情況
            content = re.sub(r':\s*([^",}\]]+)([,}\]])', r': "\1"\2', content)
            
            return content
            
        except Exception as e:
            logging.error(f"修復缺少引號時發生錯誤: {e}")
            return content
    
    def _fix_incomplete_structure(self, content: str) -> str:
        """
        修復不完整的 JSON 結構
        """
        try:
            # 如果缺少結尾大括號
            if content.count('{') > content.count('}'):
                missing_braces = content.count('{') - content.count('}')
                content += '}' * missing_braces
            
            # 如果缺少結尾中括號
            if content.count('[') > content.count(']'):
                missing_brackets = content.count('[') - content.count(']')
                content += ']' * missing_brackets
            
            return content
            
        except Exception as e:
            logging.error(f"修復不完整結構時發生錯誤: {e}")
            return content
    
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
    
    def parse_llm_response_enhanced(self, llm_response: str) -> dict:
        """
        增強版 LLM 回應解析，具備強大的錯誤恢復能力
        """
        try:
            logging.info("開始增強版 LLM 回應解析")
            
            if not llm_response or not llm_response.strip():
                logging.warning("LLM 回應為空")
                return self._create_fallback_response("回應內容為空")
            
            # 1. 嘗試直接解析 JSON
            try:
                parsed = json.loads(llm_response)
                if self._validate_response_structure(parsed):
                    logging.info("直接 JSON 解析成功")
                    return self._enhance_parsed_response(parsed)
                else:
                    logging.warning("直接解析的 JSON 結構不符合要求")
            except json.JSONDecodeError as e:
                logging.info(f"直接 JSON 解析失敗: {e}")
            
            # 2. 嘗試修復後解析
            try:
                fixed_content = self._fix_json_format(llm_response)
                parsed = json.loads(fixed_content)
                if self._validate_response_structure(parsed):
                    logging.info("修復後 JSON 解析成功")
                    return self._enhance_parsed_response(parsed)
                else:
                    logging.warning("修復後的 JSON 結構不符合要求")
            except json.JSONDecodeError as e:
                logging.info(f"修復後 JSON 解析失敗: {e}")
            
            # 3. 嘗試部分提取
            try:
                partial_result = self._extract_partial_json(llm_response)
                if partial_result and self._validate_response_structure(partial_result):
                    logging.info("部分 JSON 提取成功")
                    return self._enhance_parsed_response(partial_result)
                else:
                    logging.warning("部分提取的內容不符合要求")
            except Exception as e:
                logging.info(f"部分 JSON 提取失敗: {e}")
            
            # 4. 嘗試智能提取
            try:
                smart_result = self._smart_extract_response(llm_response)
                if smart_result and self._validate_response_structure(smart_result):
                    logging.info("智能提取成功")
                    return self._enhance_parsed_response(smart_result)
                else:
                    logging.warning("智能提取的內容不符合要求")
            except Exception as e:
                logging.info(f"智能提取失敗: {e}")
            
            # 5. 生成後備回應
            logging.warning("所有解析方法都失敗，生成後備回應")
            return self._create_fallback_response("JSON 解析失敗，請重新嘗試")
            
        except Exception as e:
            logging.error(f"增強版 LLM 回應解析發生嚴重錯誤: {e}")
            return self._create_fallback_response("系統錯誤，請重新嘗試")
    
    def _validate_response_structure(self, response: dict) -> bool:
        """
        驗證回應結構是否符合要求
        """
        try:
            # 必須包含的基本欄位
            required_fields = ["answer_summary", "comparison_table"]
            
            for field in required_fields:
                if field not in response:
                    logging.warning(f"回應缺少必要欄位: {field}")
                    return False
            
            # 驗證 answer_summary
            if not isinstance(response["answer_summary"], str) or not response["answer_summary"].strip():
                logging.warning("answer_summary 格式錯誤或為空")
                return False
            
            # 驗證 comparison_table
            if not isinstance(response["comparison_table"], list):
                logging.warning("comparison_table 不是列表格式")
                return False
            
            # 如果有表格內容，驗證第一行
            if response["comparison_table"]:
                first_row = response["comparison_table"][0]
                if not isinstance(first_row, dict) or "feature" not in first_row:
                    logging.warning("comparison_table 格式錯誤，缺少 feature 欄位")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"驗證回應結構時發生錯誤: {e}")
            return False
    
    def _enhance_parsed_response(self, response: dict) -> dict:
        """
        增強解析後的回應，添加額外資訊和驗證
        """
        try:
            enhanced = response.copy()
            
            # 添加解析質量評分
            enhanced["parse_quality_score"] = self._calculate_parse_quality(response)
            
            # 添加時間戳
            enhanced["parsed_at"] = self._get_timestamp()
            
            # 驗證並修復模型名稱
            enhanced["comparison_table"] = self._validate_and_fix_model_names(response.get("comparison_table", []))
            
            # 添加統計資訊
            enhanced["stats"] = {
                "table_rows": len(enhanced["comparison_table"]),
                "model_count": self._count_models_in_table(enhanced["comparison_table"]),
                "features_covered": self._count_features_in_table(enhanced["comparison_table"])
            }
            
            return enhanced
            
        except Exception as e:
            logging.error(f"增強回應時發生錯誤: {e}")
            return response
    
    def _calculate_parse_quality(self, response: dict) -> float:
        """
        計算解析品質評分 (0.0 - 1.0)
        """
        try:
            score = 0.0
            
            # 基礎分數：有基本結構
            if "answer_summary" in response and "comparison_table" in response:
                score += 0.4
            
            # answer_summary 品質
            summary = response.get("answer_summary", "")
            if summary and len(summary) > 10:
                score += 0.2
                if len(summary) > 50:
                    score += 0.1
            
            # comparison_table 品質
            table = response.get("comparison_table", [])
            if table:
                score += 0.2
                # 檢查表格完整性
                if len(table) > 1:  # 有實際的比較內容
                    score += 0.1
                # 檢查模型名稱的有效性
                valid_models = self._count_valid_models_in_table(table)
                if valid_models > 0:
                    score += min(0.1, valid_models * 0.05)
            
            return min(score, 1.0)
            
        except Exception as e:
            logging.error(f"計算解析品質評分時發生錯誤: {e}")
            return 0.5
    
    def _smart_extract_response(self, content: str) -> dict:
        """
        智能提取回應內容，處理非標準格式
        """
        try:
            result = {}
            
            # 使用更靈活的方式提取 summary
            summary_patterns = [
                r'(?:answer_summary|summary|摘要|總結)[\s]*[:：]\s*"?([^"\n]+)"?',
                r'"answer_summary"\s*:\s*"([^"]+)"',
                r'總結[:：]?\s*([^\n]+)',
                r'答案[:：]?\s*([^\n]+)'
            ]
            
            for pattern in summary_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    result["answer_summary"] = match.group(1).strip()
                    break
            
            # 如果沒有找到摘要，嘗試從內容中生成
            if "answer_summary" not in result:
                lines = content.split('\n')
                for line in lines[:5]:  # 檢查前5行
                    if len(line.strip()) > 20 and not line.strip().startswith('{'):
                        result["answer_summary"] = line.strip()
                        break
            
            # 提取表格（如果存在）
            result["comparison_table"] = []
            
            # 嘗試從 markdown 表格提取
            table_content = self._extract_markdown_table(content)
            if table_content:
                result["comparison_table"] = table_content
            
            return result if result else None
            
        except Exception as e:
            logging.error(f"智能提取時發生錯誤: {e}")
            return None
    
    def _extract_markdown_table(self, content: str) -> list:
        """
        從 markdown 表格中提取資料
        """
        try:
            table_data = []
            lines = content.split('\n')
            
            # 找到表格開始
            table_start = -1
            for i, line in enumerate(lines):
                if '|' in line and 'feature' in line.lower():
                    table_start = i
                    break
            
            if table_start == -1:
                return []
            
            # 解析表格
            header_line = lines[table_start]
            headers = [h.strip(' |') for h in header_line.split('|') if h.strip()]
            
            # 跳過分隔線
            data_start = table_start + 2
            
            for i in range(data_start, len(lines)):
                line = lines[i]
                if not line.strip() or '|' not in line:
                    break
                
                row_data = [d.strip(' |') for d in line.split('|') if d.strip()]
                if len(row_data) >= len(headers):
                    row_dict = {}
                    for j, header in enumerate(headers):
                        if j < len(row_data):
                            row_dict[header] = row_data[j]
                    table_data.append(row_dict)
            
            return table_data
            
        except Exception as e:
            logging.error(f"提取 markdown 表格時發生錯誤: {e}")
            return []
    
    def _create_fallback_response(self, error_message: str) -> dict:
        """
        創建後備回應
        """
        return {
            "answer_summary": f"抱歉，處理您的查詢時遇到問題：{error_message}。請重新描述您的需求，我將為您提供更好的服務。",
            "comparison_table": [],
            "parse_quality_score": 0.0,
            "parsed_at": self._get_timestamp(),
            "is_fallback": True,
            "stats": {
                "table_rows": 0,
                "model_count": 0,
                "features_covered": 0
            }
        }
    
    def _validate_and_fix_model_names(self, table: list) -> list:
        """
        驗證並修復表格中的模型名稱
        """
        try:
            if not table:
                return table
            
            fixed_table = []
            
            for row in table:
                if not isinstance(row, dict):
                    continue
                
                fixed_row = {}
                for key, value in row.items():
                    # 檢查鍵是否為有效的模型名稱
                    if key != "feature":
                        if key in AVAILABLE_MODELNAMES:
                            fixed_row[key] = value
                        else:
                            # 嘗試模糊匹配
                            fuzzy_matches = self._fuzzy_match_model_name(key)
                            if fuzzy_matches:
                                # 使用第一個匹配結果
                                fixed_row[fuzzy_matches[0]] = value
                                logging.info(f"修復模型名稱: {key} -> {fuzzy_matches[0]}")
                            else:
                                # 保留原始鍵但記錄警告
                                fixed_row[key] = value
                                logging.warning(f"無法識別的模型名稱: {key}")
                    else:
                        fixed_row[key] = value
                
                fixed_table.append(fixed_row)
            
            return fixed_table
            
        except Exception as e:
            logging.error(f"驗證和修復模型名稱時發生錯誤: {e}")
            return table
    
    def _count_models_in_table(self, table: list) -> int:
        """計算表格中的模型數量"""
        if not table:
            return 0
        
        model_names = set()
        for row in table:
            if isinstance(row, dict):
                for key in row.keys():
                    if key != "feature":
                        model_names.add(key)
        
        return len(model_names)
    
    def _count_features_in_table(self, table: list) -> int:
        """計算表格中的特徵數量"""
        return len(table) if table else 0
    
    def _count_valid_models_in_table(self, table: list) -> int:
        """計算表格中有效的模型數量"""
        if not table:
            return 0
        
        valid_models = set()
        for row in table:
            if isinstance(row, dict):
                for key in row.keys():
                    if key != "feature" and key in AVAILABLE_MODELNAMES:
                        valid_models.add(key)
        
        return len(valid_models)
    
    def _get_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def validate_response_quality(self, response: dict, query: str, query_intent: dict) -> dict:
        """
        全面的回應品質驗證系統
        """
        try:
            logging.info("開始回應品質驗證")
            
            quality_report = {
                "overall_score": 0.0,
                "scores": {},
                "issues": [],
                "suggestions": [],
                "validation_passed": False
            }
            
            # 1. 結構完整性檢查
            structure_score = self._validate_structure_completeness(response)
            quality_report["scores"]["structure"] = structure_score
            
            # 2. 內容準確性檢查
            accuracy_score = self._validate_content_accuracy(response, query_intent)
            quality_report["scores"]["accuracy"] = accuracy_score
            
            # 3. 相關性檢查
            relevance_score = self._validate_response_relevance(response, query, query_intent)
            quality_report["scores"]["relevance"] = relevance_score
            
            # 4. 完整性檢查
            completeness_score = self._validate_response_completeness(response, query_intent)
            quality_report["scores"]["completeness"] = completeness_score
            
            # 5. 可讀性檢查
            readability_score = self._validate_response_readability(response)
            quality_report["scores"]["readability"] = readability_score
            
            # 計算總分
            weights = {
                "structure": 0.25,
                "accuracy": 0.25,
                "relevance": 0.20,
                "completeness": 0.20,
                "readability": 0.10
            }
            
            quality_report["overall_score"] = sum(
                quality_report["scores"][key] * weights[key]
                for key in weights.keys()
            )
            
            # 判斷是否通過驗證
            quality_report["validation_passed"] = quality_report["overall_score"] >= 0.7
            
            # 生成改進建議
            quality_report["suggestions"] = self._generate_improvement_suggestions(quality_report)
            
            logging.info(f"品質驗證完成，總分: {quality_report['overall_score']:.2f}")
            return quality_report
            
        except Exception as e:
            logging.error(f"回應品質驗證時發生錯誤: {e}")
            return {
                "overall_score": 0.0,
                "scores": {},
                "issues": [f"驗證過程發生錯誤: {e}"],
                "suggestions": ["請重新生成回應"],
                "validation_passed": False
            }
    
    def _validate_structure_completeness(self, response: dict) -> float:
        """驗證結構完整性"""
        try:
            score = 0.0
            
            # 檢查必要欄位
            if "answer_summary" in response:
                score += 0.4
                if isinstance(response["answer_summary"], str) and len(response["answer_summary"].strip()) > 0:
                    score += 0.1
            
            if "comparison_table" in response:
                score += 0.4
                if isinstance(response["comparison_table"], list):
                    score += 0.1
                    if response["comparison_table"]:  # 非空
                        score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logging.error(f"結構完整性驗證錯誤: {e}")
            return 0.0
    
    def _validate_content_accuracy(self, response: dict, query_intent: dict) -> float:
        """驗證內容準確性"""
        try:
            score = 0.0
            table = response.get("comparison_table", [])
            
            if not table:
                return 0.5  # 沒有表格不一定是錯誤
            
            # 檢查模型名稱準確性
            valid_model_count = 0
            total_model_count = 0
            
            for row in table:
                if isinstance(row, dict):
                    for key in row.keys():
                        if key != "feature":
                            total_model_count += 1
                            if key in AVAILABLE_MODELNAMES:
                                valid_model_count += 1
            
            if total_model_count > 0:
                model_accuracy = valid_model_count / total_model_count
                score += model_accuracy * 0.6
            
            # 檢查特徵名稱合理性
            feature_count = len([row for row in table if isinstance(row, dict) and "feature" in row])
            if feature_count > 0:
                score += 0.4
                
            return min(score, 1.0)
            
        except Exception as e:
            logging.error(f"內容準確性驗證錯誤: {e}")
            return 0.0
    
    def _validate_response_relevance(self, response: dict, query: str, query_intent: dict) -> float:
        """驗證回應相關性"""
        try:
            score = 0.0
            
            # 檢查回應是否與查詢意圖相符
            primary_intent = query_intent.get("primary_intent", "general")
            table = response.get("comparison_table", [])
            summary = response.get("answer_summary", "").lower()
            
            # 根據意圖類型檢查相關性
            if primary_intent == "comparison":
                if len(table) > 0 and self._count_models_in_table(table) > 1:
                    score += 0.5
                if any(word in summary for word in ["比較", "compare", "差異", "不同"]):
                    score += 0.3
            
            elif primary_intent in ["cpu", "gpu", "memory", "battery", "storage"]:
                # 檢查是否包含相應的規格特徵
                relevant_features = self._get_relevant_features_for_intent(primary_intent)
                if table:
                    table_features = [row.get("feature", "").lower() for row in table if isinstance(row, dict)]
                    matching_features = sum(1 for feature in relevant_features if any(rf in feature for rf in relevant_features))
                    if matching_features > 0:
                        score += 0.5
                
                # 檢查摘要中是否提到相關關鍵詞
                intent_keywords = self.intent_keywords.get(primary_intent, {}).get("keywords", [])
                if any(keyword.lower() in summary for keyword in intent_keywords):
                    score += 0.3
            
            elif primary_intent == "specifications":
                if table and len(table) > 2:  # 有多個規格項目
                    score += 0.5
                if any(word in summary for word in ["規格", "specification", "配置"]):
                    score += 0.3
            
            # 檢查目標模型是否出現在回應中
            target_models = query_intent.get("modelnames", [])
            if target_models:
                response_text = json.dumps(response, ensure_ascii=False).lower()
                matched_models = sum(1 for model in target_models if model.lower() in response_text)
                if matched_models > 0:
                    score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logging.error(f"相關性驗證錯誤: {e}")
            return 0.0
    
    def _validate_response_completeness(self, response: dict, query_intent: dict) -> float:
        """驗證回應完整性"""
        try:
            score = 0.0
            
            # 檢查摘要完整性
            summary = response.get("answer_summary", "")
            if len(summary) > 20:
                score += 0.3
                if len(summary) > 100:
                    score += 0.2
            
            # 檢查表格完整性
            table = response.get("comparison_table", [])
            if table:
                # 檢查是否有足夠的特徵項目
                feature_count = len(table)
                if feature_count >= 3:
                    score += 0.3
                    if feature_count >= 5:
                        score += 0.1
                
                # 檢查是否包含多個模型
                model_count = self._count_models_in_table(table)
                if model_count >= 2:
                    score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logging.error(f"完整性驗證錯誤: {e}")
            return 0.0
    
    def _validate_response_readability(self, response: dict) -> float:
        """驗證回應可讀性"""
        try:
            score = 0.0
            
            # 檢查摘要可讀性
            summary = response.get("answer_summary", "")
            if summary:
                # 檢查是否包含標點符號
                if any(punct in summary for punct in ["。", "，", "；", "：", ".", ",", ";", ":"]):
                    score += 0.3
                
                # 檢查長度適中性
                if 20 <= len(summary) <= 300:
                    score += 0.2
                
                # 檢查是否使用繁體中文
                if self._is_traditional_chinese(summary):
                    score += 0.2
            
            # 檢查表格可讀性
            table = response.get("comparison_table", [])
            if table:
                # 檢查特徵名稱是否有意義
                valid_features = 0
                total_features = 0
                
                for row in table:
                    if isinstance(row, dict) and "feature" in row:
                        total_features += 1
                        feature_name = row["feature"].strip()
                        if len(feature_name) > 2 and not feature_name.isdigit():
                            valid_features += 1
                
                if total_features > 0:
                    feature_quality = valid_features / total_features
                    score += feature_quality * 0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logging.error(f"可讀性驗證錯誤: {e}")
            return 0.0
    
    def _get_relevant_features_for_intent(self, intent: str) -> list:
        """根據意圖獲取相關的特徵關鍵詞"""
        feature_mapping = {
            "cpu": ["cpu", "處理器", "processor", "核心", "core"],
            "gpu": ["gpu", "顯卡", "graphics", "radeon"],
            "memory": ["記憶體", "內存", "memory", "ram", "ddr"],
            "battery": ["電池", "battery", "續航", "電量"],
            "storage": ["硬碟", "硬盤", "storage", "ssd", "nvme"],
            "display": ["螢幕", "顯示", "screen", "lcd"],
            "portability": ["重量", "尺寸", "weight", "dimension"]
        }
        return feature_mapping.get(intent, [])
    
    def _is_traditional_chinese(self, text: str) -> bool:
        """檢查文本是否主要使用繁體中文"""
        try:
            # 檢查一些常見的繁簡字對
            traditional_chars = ["電", "記憶體", "螢幕", "顯示", "處理器", "規格"]
            simplified_chars = ["电", "内存", "屏幕", "显示", "处理器", "规格"]
            
            traditional_count = sum(1 for char in traditional_chars if char in text)
            simplified_count = sum(1 for char in simplified_chars if char in text)
            
            return traditional_count >= simplified_count
            
        except Exception as e:
            logging.error(f"繁體中文檢查錯誤: {e}")
            return True  # 預設為True
    
    def _generate_improvement_suggestions(self, quality_report: dict) -> list:
        """根據品質報告生成改進建議"""
        suggestions = []
        scores = quality_report.get("scores", {})
        
        if scores.get("structure", 0) < 0.7:
            suggestions.append("改進回應結構：確保包含完整的 answer_summary 和 comparison_table")
        
        if scores.get("accuracy", 0) < 0.7:
            suggestions.append("提高內容準確性：檢查模型名稱和規格資訊的正確性")
        
        if scores.get("relevance", 0) < 0.7:
            suggestions.append("增強相關性：確保回應內容與用戶查詢意圖相符")
        
        if scores.get("completeness", 0) < 0.7:
            suggestions.append("完善回應內容：提供更詳細的比較資訊和特徵說明")
        
        if scores.get("readability", 0) < 0.7:
            suggestions.append("改善可讀性：使用清晰的繁體中文和適當的格式")
        
        return suggestions
    
    def generate_dynamic_prompt(self, query: str, query_intent: dict, context: list) -> str:
        """
        根據查詢意圖和上下文動態生成優化的提示模板
        """
        try:
            logging.info("開始生成動態提示")
            
            # 基礎提示模板
            base_prompt = self.prompt_template
            
            # 根據意圖類型進行動態調整
            primary_intent = query_intent.get("primary_intent", "general")
            target_models = query_intent.get("modelnames", [])
            confidence_score = query_intent.get("confidence_score", 0.0)
            
            # 動態調整提示內容
            enhanced_prompt = self._enhance_prompt_for_intent(base_prompt, primary_intent, query_intent)
            
            # 添加模型特定的指導
            if target_models:
                enhanced_prompt = self._add_model_specific_guidance(enhanced_prompt, target_models)
            
            # 根據信心度調整嚴格程度
            if confidence_score < 0.6:
                enhanced_prompt = self._add_uncertainty_handling(enhanced_prompt, query)
            
            # 添加品質控制指令
            enhanced_prompt = self._add_quality_control_instructions(enhanced_prompt, query_intent)
            
            # 添加多意圖處理指令
            if len(query_intent.get("intents", [])) > 1:
                enhanced_prompt = self._add_multi_intent_instructions(enhanced_prompt, query_intent["intents"])
            
            logging.info(f"動態提示生成完成，意圖: {primary_intent}, 信心度: {confidence_score:.2f}")
            return enhanced_prompt
            
        except Exception as e:
            logging.error(f"動態提示生成失敗: {e}")
            return self.prompt_template  # 回退到原始模板
    
    def _enhance_prompt_for_intent(self, base_prompt: str, intent: str, query_intent: dict) -> str:
        """
        根據具體意圖增強提示內容
        """
        try:
            # 意圖特定的指導
            intent_guidance = {
                "comparison": """
[COMPARISON FOCUS]
- 重點突出兩個或多個模型之間的差異
- 在 comparison_table 中明確顯示對比項目
- 在 answer_summary 中提供清晰的比較結論
- 特別注意效能差異和適用場景
""",
                "cpu": """
[CPU FOCUS]
- 專注於處理器相關規格：型號、核心數、頻率、架構
- 在表格中包含 CPU Model、CPU Cores/Threads、CPU Frequency 等特徵
- 解釋 CPU 效能對日常使用和專業工作的影響
- 提及功耗和散熱特性
""",
                "gpu": """
[GPU FOCUS]
- 專注於顯卡相關規格：型號、記憶體、效能等級
- 強調遊戲和圖形處理能力
- 在表格中包含 GPU Model、GPU Memory、Graphics Performance 等特徵
- 解釋適合的應用場景（辦公、遊戲、創作）
""",
                "memory": """
[MEMORY FOCUS]
- 專注於記憶體規格：容量、類型、頻率、擴展性
- 在表格中包含 RAM Capacity、RAM Type、RAM Speed 等特徵
- 解釋記憶體對系統效能的影響
- 提及升級可能性
""",
                "battery": """
[BATTERY FOCUS]
- 專注於電池相關規格：容量、續航時間、充電速度
- 在表格中包含 Battery Capacity、Battery Life、Charging Speed 等特徵
- 提供實際使用情境下的續航估算
- 考慮不同使用模式的電池表現
""",
                "storage": """
[STORAGE FOCUS]
- 專注於儲存相關規格：容量、類型、速度、擴展性
- 在表格中包含 Storage Type、Storage Capacity、Storage Speed 等特徵
- 解釋 SSD vs HDD 的效能差異
- 提及升級和擴展選項
""",
                "portability": """
[PORTABILITY FOCUS]
- 專注於便攜性：重量、尺寸、材質、設計
- 在表格中包含 Weight、Dimensions、Build Quality 等特徵
- 評估攜帶便利性和日常使用場景
- 考慮耐用性和設計美感
""",
                "latest": """
[LATEST MODELS FOCUS]
- 強調最新的技術特性和改進
- 突出與前代產品的差異和優勢
- 提及最新的軟硬體支援
- 評估技術前瞻性和投資價值
"""
            }
            
            specific_guidance = intent_guidance.get(intent, "")
            if specific_guidance:
                # 在現有提示中插入特定指導
                insertion_point = base_prompt.find("[QUERY INTENT ANALYSIS]")
                if insertion_point != -1:
                    enhanced_prompt = base_prompt[:insertion_point] + specific_guidance + "\n" + base_prompt[insertion_point:]
                else:
                    enhanced_prompt = base_prompt + "\n" + specific_guidance
            else:
                enhanced_prompt = base_prompt
            
            return enhanced_prompt
            
        except Exception as e:
            logging.error(f"意圖特定提示增強失敗: {e}")
            return base_prompt
    
    def _add_model_specific_guidance(self, prompt: str, target_models: list) -> str:
        """
        添加模型特定的指導
        """
        try:
            model_guidance = f"""
[TARGET MODELS GUIDANCE]
- 本次查詢重點關注的模型：{', '.join(target_models)}
- 確保在 comparison_table 中使用這些確切的模型名稱
- 重點比較這些特定模型的規格差異
- 在 answer_summary 中明確提及這些模型的特點
"""
            
            # 在提示末尾添加模型指導
            return prompt + "\n" + model_guidance
            
        except Exception as e:
            logging.error(f"模型特定指導添加失敗: {e}")
            return prompt
    
    def _add_uncertainty_handling(self, prompt: str, query: str) -> str:
        """
        添加不確定性處理指令
        """
        try:
            uncertainty_guidance = """
[UNCERTAINTY HANDLING]
- 查詢意圖不太明確，請特別注意：
- 如果無法確定具體的比較需求，提供通用的規格概覽
- 在 answer_summary 中說明可能的理解並建議用戶澄清需求
- 避免做出過於具體的推薦，除非有充分的資料支持
- 如果資料不足，誠實說明限制並建議替代方案
"""
            
            return prompt + "\n" + uncertainty_guidance
            
        except Exception as e:
            logging.error(f"不確定性處理指令添加失敗: {e}")
            return prompt
    
    def _add_quality_control_instructions(self, prompt: str, query_intent: dict) -> str:
        """
        添加品質控制指令
        """
        try:
            quality_instructions = """
[ENHANCED QUALITY CONTROL]
- 嚴格遵循 JSON 格式要求，確保輸出可以被成功解析
- 所有模型名稱必須完全匹配資料庫中的 modelname 欄位
- comparison_table 的第一欄必須是 "feature"，包含規格類型名稱
- answer_summary 必須是簡潔明瞭的繁體中文總結
- 如果資料不足，使用 "N/A" 而非猜測或虛構資訊
- 確保表格結構一致，每行都包含相同的模型欄位
"""
            
            return prompt + "\n" + quality_instructions
            
        except Exception as e:
            logging.error(f"品質控制指令添加失敗: {e}")
            return prompt
    
    def _add_multi_intent_instructions(self, prompt: str, intents: list) -> str:
        """
        添加多意圖處理指令
        """
        try:
            intent_names = [intent["name"] for intent in intents if intent["confidence"] > 0.3]
            
            multi_intent_guidance = f"""
[MULTI-INTENT HANDLING]
- 檢測到多個查詢意圖：{', '.join(intent_names)}
- 請在回應中平衡處理所有相關意圖
- 在 comparison_table 中包含所有相關的規格類型
- 在 answer_summary 中綜合考慮所有意圖，提供全面的分析
- 優先處理信心度最高的意圖，同時兼顧其他相關需求
"""
            
            return prompt + "\n" + multi_intent_guidance
            
        except Exception as e:
            logging.error(f"多意圖處理指令添加失敗: {e}")
            return prompt
    
    def create_adaptive_prompt_template(self, success_patterns: dict = None, failure_patterns: dict = None) -> str:
        """
        基於歷史成功和失敗模式創建自適應提示模板
        """
        try:
            # 基礎模板
            adaptive_template = self.prompt_template
            
            # 如果有成功模式，強化相關指令
            if success_patterns:
                for pattern, frequency in success_patterns.items():
                    if frequency > 0.8:  # 高成功率的模式
                        enhancement = self._create_pattern_enhancement(pattern, True)
                        adaptive_template += f"\n{enhancement}"
            
            # 如果有失敗模式，添加避免指令
            if failure_patterns:
                for pattern, frequency in failure_patterns.items():
                    if frequency > 0.3:  # 常見失敗模式
                        avoidance = self._create_pattern_enhancement(pattern, False)
                        adaptive_template += f"\n{avoidance}"
            
            return adaptive_template
            
        except Exception as e:
            logging.error(f"自適應提示模板創建失敗: {e}")
            return self.prompt_template
    
    def _create_pattern_enhancement(self, pattern: str, is_success: bool) -> str:
        """
        基於模式創建提示增強
        """
        if is_success:
            return f"[SUCCESS PATTERN] 繼續使用成功模式：{pattern}"
        else:
            return f"[AVOID PATTERN] 避免失敗模式：{pattern}"

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
        
        for modeltype in AVAILABLE_MODELTYPES:
            if modeltype.lower() in query_lower:
                found_modeltypes.append(modeltype)
        
        return len(found_modeltypes) > 0, found_modeltypes

    def _get_models_by_type(self, modeltype: str) -> list:
        """
        根據modeltype獲取所有相關的modelname
        """
        try:
            # 使用DuckDB查詢包含該modeltype的所有modelname
            sql_query = "SELECT DISTINCT modelname FROM specs WHERE modelname LIKE ?"
            pattern = f"%{modeltype}%"
            
            results = self.duckdb_query.query_with_params(sql_query, [pattern])
            
            if results:
                modelnames = [record[0] for record in results]
                logging.info(f"根據modeltype '{modeltype}' 找到的modelname: {modelnames}")
                return modelnames
            else:
                logging.warning(f"未找到包含modeltype '{modeltype}' 的modelname")
                return []
                
        except Exception as e:
            logging.error(f"查詢modeltype '{modeltype}' 相關modelname時發生錯誤: {e}")
            return []

    def _parse_query_intent(self, query: str) -> dict:
        """
        增強版查詢意圖解析，整合實體識別系統
        支援多意圖檢測和信心度評分
        """
        try:
            logging.info(f"開始增強版查詢意圖解析: {query}")
            
            # 使用實體識別系統進行全面分析
            entity_analysis = self.entity_recognizer.process_text(query)
            
            result = {
                "modelnames": [],
                "modeltypes": [],
                "intents": [],  # 支援多意圖
                "primary_intent": "general",  # 主要意圖
                "query_type": "unknown",
                "entities": entity_analysis.get("entities", []),
                "confidence_score": 0.0,
                "entity_intent_relations": entity_analysis.get("relations", [])
            }
            
            # 1. 從實體識別結果中提取模型名稱和類型
            for entity in entity_analysis.get("entities", []):
                if entity["label"] == "MODEL_NAME":
                    # 精確匹配
                    if entity["text"] in AVAILABLE_MODELNAMES:
                        result["modelnames"].append(entity["text"])
                        result["query_type"] = "specific_model"
                    else:
                        # 模糊匹配
                        fuzzy_matches = self._fuzzy_match_model_name(entity["text"])
                        if fuzzy_matches:
                            result["modelnames"].extend(fuzzy_matches)
                            result["query_type"] = "specific_model"
                            logging.info(f"模糊匹配到模型: {entity['text']} -> {fuzzy_matches}")
                elif entity["label"] == "MODEL_TYPE":
                    if entity["text"] in AVAILABLE_MODELTYPES:
                        result["modeltypes"].append(entity["text"])
                        if result["query_type"] == "unknown":
                            result["query_type"] = "model_type"
            
            # 2. 多意圖檢測 - 使用加權評分系統
            intent_scores = {}
            query_lower = query.lower()
            
            for intent_name, intent_config in self.intent_keywords.items():
                keywords = intent_config.get("keywords", [])
                score = 0.0
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword.lower() in query_lower:
                        # 基礎分數
                        keyword_score = 1.0
                        
                        # 根據關鍵字長度調整權重
                        keyword_score *= (len(keyword) / 10.0 + 0.5)
                        
                        # 檢查是否為完整詞彙匹配
                        if f" {keyword.lower()} " in f" {query_lower} ":
                            keyword_score *= 1.5
                        
                        score += keyword_score
                        matched_keywords.append(keyword)
                
                if score > 0:
                    intent_scores[intent_name] = {
                        "score": score,
                        "keywords": matched_keywords,
                        "confidence": min(score / len(keywords), 1.0) if keywords else 0.0
                    }
            
            # 3. 排序意圖並選擇主要意圖
            sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1]["score"], reverse=True)
            
            if sorted_intents:
                # 主要意圖
                result["primary_intent"] = sorted_intents[0][0]
                result["confidence_score"] = sorted_intents[0][1]["confidence"]
                
                # 所有檢測到的意圖（分數 > 0.3 的）
                result["intents"] = [
                    {
                        "name": intent_name,
                        "confidence": intent_data["confidence"],
                        "keywords": intent_data["keywords"]
                    }
                    for intent_name, intent_data in sorted_intents
                    if intent_data["confidence"] > 0.3
                ]
                
                logging.info(f"檢測到多個意圖: {[i['name'] for i in result['intents']]}")
            
            # 4. 後備意圖推斷 - 根據實體類型推斷可能的意圖
            if result["primary_intent"] == "general" and entity_analysis.get("entities"):
                inferred_intent = self._infer_intent_from_entities(entity_analysis.get("entities", []))
                if inferred_intent:
                    result["primary_intent"] = inferred_intent
                    result["confidence_score"] = 0.6  # 推斷的信心度較低
                    logging.info(f"根據實體推斷意圖: {inferred_intent}")
            
            # 5. 為了向後兼容，保持舊的 intent 欄位
            result["intent"] = result["primary_intent"]
            
            logging.info(f"增強版查詢意圖解析結果: {result}")
            return result
            
        except Exception as e:
            logging.error(f"增強版查詢意圖解析時發生錯誤: {e}")
            # 回退到原始方法
            return self._parse_query_intent_fallback(query)
    
    def _infer_intent_from_entities(self, entities: list) -> str:
        """
        根據實體類型推斷可能的意圖
        """
        entity_labels = [entity["label"] for entity in entities]
        
        # 推斷規則
        if "COMPARISON_WORD" in entity_labels:
            return "comparison"
        elif "SPEC_TYPE" in entity_labels:
            spec_entities = [e for e in entities if e["label"] == "SPEC_TYPE"]
            if spec_entities:
                spec_text = spec_entities[0]["text"].lower()
                if any(word in spec_text for word in ["cpu", "處理器"]):
                    return "cpu"
                elif any(word in spec_text for word in ["gpu", "顯卡"]):
                    return "gpu"
                elif any(word in spec_text for word in ["記憶體", "內存", "memory"]):
                    return "memory"
                elif any(word in spec_text for word in ["電池", "battery"]):
                    return "battery"
                else:
                    return "specifications"
        elif "TIME_WORD" in entity_labels:
            return "latest"
        elif "PERFORMANCE_WORD" in entity_labels:
            return "specifications"
        elif "PRICE_WORD" in entity_labels:
            return "general"  # 目前沒有價格相關的意圖
        
        return None
    
    def _fuzzy_match_model_name(self, input_name: str, threshold: float = 0.7) -> list:
        """
        模糊匹配模型名稱，處理拼寫錯誤或部分匹配
        """
        try:
            matches = []
            input_lower = input_name.lower().strip()
            
            for available_name in AVAILABLE_MODELNAMES:
                available_lower = available_name.lower()
                
                # 1. 子字串匹配
                if input_lower in available_lower or available_lower in input_lower:
                    matches.append(available_name)
                    continue
                
                # 2. 相似度計算（簡單版本）
                similarity = self._calculate_string_similarity(input_lower, available_lower)
                if similarity >= threshold:
                    matches.append(available_name)
                    logging.info(f"相似度匹配: {input_name} <-> {available_name} (相似度: {similarity:.2f})")
                
                # 3. 關鍵部分匹配（型號系列）
                input_series = self._extract_model_series(input_lower)
                available_series = self._extract_model_series(available_lower)
                if input_series and available_series and input_series == available_series:
                    matches.append(available_name)
                    logging.info(f"系列匹配: {input_name} <-> {available_name} (系列: {input_series})")
            
            # 去重並限制結果數量
            matches = list(dict.fromkeys(matches))[:3]  # 最多返回3個匹配結果
            
            return matches
            
        except Exception as e:
            logging.error(f"模糊匹配時發生錯誤: {e}")
            return []
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        計算兩個字串的相似度（簡化版 Levenshtein 距離）
        """
        try:
            if not str1 or not str2:
                return 0.0
            
            if str1 == str2:
                return 1.0
            
            # 簡化版相似度計算
            max_len = max(len(str1), len(str2))
            if max_len == 0:
                return 1.0
            
            # 計算共同字符數
            common_chars = 0
            str1_chars = list(str1)
            str2_chars = list(str2)
            
            for char in str1_chars:
                if char in str2_chars:
                    common_chars += 1
                    str2_chars.remove(char)
            
            return common_chars / max_len
            
        except Exception as e:
            logging.error(f"計算字串相似度時發生錯誤: {e}")
            return 0.0
    
    def _extract_model_series(self, model_name: str) -> str:
        """
        從模型名稱中提取系列標識符
        """
        try:
            # 提取數字部分（如819, 839, 958）
            import re
            series_match = re.search(r'(819|839|958)', model_name)
            if series_match:
                return series_match.group(1)
            return None
        except Exception as e:
            logging.error(f"提取模型系列時發生錯誤: {e}")
            return None
    
    def _parse_query_intent_fallback(self, query: str) -> dict:
        """
        原始的意圖解析方法作為後備
        """
        try:
            result = {
                "modelnames": [],
                "modeltypes": [],
                "intents": [],
                "primary_intent": "general",
                "intent": "general",
                "query_type": "unknown",
                "entities": [],
                "confidence_score": 0.0,
                "entity_intent_relations": []
            }
            
            # 1. 檢查模型名稱
            contains_modelname, found_modelnames = self._check_query_contains_modelname(query)
            if contains_modelname:
                result["modelnames"] = found_modelnames
                result["query_type"] = "specific_model"
            
            # 2. 檢查模型類型
            contains_modeltype, found_modeltypes = self._check_query_contains_modeltype(query)
            if contains_modeltype:
                result["modeltypes"] = found_modeltypes
                if result["query_type"] == "unknown":
                    result["query_type"] = "model_type"
            
            # 3. 簡單意圖檢測
            query_lower = query.lower()
            for intent_name, intent_config in self.intent_keywords.items():
                keywords = intent_config.get("keywords", [])
                if any(keyword.lower() in query_lower for keyword in keywords):
                    result["intent"] = intent_name
                    result["primary_intent"] = intent_name
                    result["intents"] = [{"name": intent_name, "confidence": 0.8, "keywords": keywords}]
                    break
            
            return result
            
        except Exception as e:
            logging.error(f"後備意圖解析失敗: {e}")
            return {
                "modelnames": [],
                "modeltypes": [],
                "intents": [],
                "primary_intent": "general",
                "intent": "general",
                "query_type": "unknown",
                "entities": [],
                "confidence_score": 0.0,
                "entity_intent_relations": []
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
                sql_query = f"SELECT * FROM specs WHERE modelname IN ({placeholders})"
                
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
                sql_query = f"SELECT * FROM specs WHERE modelname IN ({placeholders})"
                
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

    async def process_clarification_response(self, conversation_id: str, user_choice: str, user_input: str = ""):
        """
        處理用戶的澄清回應
        
        Args:
            conversation_id: 對話ID
            user_choice: 用戶選擇的選項ID
            user_input: 用戶額外輸入
            
        Returns:
            處理結果
        """
        try:
            logging.info(f"處理澄清回應: conversation_id={conversation_id}, choice={user_choice}")
            
            # 處理澄清回應
            result = self.clarification_manager.process_clarification_response(
                conversation_id, user_choice, user_input
            )
            
            if result["action"] == "continue":
                # 需要下一步澄清
                next_question = result["next_question"]
                
                clarification_response = {
                    "message_type": "clarification_request",
                    "conversation_id": conversation_id,
                    "question": next_question.question,
                    "question_type": next_question.question_type,
                    "options": next_question.options,
                    "current_step": result["current_step"],
                    "total_steps": result["total_steps"],
                    "template_name": next_question.template_name,
                    "answer_summary": "感謝您的回覆！請繼續協助我了解您的需求："
                }
                
                return clarification_response
                
            elif result["action"] == "complete":
                # 澄清完成，使用增強的意圖重新查詢
                enhanced_intent = result["enhanced_intent"]
                clarification_summary = result["clarification_summary"]
                
                logging.info(f"澄清完成，增強意圖: {enhanced_intent}")
                
                # 重新構建查詢意圖用於數據檢索
                enhanced_query_intent = self._build_query_intent_from_enhanced(enhanced_intent)
                
                # 執行正常的查詢流程
                return await self._execute_enhanced_query(enhanced_query_intent, clarification_summary)
            
            else:
                raise ValueError(f"未知的澄清動作: {result['action']}")
                
        except Exception as e:
            logging.error(f"處理澄清回應時發生錯誤: {e}")
            return {
                "message_type": "error",
                "answer_summary": f"處理澄清回應時發生錯誤: {str(e)}",
                "comparison_table": []
            }

    def _build_query_intent_from_enhanced(self, enhanced_intent: dict) -> dict:
        """
        從增強意圖構建查詢意圖
        """
        clarification_context = enhanced_intent.get("clarification_context", {})
        primary_intent = enhanced_intent.get("primary_intent", "general")
        priority_specs = enhanced_intent.get("priority_specs", [])
        
        # 根據使用場景和澄清資訊構建查詢意圖
        usage_scenario = clarification_context.get("usage_scenario", "")
        
        # 映射使用場景到型號系列
        modeltype_mapping = {
            "gaming": "958",      # 遊戲娛樂 -> 高性能958系列
            "business": "819",    # 商務辦公 -> 819系列
            "creation": "958",    # 設計創作 -> 高性能958系列
            "study": "839"        # 學習研究 -> 中階839系列
        }
        
        query_intent = {
            "modelnames": [],
            "modeltypes": [modeltype_mapping.get(usage_scenario, "839")],  # 預設中階
            "intents": priority_specs,
            "primary_intent": primary_intent,
            "intent": primary_intent,
            "query_type": "model_type",  # 基於系列進行查詢
            "confidence_score": enhanced_intent.get("confidence_score", 0.9),
            "clarification_enhanced": True,
            "clarification_context": clarification_context
        }
        
        return query_intent

    async def _execute_enhanced_query(self, query_intent: dict, clarification_summary: str):
        """
        使用增強意圖執行查詢
        """
        try:
            # 獲取數據
            context_list_of_dicts, target_modelnames = self._get_data_by_query_type(query_intent)
            
            # 構建增強的上下文
            enhanced_context = {
                "data": context_list_of_dicts,
                "query_intent": query_intent,
                "target_modelnames": target_modelnames,
                "clarification_summary": clarification_summary
            }
            
            context_str = json.dumps(enhanced_context, indent=2, ensure_ascii=False)
            
            # 構建針對澄清結果的特殊提示
            clarification_prompt = f"""
根據用戶的澄清回應：{clarification_summary}

請基於以下資訊提供精準的筆電推薦：
- 使用場景已確認
- 需求優先級已明確
- 推薦重點應符合澄清結果

{self.prompt_template}
"""
            
            # 構建查詢（基於澄清結果的虛擬查詢）
            virtual_query = f"根據我的需求（{clarification_summary}），推薦適合的筆電"
            
            final_prompt = clarification_prompt.replace("{context}", context_str).replace("{query}", virtual_query)
            
            # 調用 LLM
            response_str = self.llm_initializer.invoke(final_prompt)
            
            # 解析回應
            think_end = response_str.find("</think>")
            if think_end != -1:
                cleaned_response_str = response_str[think_end + 8:].strip()
            else:
                cleaned_response_str = response_str
            
            json_start = cleaned_response_str.find("{")
            json_end = cleaned_response_str.rfind("}")
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_content = cleaned_response_str[json_start:json_end+1]
                
                try:
                    parsed_json = json.loads(json_content)
                    
                    # 添加澄清資訊到回應
                    parsed_json["message_type"] = "final_response"
                    parsed_json["clarification_summary"] = clarification_summary
                    
                    return parsed_json
                    
                except json.JSONDecodeError:
                    # JSON 解析失敗的後備方案
                    return {
                        "message_type": "final_response",
                        "answer_summary": cleaned_response_str,
                        "comparison_table": [],
                        "clarification_summary": clarification_summary
                    }
            else:
                # 沒有找到 JSON 格式的後備方案
                return {
                    "message_type": "final_response",
                    "answer_summary": cleaned_response_str,
                    "comparison_table": [],
                    "clarification_summary": clarification_summary
                }
                
        except Exception as e:
            logging.error(f"執行增強查詢時發生錯誤: {e}")
            return {
                "message_type": "error",
                "answer_summary": f"查詢時發生錯誤: {str(e)}",
                "comparison_table": []
            }

    async def chat_stream(self, query: str, **kwargs):
        """
        新的RAG流程：
        1. 解析用户查询意图（modelname、modeltype、intent）
        2. 根据查询类型获取精确数据
        3. 将数据和查询意图传递给LLM
        """
        try:
            logging.info(f"開始新的RAG流程，查詢: {query}")
            
            # 步骤0.5：檢查是否應該啟動多輪對話導引
            should_start_multichat = self.multichat_manager.should_activate_multichat(query)
            if should_start_multichat:
                logging.info("檢測到模糊查詢，啟動多輪對話導引系統")
                try:
                    session_id, first_question = self.multichat_manager.start_multichat_flow(query)
                    formatted_question = self.chat_template_manager.format_session_start(
                        query, 
                        self.chat_template_manager.format_question(
                            first_question, 
                            first_question.step, 
                            len(self.multichat_manager.active_sessions[session_id].chat_chain.features_order)
                        )
                    )
                    
                    # 以串流方式返回多輪對話開始訊息
                    yield f"data: {json.dumps({'type': 'multichat_start', 'session_id': session_id, 'content': formatted_question}, ensure_ascii=False)}\n\n"
                    return
                    
                except Exception as e:
                    logging.error(f"啟動多輪對話失敗: {e}")
                    # 如果多輪對話啟動失敗，繼續使用原有流程
            
            # 步骤1：使用 Parent-Child 檢索系統 (替代原有的三層意圖檢測)
            logging.info("使用 Parent-Child 檢索系統處理查詢")
            query_intent = self.parent_child_retriever.process_query(query)
            logging.info(f"Parent-Child 檢索結果: {query_intent.get('primary_intent', 'unknown')}")
            
            # 步骤1.5：檢查是否需要澄清 (Parent-Child 系統幾乎不需要澄清)
            should_clarify = self.parent_child_retriever.should_clarify(query_intent)
            if should_clarify:
                logging.warning("Parent-Child 系統觸發澄清請求（極罕見情況）")
                # 即使在極少數情況下，我們也提供一般性推薦而非澄清
                query_intent.update({
                    "modelnames": [],
                    "modeltypes": ["819", "839", "958"],
                    "primary_intent": "general",
                    "query_type": "model_type"
                })
                logging.info("已轉換為一般性推薦，避免澄清請求")
            
            # 检查是否有有效的查询类型
            if query_intent["query_type"] == "unknown":
                # 智能分析用戶查詢，生成具體問題而不是要求重新輸入
                smart_questions = self._generate_smart_clarification_questions(query, query_intent)
                
                if smart_questions:
                    # 構建智能澄清回應
                    clarification_response = {
                        "message_type": "smart_clarification",
                        "original_query": query,
                        "questions": smart_questions,
                        "answer_summary": "我理解您的需求，讓我幫您找到最適合的筆電。請回答以下問題："
                    }
                    yield f"data: {json.dumps(clarification_response, ensure_ascii=False)}\n\n"
                    return
                else:
                    # 如果無法生成智能問題，提供友善的幫助信息
                    help_message = self._generate_user_friendly_help(query)
                    help_response = {
                        "answer_summary": help_message,
                        "comparison_table": []
                    }
                    yield f"data: {json.dumps(help_response, ensure_ascii=False)}\n\n"
                    return
            
            # 步骤2：根据查询类型获取精确数据
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
            
            # 步骤3：构建增强的上下文，整合 Parent-Child 檢索結果
            enhanced_context = {
                "data": context_list_of_dicts,
                "query_intent": query_intent,
                "target_modelnames": target_modelnames
            }
            
            # 添加 Parent-Child 特定的上下文信息
            parent_child_context = self.parent_child_retriever.get_enhanced_context_for_llm(query_intent)
            enhanced_context["parent_child_guidance"] = parent_child_context
            
            context_str = json.dumps(enhanced_context, indent=2, ensure_ascii=False)
            logging.info("成功构建 Parent-Child 增强上下文")
            
            # 步骤4：构建提示并请求LLM
            # 构建包含 Parent-Child 分析信息的 prompt
            parent_child_data = query_intent.get("parent_child_data", {})
            response_strategy = parent_child_data.get("response_strategy", "general")
            retrieval_confidence = parent_child_data.get("retrieval_confidence", 0.0)
            
            intent_info = f"""
[PARENT-CHILD QUERY ANALYSIS]
使用 Parent-Child 檢索系統分析結果：
- 查詢類型: {query_intent['query_type']}
- 主要意圖: {query_intent['primary_intent']}
- 目標型號: {', '.join(target_modelnames)}
- 回應策略: {response_strategy}
- 檢索信心度: {retrieval_confidence:.2f}

Parent-Child 回應指導：
{parent_child_context}

請根據以上 Parent-Child 分析結果，提供精準且有用的回應。
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
        生成备用的comparison_table - 擴展版本，包含更多筆電特性
        """
        try:
            # 根据查询类型决定要比较的特征
            if "螢幕" in query or "顯示" in query or "screen" in query.lower():
                features = [
                    ("Display Size", "lcd"),
                    ("Resolution", "lcd"),
                    ("Refresh Rate", "lcd"),
                    ("Panel Type", "lcd"),
                    ("Color Gamut", "lcd"),
                    ("Brightness", "lcd"),
                    ("Touch Support", "lcd")
                ]
            elif "電池" in query or "續航" in query or "battery" in query.lower():
                features = [
                    ("Battery Capacity", "battery"),
                    ("Battery Life", "battery"),
                    ("Charging Speed", "battery"),
                    ("Power Adapter", "battery"),
                    ("Fast Charging", "battery")
                ]
            elif "cpu" in query.lower() or "處理器" in query:
                features = [
                    ("CPU Model", "cpu"),
                    ("CPU Architecture", "cpu"),
                    ("CPU TDP", "cpu"),
                    ("CPU Cores", "cpu"),
                    ("CPU Threads", "cpu"),
                    ("CPU Base Speed", "cpu"),
                    ("CPU Boost Speed", "cpu"),
                    ("CPU Cache", "cpu")
                ]
            elif "gpu" in query.lower() or "顯卡" in query:
                features = [
                    ("GPU Model", "gpu"),
                    ("GPU Memory", "gpu"),
                    ("GPU Power", "gpu"),
                    ("GPU Architecture", "gpu"),
                    ("GPU Cores", "gpu"),
                    ("GPU Boost Clock", "gpu"),
                    ("Ray Tracing", "gpu"),
                    ("DLSS/FSR Support", "gpu")
                ]
            elif "記憶體" in query or "內存" in query or "memory" in query.lower() or "ram" in query.lower():
                features = [
                    ("Memory Type", "memory"),
                    ("Memory Speed", "memory"),
                    ("Memory Capacity", "memory"),
                    ("Memory Channels", "memory"),
                    ("Memory Slots", "memory"),
                    ("Max Memory", "memory")
                ]
            elif "硬碟" in query or "硬盤" in query or "storage" in query.lower() or "ssd" in query.lower():
                features = [
                    ("Storage Type", "storage"),
                    ("Storage Capacity", "storage"),
                    ("Storage Speed", "storage"),
                    ("Storage Slots", "storage"),
                    ("Secondary Storage", "storage"),
                    ("Storage Interface", "storage")
                ]
            elif "輕便" in query or "重量" in query or "weight" in query.lower() or "portable" in query.lower():
                features = [
                    ("Weight", "structconfig"),
                    ("Dimensions", "structconfig"),
                    ("Form Factor", "structconfig"),
                    ("Material", "structconfig"),
                    ("Thickness", "structconfig"),
                    ("Build Quality", "structconfig")
                ]
            elif "散熱" in query or "thermal" in query.lower() or "cooling" in query.lower():
                features = [
                    ("Thermal Design", "thermal"),
                    ("Cooling System", "thermal"),
                    ("Fan Configuration", "thermal"),
                    ("Thermal Performance", "thermal"),
                    ("Noise Level", "thermal")
                ]
            elif "接口" in query or "port" in query.lower() or "connectivity" in query.lower():
                features = [
                    ("USB Ports", "iointerface"),
                    ("USB-C/Thunderbolt", "iointerface"),
                    ("HDMI/DisplayPort", "iointerface"),
                    ("Audio Jacks", "iointerface"),
                    ("Card Reader", "iointerface"),
                    ("Network Port", "iointerface"),
                    ("Wireless Connectivity", "iointerface")
                ]
            elif "音效" in query or "audio" in query.lower() or "speaker" in query.lower():
                features = [
                    ("Audio System", "audio"),
                    ("Speaker Configuration", "audio"),
                    ("Audio Quality", "audio"),
                    ("Microphone", "audio"),
                    ("Audio Codec", "audio")
                ]
            elif "鍵盤" in query or "keyboard" in query.lower():
                features = [
                    ("Keyboard Type", "keyboard"),
                    ("Backlight", "keyboard"),
                    ("Key Travel", "keyboard"),
                    ("Numpad", "keyboard"),
                    ("Function Keys", "keyboard")
                ]
            elif "觸控板" in query or "trackpad" in query.lower() or "touchpad" in query.lower():
                features = [
                    ("Touchpad Size", "trackpad"),
                    ("Touchpad Features", "trackpad"),
                    ("Gesture Support", "trackpad"),
                    ("Precision", "trackpad")
                ]
            elif "遊戲" in query or "gaming" in query.lower():
                features = [
                    ("CPU Model", "cpu"),
                    ("GPU Model", "gpu"),
                    ("GPU Memory", "gpu"),
                    ("Memory Type", "memory"),
                    ("Storage Type", "storage"),
                    ("Display Refresh Rate", "lcd"),
                    ("Thermal Design", "thermal"),
                    ("RGB Lighting", "gaming"),
                    ("Gaming Features", "gaming")
                ]
            elif "商務" in query or "辦公" in query or "business" in query.lower():
                features = [
                    ("CPU Model", "cpu"),
                    ("Memory Type", "memory"),
                    ("Storage Type", "storage"),
                    ("Battery Capacity", "battery"),
                    ("Weight", "structconfig"),
                    ("Security Features", "security"),
                    ("Business Features", "business")
                ]
            elif "創作" in query or "設計" in query or "creative" in query.lower():
                features = [
                    ("CPU Model", "cpu"),
                    ("GPU Model", "gpu"),
                    ("Display Quality", "lcd"),
                    ("Color Accuracy", "lcd"),
                    ("Memory Type", "memory"),
                    ("Storage Type", "storage"),
                    ("Pen Support", "creative")
                ]
            else:
                # 通用比较 - 擴展版本
                features = [
                    ("CPU Model", "cpu"),
                    ("CPU Cores/Threads", "cpu"),
                    ("GPU Model", "gpu"),
                    ("GPU Memory", "gpu"),
                    ("Memory Type", "memory"),
                    ("Memory Capacity", "memory"),
                    ("Storage Type", "storage"),
                    ("Storage Capacity", "storage"),
                    ("Display Size", "lcd"),
                    ("Display Resolution", "lcd"),
                    ("Battery Capacity", "battery"),
                    ("Weight", "structconfig"),
                    ("USB Ports", "iointerface"),
                    ("Thermal Design", "thermal")
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
                            elif feature_name == "CPU Cores":
                                # 提取核心数
                                cores_match = re.search(r"(\d+)\s*cores", field_data)
                                row[model_name] = f"{cores_match.group(1)} Cores" if cores_match else "N/A"
                            elif feature_name == "CPU Threads":
                                # 提取线程数
                                threads_match = re.search(r"(\d+)\s*threads", field_data)
                                row[model_name] = f"{threads_match.group(1)} Threads" if threads_match else "N/A"
                            elif feature_name == "CPU Base Speed":
                                # 提取基础频率
                                base_match = re.search(r"(\d+\.?\d*)\s*GHz", field_data)
                                row[model_name] = f"{base_match.group(1)} GHz" if base_match else "N/A"
                            elif feature_name == "CPU Boost Speed":
                                # 提取加速频率
                                boost_match = re.search(r"up to\s*(\d+\.?\d*)\s*GHz", field_data)
                                row[model_name] = f"Up to {boost_match.group(1)} GHz" if boost_match else "N/A"
                            elif feature_name == "CPU Cache":
                                # 提取缓存信息
                                cache_match = re.search(r"(\d+)\s*MB\s*cache", field_data)
                                row[model_name] = f"{cache_match.group(1)} MB Cache" if cache_match else "N/A"
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
                            elif feature_name == "GPU Architecture":
                                # 提取架构信息
                                if "RDNA" in field_data:
                                    arch_match = re.search(r"RDNA\s*(\d+)", field_data)
                                    row[model_name] = f"RDNA {arch_match.group(1)}" if arch_match else "RDNA"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "GPU Cores":
                                # 提取核心数
                                cores_match = re.search(r"(\d+)\s*cores", field_data)
                                row[model_name] = f"{cores_match.group(1)} Cores" if cores_match else "N/A"
                            elif feature_name == "GPU Boost Clock":
                                # 提取加速频率
                                boost_match = re.search(r"(\d+\.?\d*)\s*MHz", field_data)
                                row[model_name] = f"{boost_match.group(1)} MHz" if boost_match else "N/A"
                            elif feature_name == "Ray Tracing":
                                # 检查光线追踪支持
                                if "ray tracing" in field_data.lower() or "rt" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
                            elif feature_name == "DLSS/FSR Support":
                                # 检查AI升频支持
                                features = []
                                if "fsr" in field_data.lower():
                                    features.append("FSR")
                                if "dlss" in field_data.lower():
                                    features.append("DLSS")
                                row[model_name] = ", ".join(features) if features else "N/A"
                            else:
                                # 默认提取第一个GPU型号
                                gpu_match = re.search(r"AMD Radeon™\s+[A-Z0-9]+[A-Z]*", field_data)
                                row[model_name] = gpu_match.group(0) if gpu_match else "N/A"
                        elif data_field == "memory":
                            # 提取内存信息
                            if feature_name == "Memory Type":
                                memory_match = re.search(r"DDR\d+", field_data)
                                row[model_name] = memory_match.group(0) if memory_match else "N/A"
                            elif feature_name == "Memory Speed":
                                speed_match = re.search(r"DDR\d+\s*(\d+)", field_data)
                                row[model_name] = f"{speed_match.group(1)} MHz" if speed_match else "N/A"
                            elif feature_name == "Memory Capacity":
                                capacity_match = re.search(r"(\d+)\s*GB", field_data)
                                row[model_name] = f"{capacity_match.group(1)} GB" if capacity_match else "N/A"
                            elif feature_name == "Memory Channels":
                                if "dual" in field_data.lower():
                                    row[model_name] = "Dual"
                                elif "single" in field_data.lower():
                                    row[model_name] = "Single"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Memory Slots":
                                slots_match = re.search(r"(\d+)\s*slots", field_data)
                                row[model_name] = f"{slots_match.group(1)} Slots" if slots_match else "N/A"
                            elif feature_name == "Max Memory":
                                max_match = re.search(r"up to\s*(\d+)\s*GB", field_data)
                                row[model_name] = f"Up to {max_match.group(1)} GB" if max_match else "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "storage":
                            # 提取存储信息
                            if feature_name == "Storage Type":
                                if "nvme" in field_data.lower():
                                    row[model_name] = "NVMe SSD"
                                elif "ssd" in field_data.lower():
                                    row[model_name] = "SSD"
                                elif "hdd" in field_data.lower():
                                    row[model_name] = "HDD"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Storage Capacity":
                                capacity_match = re.search(r"(\d+)\s*GB", field_data)
                                if capacity_match:
                                    capacity = int(capacity_match.group(1))
                                    if capacity >= 1024:
                                        row[model_name] = f"{capacity/1024:.0f} TB"
                                    else:
                                        row[model_name] = f"{capacity} GB"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Storage Speed":
                                speed_match = re.search(r"(\d+)\s*MB/s", field_data)
                                row[model_name] = f"{speed_match.group(1)} MB/s" if speed_match else "N/A"
                            elif feature_name == "Storage Slots":
                                slots_match = re.search(r"(\d+)\s*slots", field_data)
                                row[model_name] = f"{slots_match.group(1)} Slots" if slots_match else "N/A"
                            elif feature_name == "Secondary Storage":
                                if "hdd" in field_data.lower():
                                    row[model_name] = "HDD"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Storage Interface":
                                if "pcie" in field_data.lower():
                                    row[model_name] = "PCIe"
                                elif "sata" in field_data.lower():
                                    row[model_name] = "SATA"
                                else:
                                    row[model_name] = "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "battery":
                            # 提取电池信息
                            if feature_name == "Battery Capacity":
                                battery_match = re.search(r"(\d+\.?\d*)\s*Wh", field_data)
                                row[model_name] = f"{battery_match.group(1)}Wh" if battery_match else "N/A"
                            elif feature_name == "Battery Life":
                                life_match = re.search(r"(\d+\.?\d*)\s*hours", field_data)
                                row[model_name] = f"{life_match.group(1)} hours" if life_match else "N/A"
                            elif feature_name == "Charging Speed":
                                if "fast" in field_data.lower():
                                    row[model_name] = "Fast Charging"
                                else:
                                    row[model_name] = "Standard"
                            elif feature_name == "Power Adapter":
                                adapter_match = re.search(r"(\d+)\s*W", field_data)
                                row[model_name] = f"{adapter_match.group(1)}W" if adapter_match else "N/A"
                            elif feature_name == "Fast Charging":
                                if "fast" in field_data.lower() or "quick" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "lcd":
                            # 提取屏幕信息
                            if feature_name == "Display Size":
                                size_match = re.search(r"(\d+\.?\d*)\s*inch", field_data)
                                row[model_name] = f"{size_match.group(1)}\"" if size_match else "N/A"
                            elif feature_name == "Resolution":
                                if "FHD" in field_data or "1920×1080" in field_data:
                                    row[model_name] = "FHD 1920×1080"
                                elif "QHD" in field_data or "2560×1440" in field_data:
                                    row[model_name] = "QHD 2560×1440"
                                elif "4K" in field_data or "3840×2160" in field_data:
                                    row[model_name] = "4K 3840×2160"
                                else:
                                    res_match = re.search(r"(\d+×\d+)", field_data)
                                    row[model_name] = res_match.group(1) if res_match else "N/A"
                            elif feature_name == "Refresh Rate":
                                refresh_match = re.search(r"(\d+)\s*Hz", field_data)
                                row[model_name] = f"{refresh_match.group(1)}Hz" if refresh_match else "N/A"
                            elif feature_name == "Panel Type":
                                if "IPS" in field_data:
                                    row[model_name] = "IPS"
                                elif "VA" in field_data:
                                    row[model_name] = "VA"
                                elif "TN" in field_data:
                                    row[model_name] = "TN"
                                elif "OLED" in field_data:
                                    row[model_name] = "OLED"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Color Gamut":
                                if "sRGB" in field_data:
                                    row[model_name] = "sRGB"
                                elif "Adobe RGB" in field_data:
                                    row[model_name] = "Adobe RGB"
                                elif "DCI-P3" in field_data:
                                    row[model_name] = "DCI-P3"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Brightness":
                                brightness_match = re.search(r"(\d+)\s*nits", field_data)
                                row[model_name] = f"{brightness_match.group(1)} nits" if brightness_match else "N/A"
                            elif feature_name == "Touch Support":
                                if "touch" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "structconfig":
                            # 提取結構配置信息
                            if feature_name == "Weight":
                                weight_match = re.search(r"Weight:\s*(\d+)\s*g", field_data)
                                if weight_match:
                                    weight_g = int(weight_match.group(1))
                                    row[model_name] = f"{weight_g}g ({weight_g/1000:.1f}kg)"
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
                            elif feature_name == "Thickness":
                                thickness_match = re.search(r"(\d+\.?\d*)\s*mm", field_data)
                                row[model_name] = f"{thickness_match.group(1)}mm" if thickness_match else "N/A"
                            elif feature_name == "Build Quality":
                                if "aluminum" in field_data.lower() or "metal" in field_data.lower():
                                    row[model_name] = "Metal"
                                elif "plastic" in field_data.lower():
                                    row[model_name] = "Plastic"
                                else:
                                    row[model_name] = "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "thermal":
                            # 提取散熱信息
                            if feature_name == "Thermal Design":
                                thermal_match = re.search(r"(\d+)W", field_data)
                                row[model_name] = f"{thermal_match.group(1)}W" if thermal_match else "N/A"
                            elif feature_name == "Cooling System":
                                if "dual" in field_data.lower() and "fan" in field_data.lower():
                                    row[model_name] = "Dual Fan"
                                elif "fan" in field_data.lower():
                                    row[model_name] = "Single Fan"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Fan Configuration":
                                if "dual" in field_data.lower():
                                    row[model_name] = "Dual"
                                else:
                                    row[model_name] = "Single"
                            elif feature_name == "Thermal Performance":
                                if "excellent" in field_data.lower():
                                    row[model_name] = "Excellent"
                                elif "good" in field_data.lower():
                                    row[model_name] = "Good"
                                elif "average" in field_data.lower():
                                    row[model_name] = "Average"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Noise Level":
                                if "quiet" in field_data.lower():
                                    row[model_name] = "Quiet"
                                elif "moderate" in field_data.lower():
                                    row[model_name] = "Moderate"
                                else:
                                    row[model_name] = "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "iointerface":
                            # 提取接口信息
                            if feature_name == "USB Ports":
                                usb_match = re.search(r"(\d+)\s*USB", field_data)
                                row[model_name] = f"{usb_match.group(1)} USB" if usb_match else "N/A"
                            elif feature_name == "USB-C/Thunderbolt":
                                if "thunderbolt" in field_data.lower():
                                    row[model_name] = "Thunderbolt"
                                elif "usb-c" in field_data.lower():
                                    row[model_name] = "USB-C"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "HDMI/DisplayPort":
                                if "hdmi" in field_data.lower():
                                    row[model_name] = "HDMI"
                                elif "displayport" in field_data.lower():
                                    row[model_name] = "DisplayPort"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Audio Jacks":
                                audio_match = re.search(r"(\d+)\s*audio", field_data)
                                row[model_name] = f"{audio_match.group(1)} Audio" if audio_match else "N/A"
                            elif feature_name == "Card Reader":
                                if "card" in field_data.lower() and "reader" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
                            elif feature_name == "Network Port":
                                if "ethernet" in field_data.lower() or "lan" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
                            elif feature_name == "Wireless Connectivity":
                                if "wifi" in field_data.lower() and "bluetooth" in field_data.lower():
                                    row[model_name] = "WiFi + Bluetooth"
                                elif "wifi" in field_data.lower():
                                    row[model_name] = "WiFi"
                                else:
                                    row[model_name] = "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "audio":
                            # 提取音效信息
                            if feature_name == "Audio System":
                                if "harman" in field_data.lower():
                                    row[model_name] = "Harman Kardon"
                                elif "bang" in field_data.lower() and "olufsen" in field_data.lower():
                                    row[model_name] = "Bang & Olufsen"
                                else:
                                    row[model_name] = "Standard"
                            elif feature_name == "Speaker Configuration":
                                if "dual" in field_data.lower() and "speaker" in field_data.lower():
                                    row[model_name] = "Dual Speakers"
                                elif "quad" in field_data.lower():
                                    row[model_name] = "Quad Speakers"
                                else:
                                    row[model_name] = "Standard"
                            elif feature_name == "Audio Quality":
                                if "premium" in field_data.lower():
                                    row[model_name] = "Premium"
                                elif "high" in field_data.lower():
                                    row[model_name] = "High"
                                else:
                                    row[model_name] = "Standard"
                            elif feature_name == "Microphone":
                                if "array" in field_data.lower():
                                    row[model_name] = "Array Microphone"
                                else:
                                    row[model_name] = "Standard"
                            elif feature_name == "Audio Codec":
                                if "realtek" in field_data.lower():
                                    row[model_name] = "Realtek"
                                else:
                                    row[model_name] = "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "keyboard":
                            # 提取鍵盤信息
                            if feature_name == "Keyboard Type":
                                if "mechanical" in field_data.lower():
                                    row[model_name] = "Mechanical"
                                else:
                                    row[model_name] = "Membrane"
                            elif feature_name == "Backlight":
                                if "rgb" in field_data.lower():
                                    row[model_name] = "RGB"
                                elif "backlight" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
                            elif feature_name == "Key Travel":
                                travel_match = re.search(r"(\d+\.?\d*)\s*mm", field_data)
                                row[model_name] = f"{travel_match.group(1)}mm" if travel_match else "N/A"
                            elif feature_name == "Numpad":
                                if "numpad" in field_data.lower() or "number pad" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
                            elif feature_name == "Function Keys":
                                if "function" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "trackpad":
                            # 提取觸控板信息
                            if feature_name == "Touchpad Size":
                                size_match = re.search(r"(\d+\.?\d*)\s*inch", field_data)
                                row[model_name] = f"{size_match.group(1)}\"" if size_match else "N/A"
                            elif feature_name == "Touchpad Features":
                                if "precision" in field_data.lower():
                                    row[model_name] = "Precision"
                                else:
                                    row[model_name] = "Standard"
                            elif feature_name == "Gesture Support":
                                if "gesture" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "N/A"
                            elif feature_name == "Precision":
                                if "precision" in field_data.lower():
                                    row[model_name] = "High"
                                else:
                                    row[model_name] = "Standard"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "gaming":
                            # 提取遊戲特性
                            if feature_name == "RGB Lighting":
                                if "rgb" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
                            elif feature_name == "Gaming Features":
                                features = []
                                if "g-sync" in field_data.lower():
                                    features.append("G-Sync")
                                if "freesync" in field_data.lower():
                                    features.append("FreeSync")
                                if "game mode" in field_data.lower():
                                    features.append("Game Mode")
                                row[model_name] = ", ".join(features) if features else "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "security":
                            # 提取安全特性
                            if feature_name == "Security Features":
                                features = []
                                if "fingerprint" in field_data.lower():
                                    features.append("Fingerprint")
                                if "face" in field_data.lower() and "recognition" in field_data.lower():
                                    features.append("Face Recognition")
                                if "tpm" in field_data.lower():
                                    features.append("TPM")
                                row[model_name] = ", ".join(features) if features else "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "business":
                            # 提取商務特性
                            if feature_name == "Business Features":
                                features = []
                                if "vpro" in field_data.lower():
                                    features.append("vPro")
                                if "docking" in field_data.lower():
                                    features.append("Docking")
                                if "management" in field_data.lower():
                                    features.append("Management")
                                row[model_name] = ", ".join(features) if features else "N/A"
                            else:
                                row[model_name] = "N/A"
                        elif data_field == "creative":
                            # 提取創作特性
                            if feature_name == "Pen Support":
                                if "pen" in field_data.lower() or "stylus" in field_data.lower():
                                    row[model_name] = "Yes"
                                else:
                                    row[model_name] = "No"
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

    def _generate_smart_clarification_questions(self, query: str, query_intent: dict) -> list:
        """
        根據用戶查詢智能生成具體問題
        分析用戶意圖，生成針對性的問題而不是要求重新輸入
        """
        try:
            questions = []
            query_lower = query.lower()
            
            # 分析用戶查詢中的關鍵詞
            detected_intents = query_intent.get("intents", [])
            entities = query_intent.get("entities", [])
            
            # 1. 如果檢測到比較意圖但沒有具體型號
            if "comparison" in [intent.get("name") for intent in detected_intents]:
                if not query_intent.get("modelnames") and not query_intent.get("modeltypes"):
                    questions.append({
                        "id": "comparison_scope",
                        "question": "您想要比較哪些筆電？",
                        "type": "choice",
                        "options": [
                            {"id": "series", "label": "比較同系列筆電（如 819 系列、958 系列）"},
                            {"id": "specific", "label": "比較特定型號（請告訴我型號名稱）"},
                            {"id": "recommend", "label": "請推薦適合的筆電讓我比較"}
                        ]
                    })
            
            # 2. 如果檢測到使用場景相關意圖
            usage_keywords = ["遊戲", "電競", "辦公", "商務", "學習", "創作", "設計", "工作"]
            detected_usage = [word for word in usage_keywords if word in query_lower]
            
            if detected_usage:
                questions.append({
                    "id": "usage_scenario",
                    "question": f"您主要用於{detected_usage[0]}嗎？",
                    "type": "choice",
                    "options": [
                        {"id": "gaming", "label": "🎮 遊戲娛樂"},
                        {"id": "business", "label": "💼 商務辦公"},
                        {"id": "creation", "label": "🎨 設計創作"},
                        {"id": "study", "label": "📚 學習研究"}
                    ]
                })
            
            # 3. 如果檢測到性能相關意圖
            performance_keywords = ["性能", "速度", "快", "慢", "效能"]
            if any(word in query_lower for word in performance_keywords):
                questions.append({
                    "id": "performance_priority",
                    "question": "您最重視哪方面的性能？",
                    "type": "choice",
                    "options": [
                        {"id": "cpu", "label": "💻 處理器性能"},
                        {"id": "gpu", "label": "🎮 顯卡性能"},
                        {"id": "battery", "label": "🔋 續航能力"},
                        {"id": "memory", "label": "💾 記憶體容量"}
                    ]
                })
            
            # 4. 如果檢測到便攜性相關意圖
            portability_keywords = ["輕便", "重量", "攜帶", "便攜", "輕薄"]
            if any(word in query_lower for word in portability_keywords):
                questions.append({
                    "id": "portability_priority",
                    "question": "您對筆電的重量有什麼要求？",
                    "type": "choice",
                    "options": [
                        {"id": "ultralight", "label": "超輕薄（1.5kg 以下）"},
                        {"id": "light", "label": "輕便（1.5-2kg）"},
                        {"id": "standard", "label": "標準重量（2kg 以上）"}
                    ]
                })
            
            # 5. 如果檢測到預算相關意圖
            budget_keywords = ["便宜", "貴", "價格", "預算", "價錢"]
            if any(word in query_lower for word in budget_keywords):
                questions.append({
                    "id": "budget_range",
                    "question": "您的預算範圍大概是多少？",
                    "type": "choice",
                    "options": [
                        {"id": "economy", "label": "經濟型（預算有限）"},
                        {"id": "mid_range", "label": "中階（適中預算）"},
                        {"id": "premium", "label": "高階（預算充足）"}
                    ]
                })
            
            # 6. 如果沒有檢測到具體意圖，提供通用問題
            if not questions:
                questions.append({
                    "id": "general_purpose",
                    "question": "您主要用這台筆電做什麼？",
                    "type": "choice",
                    "options": [
                        {"id": "gaming", "label": "🎮 玩遊戲"},
                        {"id": "work", "label": "💼 工作辦公"},
                        {"id": "study", "label": "📚 學習上網"},
                        {"id": "creation", "label": "🎨 設計創作"}
                    ]
                })
            
            logging.info(f"為查詢 '{query}' 生成了 {len(questions)} 個智能問題")
            return questions
            
        except Exception as e:
            logging.error(f"生成智能澄清問題時發生錯誤: {e}")
            return []

    def _generate_user_friendly_help(self, query: str) -> str:
        """
        生成友善的幫助信息，不使用專業術語
        """
        try:
            query_lower = query.lower()
            
            # 分析查詢中的關鍵詞
            if any(word in query_lower for word in ["比較", "比較", "compare", "差異", "差异"]):
                return """我理解您想要比較筆電，讓我幫您找到最適合的選擇。

您可以這樣問我：
• "哪一款筆電比較省電？"
• "哪一款筆電比較適合玩遊戲？"
• "這二種筆電的主要差異在哪些部分？"
• "請推薦適合辦公的筆電"
• "比較 819 系列和 958 系列的差異"

或者告訴我您的使用需求，我會為您推薦最適合的筆電！"""

            elif any(word in query_lower for word in ["推薦", "建議", "推薦", "建議"]):
                return """我來幫您推薦最適合的筆電！

請告訴我：
• 您主要用這台筆電做什麼？（遊戲、工作、學習、設計）
• 您最重視什麼？（性能、續航、輕便、價格）
• 您的預算大概是多少？

這樣我就能為您找到最適合的選擇！"""

            elif any(word in query_lower for word in ["遊戲", "電競", "gaming"]):
                return """您想要遊戲筆電！讓我為您推薦最適合的選擇。

遊戲筆電主要看：
• 顯卡性能（影響遊戲流暢度）
• 處理器性能（影響遊戲速度）
• 螢幕品質（影響遊戲體驗）

您可以問我：
• "哪一款筆電比較適合玩遊戲？"
• "比較 958 系列的遊戲性能"
• "推薦高性價比的遊戲筆電"

或者告訴我您玩什麼類型的遊戲，我會為您推薦！"""

            elif any(word in query_lower for word in ["辦公", "工作", "商務", "business"]):
                return """您需要辦公筆電！讓我為您推薦最適合的選擇。

辦公筆電主要看：
• 續航能力（影響工作時間）
• 處理器性能（影響工作效率）
• 輕便程度（影響攜帶便利性）

您可以問我：
• "哪一款筆電比較適合辦公？"
• "推薦續航能力強的筆電"
• "比較 819 系列的辦公性能"

或者告訴我您的具體工作需求，我會為您推薦！"""

            else:
                return """我來幫您找到最適合的筆電！

您可以這樣問我：
• "哪一款筆電比較省電？"
• "哪一款筆電比較適合玩遊戲？"
• "推薦適合辦公的筆電"
• "比較 819 系列和 958 系列的差異"
• "這二種筆電的主要差異在哪些部分？"

或者直接告訴我您的使用需求，我會為您推薦最適合的選擇！"""

        except Exception as e:
            logging.error(f"生成友善幫助信息時發生錯誤: {e}")
            return "我來幫您找到最適合的筆電！請告訴我您的使用需求。"

    async def process_smart_clarification_response(self, original_query: str, question_id: str, user_choice: str, user_input: str = ""):
        """
        處理智能澄清回應
        
        Args:
            original_query: 原始查詢
            question_id: 問題ID
            user_choice: 用戶選擇
            user_input: 用戶額外輸入
            
        Returns:
            處理結果
        """
        try:
            logging.info(f"處理智能澄清回應: question_id={question_id}, choice={user_choice}")
            
            # 根據問題ID和用戶選擇重新構建查詢意圖
            enhanced_query_intent = self._build_query_intent_from_smart_clarification(
                original_query, question_id, user_choice, user_input
            )
            
            # 執行增強的查詢
            return await self._execute_enhanced_query(enhanced_query_intent, f"根據您的選擇：{user_choice}")
            
        except Exception as e:
            logging.error(f"處理智能澄清回應時發生錯誤: {e}")
            return {
                "message_type": "error",
                "answer_summary": f"處理澄清回應時發生錯誤: {str(e)}",
                "comparison_table": []
            }

    def _build_query_intent_from_smart_clarification(self, original_query: str, question_id: str, user_choice: str, user_input: str) -> dict:
        """
        根據智能澄清回應構建查詢意圖
        """
        try:
            # 基礎查詢意圖
            query_intent = {
                "modelnames": [],
                "modeltypes": [],
                "intents": [],
                "primary_intent": "general",
                "query_type": "unknown",
                "confidence_score": 0.8,
                "smart_clarification_enhanced": True,
                "original_query": original_query,
                "clarification_context": {
                    "question_id": question_id,
                    "user_choice": user_choice,
                    "user_input": user_input
                }
            }
            
            # 根據問題ID和用戶選擇調整查詢意圖
            if question_id == "comparison_scope":
                if user_choice == "series":
                    # 用戶想要比較系列，提供系列選項
                    query_intent["query_type"] = "model_type"
                    query_intent["modeltypes"] = ["819", "839", "958"]
                    query_intent["primary_intent"] = "comparison"
                elif user_choice == "specific":
                    # 用戶想要比較特定型號，但沒有提供型號名稱
                    query_intent["query_type"] = "unknown"
                    query_intent["primary_intent"] = "comparison"
                elif user_choice == "recommend":
                    # 用戶想要推薦
                    query_intent["primary_intent"] = "recommendation"
                    
            elif question_id == "usage_scenario":
                # 根據使用場景映射到相應的系列和意圖
                scenario_mapping = {
                    "gaming": {"modeltypes": ["958"], "intents": ["gpu", "cpu"], "primary_intent": "gaming"},
                    "business": {"modeltypes": ["819"], "intents": ["battery", "cpu"], "primary_intent": "business"},
                    "creation": {"modeltypes": ["958"], "intents": ["gpu", "cpu", "memory"], "primary_intent": "creation"},
                    "study": {"modeltypes": ["839"], "intents": ["battery", "cpu"], "primary_intent": "study"}
                }
                
                if user_choice in scenario_mapping:
                    mapping = scenario_mapping[user_choice]
                    query_intent["modeltypes"] = mapping["modeltypes"]
                    query_intent["intents"] = mapping["intents"]
                    query_intent["primary_intent"] = mapping["primary_intent"]
                    query_intent["query_type"] = "model_type"
                    
            elif question_id == "performance_priority":
                # 根據性能優先級調整意圖
                performance_mapping = {
                    "cpu": {"intents": ["cpu"], "primary_intent": "cpu"},
                    "gpu": {"intents": ["gpu"], "primary_intent": "gpu"},
                    "battery": {"intents": ["battery"], "primary_intent": "battery"},
                    "memory": {"intents": ["memory"], "primary_intent": "memory"}
                }
                
                if user_choice in performance_mapping:
                    mapping = performance_mapping[user_choice]
                    query_intent["intents"] = mapping["intents"]
                    query_intent["primary_intent"] = mapping["primary_intent"]
                    # 如果沒有指定系列，使用所有系列
                    if not query_intent["modeltypes"]:
                        query_intent["modeltypes"] = ["819", "839", "958"]
                        query_intent["query_type"] = "model_type"
                        
            elif question_id == "portability_priority":
                # 根據便攜性需求調整意圖
                portability_mapping = {
                    "ultralight": {"intents": ["portability"], "primary_intent": "portability"},
                    "light": {"intents": ["portability"], "primary_intent": "portability"},
                    "standard": {"intents": ["portability"], "primary_intent": "portability"}
                }
                
                if user_choice in portability_mapping:
                    mapping = portability_mapping[user_choice]
                    query_intent["intents"] = mapping["intents"]
                    query_intent["primary_intent"] = mapping["primary_intent"]
                    # 如果沒有指定系列，使用所有系列
                    if not query_intent["modeltypes"]:
                        query_intent["modeltypes"] = ["819", "839", "958"]
                        query_intent["query_type"] = "model_type"
                        
            elif question_id == "budget_range":
                # 根據預算範圍調整意圖
                budget_mapping = {
                    "economy": {"modeltypes": ["839"], "intents": ["budget"], "primary_intent": "budget"},
                    "mid_range": {"modeltypes": ["819"], "intents": ["budget"], "primary_intent": "budget"},
                    "premium": {"modeltypes": ["958"], "intents": ["budget"], "primary_intent": "budget"}
                }
                
                if user_choice in budget_mapping:
                    mapping = budget_mapping[user_choice]
                    query_intent["modeltypes"] = mapping["modeltypes"]
                    query_intent["intents"] = mapping["intents"]
                    query_intent["primary_intent"] = mapping["primary_intent"]
                    query_intent["query_type"] = "model_type"
                    
            elif question_id == "general_purpose":
                # 通用目的問題
                purpose_mapping = {
                    "gaming": {"modeltypes": ["958"], "intents": ["gpu", "cpu"], "primary_intent": "gaming"},
                    "work": {"modeltypes": ["819"], "intents": ["battery", "cpu"], "primary_intent": "business"},
                    "study": {"modeltypes": ["839"], "intents": ["battery", "cpu"], "primary_intent": "study"},
                    "creation": {"modeltypes": ["958"], "intents": ["gpu", "cpu", "memory"], "primary_intent": "creation"}
                }
                
                if user_choice in purpose_mapping:
                    mapping = purpose_mapping[user_choice]
                    query_intent["modeltypes"] = mapping["modeltypes"]
                    query_intent["intents"] = mapping["intents"]
                    query_intent["primary_intent"] = mapping["primary_intent"]
                    query_intent["query_type"] = "model_type"
            
            # 為了向後兼容，設置 intent 欄位
            query_intent["intent"] = query_intent["primary_intent"]
            
            logging.info(f"根據智能澄清構建查詢意圖: {query_intent}")
            return query_intent
            
        except Exception as e:
            logging.error(f"構建智能澄清查詢意圖時發生錯誤: {e}")
            return {
                "modelnames": [],
                "modeltypes": ["839"],  # 預設中階系列
                "intents": [],
                "primary_intent": "general",
                "intent": "general",
                "query_type": "model_type",
                "confidence_score": 0.5,
                "smart_clarification_enhanced": True
            }

    async def process_multichat_response(self, session_id: str, user_choice: str, user_input: str = ""):
        """
        處理多輪對話回應
        
        Args:
            session_id: 會話ID
            user_choice: 使用者選擇的選項編號或ID
            user_input: 使用者額外輸入
            
        Returns:
            處理結果
        """
        try:
            logging.info(f"處理多輪對話回應: session_id={session_id}, choice={user_choice}")
            
            # 獲取會話狀態
            session = self.multichat_manager.get_session_state(session_id)
            if not session:
                return {
                    "message_type": "error",
                    "content": self.chat_template_manager.format_error_message("session_timeout")
                }
            
            # 獲取當前問題和選項
            current_feature_id = session.chat_chain.features_order[session.current_step]
            current_feature = self.multichat_manager.nb_features[current_feature_id]
            
            # 將數字選擇轉換為選項ID
            actual_choice = user_choice
            if user_choice.isdigit():
                try:
                    choice_index = int(user_choice) - 1
                    if 0 <= choice_index < len(current_feature.options):
                        actual_choice = current_feature.options[choice_index].option_id
                    else:
                        return {
                            "message_type": "error",
                            "content": self.chat_template_manager.format_error_message("invalid_choice").format(max_options=len(current_feature.options))
                        }
                except ValueError:
                    return {
                        "message_type": "error", 
                        "content": self.chat_template_manager.format_error_message("invalid_choice").format(max_options=len(current_feature.options))
                    }
            
            # 處理使用者回應
            result = self.multichat_manager.process_feature_response(session_id, actual_choice, user_input)
            
            if result["action"] == "continue":
                # 繼續下一個問題
                next_question = result["next_question"]
                
                # 格式化回應
                selected_option = None
                for option in current_feature.options:
                    if option.option_id == actual_choice:
                        selected_option = option
                        break
                
                formatted_response = self.chat_template_manager.format_next_question_response(
                    selected_option.label if selected_option else actual_choice,
                    self.chat_template_manager.format_question(
                        next_question,
                        result["current_step"],
                        result["total_steps"]
                    )
                )
                
                return {
                    "message_type": "multichat_continue",
                    "session_id": session_id,
                    "content": formatted_response,
                    "progress": result["progress"]
                }
                
            elif result["action"] == "complete":
                # 多輪對話完成，執行查詢
                preferences_summary = result["collected_preferences"]
                db_filters = result["db_filters"]
                enhanced_query = result["enhanced_query"]
                
                # 格式化完成訊息
                completion_message = self.chat_template_manager.format_session_complete(preferences_summary)
                
                # 構建查詢意圖用於資料檢索
                query_intent = self._build_query_intent_from_multichat(result)
                
                # 執行查詢並返回結果
                query_result = await self._execute_multichat_query(query_intent, preferences_summary, enhanced_query)
                
                return {
                    "message_type": "multichat_complete",
                    "session_id": session_id,
                    "completion_message": completion_message,
                    "query_result": query_result
                }
            
            else:
                raise ValueError(f"未知的多輪對話動作: {result['action']}")
                
        except Exception as e:
            logging.error(f"處理多輪對話回應時發生錯誤: {e}")
            return {
                "message_type": "error",
                "content": self.chat_template_manager.format_error_message("general")
            }

    def _build_query_intent_from_multichat(self, multichat_result: dict) -> dict:
        """
        從多輪對話結果構建查詢意圖
        
        Args:
            multichat_result: 多輪對話完成結果
            
        Returns:
            查詢意圖字典
        """
        try:
            preferences = multichat_result.get("collected_preferences", {})
            db_filters = multichat_result.get("db_filters", {})
            
            # 基於收集的偏好構建查詢意圖
            query_intent = {
                "modelnames": [],
                "modeltypes": ["819", "839", "958"],  # 預設所有系列
                "intents": [],
                "primary_intent": "multichat_guided",
                "intent": "multichat_guided",
                "query_type": "model_type",
                "confidence_score": 0.95,
                "multichat_enhanced": True,
                "collected_preferences": preferences,
                "db_filters": db_filters
            }
            
            # 根據GPU偏好調整系列
            if "gpu" in preferences:
                gpu_pref = preferences["gpu"]["selected_option"]
                if "遊戲級" in gpu_pref or "創作級" in gpu_pref:
                    query_intent["modeltypes"] = ["958"]  # 高性能系列
                elif "內建顯卡" in gpu_pref:
                    query_intent["modeltypes"] = ["819", "839"]  # 節能系列
            
            # 根據價格偏好調整系列
            if "price" in preferences:
                price_pref = preferences["price"]["selected_option"]
                if "經濟型" in price_pref:
                    query_intent["modeltypes"] = ["839"]
                elif "高階型" in price_pref or "旗艦型" in price_pref:
                    query_intent["modeltypes"] = ["958"]
                elif "中階型" in price_pref:
                    query_intent["modeltypes"] = ["819", "839"]
            
            # 設定優先規格
            priority_specs = []
            for feature_id, pref_data in preferences.items():
                if pref_data["selected_option"] not in ["沒有偏好", "沒有特殊需求", "彈性選擇"]:
                    priority_specs.append(feature_id)
            
            query_intent["intents"] = priority_specs
            
            logging.info(f"從多輪對話構建查詢意圖: {query_intent}")
            return query_intent
            
        except Exception as e:
            logging.error(f"構建多輪對話查詢意圖失敗: {e}")
            return {
                "modelnames": [],
                "modeltypes": ["839"],
                "intents": [],
                "primary_intent": "general",
                "intent": "general", 
                "query_type": "model_type",
                "confidence_score": 0.5,
                "multichat_enhanced": True
            }

    async def _execute_multichat_query(self, query_intent: dict, preferences_summary: dict, enhanced_query: str):
        """
        執行多輪對話引導的查詢
        
        Args:
            query_intent: 查詢意圖
            preferences_summary: 偏好總結
            enhanced_query: 增強查詢字串
            
        Returns:
            查詢結果
        """
        try:
            # 獲取資料
            context_list_of_dicts, target_modelnames = self._get_data_by_query_type(query_intent)
            
            # 構建包含偏好的上下文
            multichat_context = {
                "data": context_list_of_dicts,
                "query_intent": query_intent,
                "target_modelnames": target_modelnames,
                "user_preferences": preferences_summary,
                "guided_query": enhanced_query
            }
            
            context_str = json.dumps(multichat_context, indent=2, ensure_ascii=False)
            
            # 構建專用的多輪對話提示
            preferences_text = ""
            for feature_id, pref_data in preferences_summary.items():
                if pref_data["selected_option"] not in ["沒有偏好", "沒有特殊需求", "彈性選擇"]:
                    preferences_text += f"- {pref_data['feature_name']}: {pref_data['selected_option']}\n"
            
            multichat_prompt = f"""
根據用戶通過多輪對話明確表達的需求偏好：

{preferences_text}

請基於以下資訊提供精準的筆電推薦：
- 所有偏好都已通過系統性問答收集
- 推薦應嚴格符合用戶明確表達的偏好
- 重點突出符合用戶偏好的機型特色
- 如有多個符合條件的機型，請按匹配度排序

{self.prompt_template}
"""
            
            final_prompt = multichat_prompt.replace("{context}", context_str).replace("{query}", enhanced_query)
            
            # 調用LLM
            response_str = self.llm_initializer.invoke(final_prompt)
            
            # 解析回應
            think_end = response_str.find("</think>")
            if think_end != -1:
                cleaned_response_str = response_str[think_end + 8:].strip()
            else:
                cleaned_response_str = response_str
            
            json_start = cleaned_response_str.find("{")
            json_end = cleaned_response_str.rfind("}")
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_content = cleaned_response_str[json_start:json_end+1]
                try:
                    parsed_response = json.loads(json_content)
                    
                    # 加入多輪對話標記
                    parsed_response["multichat_guided"] = True
                    parsed_response["user_preferences"] = preferences_summary
                    
                    return parsed_response
                    
                except json.JSONDecodeError as e:
                    logging.error(f"JSON解析失敗: {e}")
                    return {
                        "answer_summary": cleaned_response_str,
                        "comparison_table": [],
                        "multichat_guided": True,
                        "user_preferences": preferences_summary
                    }
            else:
                return {
                    "answer_summary": cleaned_response_str,
                    "comparison_table": [],
                    "multichat_guided": True,
                    "user_preferences": preferences_summary
                }
                
        except Exception as e:
            logging.error(f"執行多輪對話查詢失敗: {e}")
            return {
                "answer_summary": f"執行查詢時發生錯誤: {str(e)}",
                "comparison_table": [],
                "multichat_guided": True,
                "user_preferences": preferences_summary
            }