"""
PromptManageHandler - MGFD 提示工程整合模組

提供完整的提示管理功能：
1. PromptManagementHandler - 主要提示管理器
2. PromptRegistry - 提示註冊中心
3. PromptSelector - 智能提示選擇器
4. PromptRenderer - 安全提示渲染器

基於 MGFD 系統設計，實現：
- 統一的提示管理接口
- 智能提示選擇機制
- 安全的模板渲染
- 與狀態機深度整合
- 高性能緩存和監控
"""

# 導入核心類別
from .PromptManagementHandler import PromptManagementHandler
from .PromptRegistry import (
    PromptRegistry,
    PromptMetadata,
    PromptRegistryError
)
from .PromptSelector import (
    PromptSelector,
    SelectionCriteria,
    SelectionResult,
    SelectionStrategy
)
from .PromptRenderer import (
    PromptRenderer,
    RenderContext,
    RenderResult,
    PromptRendererError
)

# 版本信息
__version__ = "2.0.0"
__author__ = "MGFD Development Team"

# 導出的主要類別和函數
__all__ = [
    # 核心組件
    "PromptManagementHandler",
    "PromptRegistry",
    "PromptSelector", 
    "PromptRenderer",
    
    # 數據結構
    "PromptMetadata",
    "SelectionCriteria",
    "SelectionResult",
    "RenderContext",
    "RenderResult",
    
    # 枚舉
    "SelectionStrategy",
    
    # 異常類
    "PromptRegistryError",
    "PromptRendererError",
    
    # 便利函數
    "create_prompt_manager",
    "create_simple_render_context",
    "create_selection_criteria"
]

# 模組初始化日誌
import logging
logger = logging.getLogger(__name__)
logger.info(f"PromptManageHandler 模組已載入 (版本 {__version__})")

# 便利函數：創建預配置的提示管理器
async def create_prompt_manager(
    prompts_base_dir: str = None,
    enable_cache: bool = True,
    auto_reload: bool = True,
    auto_initialize: bool = True
) -> PromptManagementHandler:
    """
    創建並初始化提示管理器實例
    
    Args:
        prompts_base_dir: 提示基礎目錄
        enable_cache: 是否啟用緩存
        auto_reload: 是否自動重載
        auto_initialize: 是否自動初始化
        
    Returns:
        PromptManagementHandler 實例
    """
    try:
        manager = PromptManagementHandler(
            prompts_base_dir=prompts_base_dir,
            enable_cache=enable_cache,
            auto_reload=auto_reload
        )
        
        if auto_initialize:
            init_result = await manager.initialize()
            if not init_result["success"]:
                logger.error(f"提示管理器初始化失敗: {init_result['error']}")
                raise RuntimeError(f"初始化失敗: {init_result['error']}")
        
        return manager
        
    except Exception as e:
        logger.error(f"創建提示管理器失敗: {e}")
        raise

# 便利函數：創建簡單的渲染上下文
def create_simple_render_context(
    variables: dict = None,
    user_profile: dict = None,
    conversation_context: dict = None
) -> RenderContext:
    """
    創建簡單的渲染上下文
    
    Args:
        variables: 渲染變數
        user_profile: 用戶資料
        conversation_context: 對話上下文
        
    Returns:
        RenderContext 實例
    """
    from datetime import datetime
    
    return RenderContext(
        variables=variables or {},
        global_variables={},
        user_profile=user_profile or {},
        conversation_context=conversation_context or {},
        system_info={
            "timestamp": datetime.now().isoformat(),
            "system_version": __version__
        },
        render_options={}
    )

# 便利函數：創建選擇條件
def create_selection_criteria(
    state: str = None,
    intent: str = None,
    category: str = None,
    language: str = "zh-TW",
    **kwargs
) -> SelectionCriteria:
    """
    創建提示選擇條件
    
    Args:
        state: 對話狀態
        intent: 用戶意圖
        category: 提示分類
        language: 語言偏好
        **kwargs: 其他選擇條件
        
    Returns:
        SelectionCriteria 實例
    """
    return SelectionCriteria(
        state=state,
        intent=intent,
        category=category,
        language=language,
        context_keywords=kwargs.get('context_keywords', []),
        user_profile=kwargs.get('user_profile', {}),
        conversation_history=kwargs.get('conversation_history', []),
        exclude_prompt_ids=kwargs.get('exclude_prompt_ids', [])
    )

# 預設配置載入
def load_default_config() -> dict:
    """
    載入默認配置
    
    Returns:
        配置字典
    """
    import json
    from pathlib import Path
    
    try:
        config_dir = Path(__file__).parent / "config"
        default_settings_file = config_dir / "default_settings.json"
        
        if default_settings_file.exists():
            with open(default_settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning("默認配置文件不存在，使用內建配置")
            return {
                "system_settings": {
                    "enable_cache": True,
                    "auto_reload": True,
                    "strict_mode": False
                }
            }
            
    except Exception as e:
        logger.error(f"載入默認配置失敗: {e}")
        return {}

# 健康檢查函數
async def health_check(manager: PromptManagementHandler = None) -> dict:
    """
    執行健康檢查
    
    Args:
        manager: 提示管理器實例（可選）
        
    Returns:
        健康檢查結果
    """
    try:
        if manager:
            return await manager.health_check()
        else:
            # 創建臨時管理器進行檢查
            temp_manager = PromptManagementHandler()
            init_result = await temp_manager.initialize()
            
            return {
                "module_healthy": True,
                "initialization_test": init_result["success"],
                "error": init_result.get("error") if not init_result["success"] else None
            }
            
    except Exception as e:
        return {
            "module_healthy": False,
            "error": str(e)
        }

# 版本兼容性檢查
def check_compatibility() -> dict:
    """
    檢查模組兼容性
    
    Returns:
        兼容性檢查結果
    """
    compatibility_info = {
        "version": __version__,
        "compatible": True,
        "warnings": [],
        "requirements_met": True
    }
    
    try:
        # 檢查必要的依賴
        required_modules = [
            'asyncio', 'json', 'logging', 'pathlib',
            'datetime', 'hashlib', 're', 'typing'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            compatibility_info["compatible"] = False
            compatibility_info["requirements_met"] = False
            compatibility_info["warnings"].append(f"缺少必要模組: {missing_modules}")
        
        # 檢查 Python 版本
        import sys
        if sys.version_info < (3, 7):
            compatibility_info["compatible"] = False
            compatibility_info["warnings"].append("需要 Python 3.7 或更高版本")
        
    except Exception as e:
        compatibility_info["compatible"] = False
        compatibility_info["warnings"].append(f"兼容性檢查失敗: {str(e)}")
    
    return compatibility_info

# 模組級別的統計信息
_module_stats = {
    "loaded_at": None,
    "managers_created": 0,
    "total_requests": 0
}

def get_module_stats() -> dict:
    """獲取模組統計信息"""
    from datetime import datetime
    
    if _module_stats["loaded_at"] is None:
        _module_stats["loaded_at"] = datetime.now().isoformat()
    
    return _module_stats.copy()

# 模組清理函數
def cleanup():
    """清理模組資源"""
    logger.info("清理 PromptManageHandler 模組資源")
    # 這裡可以添加清理邏輯

# 導入時執行兼容性檢查
_compatibility_result = check_compatibility()
if not _compatibility_result["compatible"]:
    logger.warning(f"模組兼容性檢查發現問題: {_compatibility_result['warnings']}")

logger.info(f"PromptManageHandler v{__version__} 初始化完成")