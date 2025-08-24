class GateFuturesConfig:
    """Gate.io 期货上市监控配置"""
    
    # 监控的网页URL
    MONITOR_URL = "https://www.gate.com/zh-tw/announcements/newfutureslistings"
    
    # 数据存储配置
    DATA_DIR = "data"
    HISTORY_FILE = "futures_history.json"
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    # 检查间隔（秒）
    CHECK_INTERVAL = 300  # 5分钟
    
    # Telegram 配置
    TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # 请替换为你的bot token
    TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"      # 请替换为你的chat ID
    
    # 通知消息模板
    NOTIFICATION_TEMPLATE = """
🚀 Gate.io 新期货上市通知

📈 新期货: {symbol}
📅 上市时间: {listing_time}
🔗 详情链接: {url}

#GateIO #期货 #新上市
"""
