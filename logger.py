"""
日誌配置模組
用於設定 Gate.io 期貨監控的日誌系統
"""

import logging
import sys
from config import GateFuturesConfig


def setup_gate_logger(name: str) -> logging.Logger:
    """設定 Gate.io 期貨監控日誌器
    
    Args:
        name: 日誌器名稱（通常是模組名稱）
        
    Returns:
        logging.Logger: 配置好的日誌器
    """
    # 創建日誌器
    logger = logging.getLogger(name)
    
    # 如果日誌器已經配置過，直接返回
    if logger.handlers:
        return logger
    
    # 設定日誌級別
    logger.setLevel(getattr(logging, GateFuturesConfig.LOG_LEVEL.upper()))
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 創建文件處理器
    try:
        import os
        os.makedirs(GateFuturesConfig.DATA_DIR, exist_ok=True)
        log_file = os.path.join(GateFuturesConfig.DATA_DIR, "gate_futures.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
    except Exception as e:
        print(f"無法創建日誌文件: {e}")
        file_handler = None
    
    # 設定日誌格式
    formatter = logging.Formatter(GateFuturesConfig.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    if file_handler:
        file_handler.setFormatter(formatter)
    
    # 添加處理器到日誌器
    logger.addHandler(console_handler)
    if file_handler:
        logger.addHandler(file_handler)
    
    # 防止日誌重複輸出
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """獲取日誌器的便捷函數
    
    Args:
        name: 日誌器名稱
        
    Returns:
        logging.Logger: 日誌器實例
    """
    return setup_gate_logger(name)
