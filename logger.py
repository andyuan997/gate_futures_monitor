import logging
import os
from datetime import datetime

def setup_gate_logger(name: str) -> logging.Logger:
    """设置 Gate.io 期货监控的日志记录器"""
    
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger
    
    # 创建文件处理器
    log_file = os.path.join(log_dir, f"gate_futures_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    
    # 设置格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
