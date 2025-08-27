# Gate.io 期貨上市監控器

一個獨立的 Python 程序，用於監控 [Gate.io 新期貨上市頁面](https://www.gate.com/zh-tw/announcements/newfutureslistings) 並發送 Telegram 通知。

## 功能特點

- 🚀 自動監控 Gate.io 新期貨上市
- 📱 即時 Telegram 通知
- 💾 本地歷史記錄存儲
- 🔄 可配置的檢查間隔
- 📊 詳細的日誌記錄

## 安裝依賴

```bash
cd gate_futures_monitor
pip install -r requirements.txt
playwright install chromium
```

## 配置

1. 編輯 `config.py` 文件，配置你的 Telegram 機器人：

```python
# Telegram 配置
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # 替換為你的bot token
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"      # 替換為你的chat ID
```

2. 如何獲取 Telegram Bot Token：
   - 在 Telegram 中搜尋 `@BotFather`
   - 發送 `/newbot` 創建新機器人
   - 獲取 bot token

3. 如何獲取 Chat ID：
   - 將機器人添加到你的群組或頻道
   - 發送一條消息
   - 訪問 `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - 找到 `chat.id` 欄位

## 使用方法

### 測試爬蟲功能
```bash
python run.py --scrape
```

### 測試 Telegram 通知
```bash
python run.py --telegram
```

### 測試所有功能
```bash
python run.py --all
```

## 文件結構

```
gate_futures_monitor/
├── config.py            # 配置文件
├── logger.py            # 日誌工具
├── scraper.py           # 網頁爬蟲
├── telegram_bot.py      # Telegram 機器人
├── run.py               # 運行腳本
├── requirements.txt     # 依賴列表
├── README.md           # 說明文檔
└── data/               # 數據存儲目錄
```

## 配置選項

在 `config.py` 中可以調整以下設定：

- `CHECK_INTERVAL`: 檢查間隔（秒），預設 5 分鐘
- `MONITOR_URL`: 監控的網頁 URL
- `DATA_DIR`: 數據存儲目錄
- `LOG_LEVEL`: 日誌級別

## 日誌

程式會生成詳細的日誌文件，保存在 `data/` 目錄下：
- 控制台輸出：即時顯示
- 文件日誌：按日期保存

## 注意事項

1. 確保網路連接穩定
2. 首次運行會創建必要的目錄和文件
3. 程式會自動處理重複的期貨上市信息
4. 可以通過 Ctrl+C 優雅地停止程式

## 故障排除

### 爬蟲無法獲取數據
- 檢查網路連接
- 確認 Gate.io 網站可訪問
- 查看日誌文件中的錯誤信息

### Telegram 通知失敗
- 檢查 bot token 是否正確
- 確認 chat ID 是否正確
- 驗證機器人是否已添加到群組/頻道

## 技術特點

- **智能爬蟲**: 使用 Playwright 自動化瀏覽器，支援動態內容
- **語言優先**: 自動檢測並優先顯示中文內容
- **反爬蟲對策**: 模擬真實用戶行為，避免被檢測
- **異步處理**: 使用 asyncio 提高性能和穩定性
- **錯誤處理**: 完善的異常處理和重試機制

## 更新日誌

### v1.0.0
- ✅ 實現基本爬蟲功能
- ✅ 支援 Telegram 通知
- ✅ 繁體中文界面
- ✅ 智能內容過濾
- ✅ 歷史記錄管理

## 授權

MIT License
