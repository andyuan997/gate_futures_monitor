"""
Gate.io 期貨上市監控配置
"""


class GateFuturesConfig:
    """Gate.io 期貨上市監控配置"""

    # 監控的網頁URL
    MONITOR_URL = "https://www.gate.com/zh-tw/announcements/newfutureslistings"

    # 數據存儲配置
    DATA_DIR = "data"
    HISTORY_FILE = "futures_history.json"

    # 日誌配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    # 檢查間隔（秒）
    CHECK_INTERVAL = 300  # 5分鐘

    # Telegram 配置
    TELEGRAM_BOT_TOKEN = "8178012778:AAFat7W2vy3c2biLwUlX2FI_P7yMRDLWo6c"  # 請替換為你的bot token
    TELEGRAM_CHAT_ID = "909636319"      # 請替換為你的chat ID

    # 通知消息模板
    NOTIFICATION_TEMPLATE = """
🚀 Gate.io 新期貨上市通知

📈 新期貨: {symbol}
📅 上市時間: {listing_time}
🔗 詳情鏈接: {url}

#GateIO #期貨 #新上市
"""
