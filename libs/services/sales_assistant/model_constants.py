#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Constants Module

This module provides centralized access to available model names and types
from the database, avoiding circular import dependencies.

Separated from service.py to prevent import chain issues with progressive_streaming.
"""

import logging

# Global variables for available models
AVAILABLE_MODELNAMES = []
AVAILABLE_MODELTYPES = []


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
            'AMD839: FT6', 'APX819', 'APX819E', 'APX839', 'APX958',
            'APX958E', 'Chalet 728', 'Chalet 758', 'Chalet 958',
            'Gaming 728', 'Gaming 728 E', 'Gaming 958 E', 'Galaxy 728',
            'Galaxy 728 E', 'Galaxy 958 E', 'Gaming 958', 'Galaxy 958',
            'XP819', 'XP958', 'XPNB819: FP7F3', 'XPNB839: FP7F3',
            'XPNB958: FP7F3'
        ]


def _get_available_modeltypes_from_db():
    """從數據庫動態獲取可用的modeltype"""
    try:
        from config import DB_PATH
        import duckdb

        conn = duckdb.connect(str(DB_PATH))
        result = conn.execute("""
            SELECT DISTINCT modeltype
            FROM nbtypes
            WHERE modeltype IS NOT NULL
              AND modeltype != ''
            ORDER BY modeltype
        """).fetchall()
        conn.close()

        modeltypes = [row[0] for row in result]
        logging.info(f"從數據庫獲取到的modeltype: {len(modeltypes)} 個")
        return modeltypes
    except Exception as e:
        logging.error(f"獲取數據庫modeltype失敗: {e}")
        return ['819', '839', '958']


# Initialize model lists from database
AVAILABLE_MODELNAMES = _get_available_modelnames_from_db()
AVAILABLE_MODELTYPES = _get_available_modeltypes_from_db()


def get_available_modelnames():
    """Get list of available model names"""
    return AVAILABLE_MODELNAMES.copy()


def get_available_modeltypes():
    """Get list of available model types"""
    return AVAILABLE_MODELTYPES.copy()


def refresh_model_lists():
    """Refresh model lists from database"""
    global AVAILABLE_MODELNAMES, AVAILABLE_MODELTYPES
    AVAILABLE_MODELNAMES = _get_available_modelnames_from_db()
    AVAILABLE_MODELTYPES = _get_available_modeltypes_from_db()
    logging.info("Model lists refreshed from database")
