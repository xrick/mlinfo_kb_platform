from typing import Optional


class Language:
    EN_US = "en-US"
    ZH_TW = "zh-TW"
    ZH_CN = "zh-CN"


def normalize_language(code_or_name: Optional[str]) -> Optional[str]:
    if not code_or_name:
        return None
    v = code_or_name.strip()
    v_lower = v.lower()
    # Common aliases
    if v_lower in {"en", "en-us", "english"}:
        return Language.EN_US
    if v_lower in {"zh-tw", "zh_hant", "traditional chinese", "繁體中文", "繁中", "zh-hant"}:
        return Language.ZH_TW
    if v_lower in {"zh-cn", "zh_hans", "simplified chinese", "简体中文", "簡中", "zh-hans"}:
        return Language.ZH_CN
    # Already normalized codes
    if v in {Language.EN_US, Language.ZH_TW, Language.ZH_CN}:
        return v
    return None


def build_language_instruction(language: str) -> str:
    lang = normalize_language(language) or Language.EN_US
    if lang == Language.ZH_TW:
        return "請以繁體中文回答。"
    if lang == Language.ZH_CN:
        return "请使用简体中文回答。"
    return "Please respond in English."


def mirror_instruction() -> str:
    return (
        "You MUST mirror the user's language: "
        "If user's message is in English, reply in English; "
        "if in Traditional Chinese, reply in Traditional Chinese; "
        "if in Simplified Chinese, reply in Simplified Chinese."
    )


def resolve_language(
    user_text_language: Optional[str],
    detected_from_query_rule: Optional[str],
    ui_language: Optional[str],
    system_default: str,
) -> str:
    """
    Decide final language per priority:
    1) Mirror user language (if determinable)
    2) System default language
    3) UI selected language (last fallback)
    """
    # 1) Mirror user language (prefer query_rule's language if present)
    for candidate in (detected_from_query_rule, user_text_language):
        norm = normalize_language(candidate)
        if norm:
            return norm

    # 2) System default
    norm_default = normalize_language(system_default)
    if norm_default:
        return norm_default

    # 3) UI selected language
    norm_ui = normalize_language(ui_language)
    if norm_ui:
        return norm_ui

    # Safety fallback
    return Language.EN_US


