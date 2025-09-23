from pathlib import Path

import pytest

from libs.KnowledgeManageHandler.knowledge_manager import KnowledgeManager


@pytest.fixture()
def knowledge_manager():
    base_path = Path(__file__).resolve().parents[1]
    manager = KnowledgeManager(base_path=str(base_path))
    manager._validate_modeltype_exists = lambda _modeltype: True
    return manager


def test_extract_product_codes_supports_three_digit_models(knowledge_manager):
    query = "請問958的CPU與819的CPU差異？"
    detected = knowledge_manager._extract_product_codes(query)
    assert detected == ['958', '819']


def test_extract_product_codes_filters_year_like_numbers(knowledge_manager):
    query = "2025年的新款筆電有哪些？"
    detected = knowledge_manager._extract_product_codes(query)
    assert detected == []
