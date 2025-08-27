# Gate.io 期貨上市監控器

一個獨立的 Python 程序，用於監控 [Gate.io 新期貨上市頁面](https://www.gate.com/zh-tw/announcements/newfutureslistings) 並發送 Telegram 通知。

## 功能特點

- 🚀 自動監控 Gate.io 新期貨上市
- 📱 即時 Telegram 通知
- 💾 本地歷史記錄存儲
- 🔄 可配置的檢查間隔
- 📊 詳細的日誌記錄
- ☁️ 支援 Render 雲端部署

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

### 本地測試
```bash
# 測試爬蟲功能
python run.py --scrape

# 測試 Telegram 通知
python run.py --telegram

# 測試完整工作流程
python run.py --workflow
```

### 持續監控（推薦用於生產環境）
```bash
# 啟動持續監控
python main.py
```

## 文件結構

```
gate_futures_monitor/
├── main.py                 # 主程序（持續監控）
├── scraper.py              # 網頁爬蟲核心
├── telegram_bot.py         # Telegram 通知模組
├── config.py               # 配置文件
├── logger.py               # 日誌配置
├── requirements.txt        # Python 依賴
├── README.md              # 項目說明
├── data/                  # 數據存儲目錄
│   ├── futures_history.json    # 期貨上市歷史記錄
│   └── gate_futures.log        # 運行日誌
└── .git/                  # Git 版本控制
```

## Render 雲端部署

### 手動部署
1. 將代碼推送到 GitHub
2. 在 [Render.com](https://render.com) 創建新的 Web Service
3. 連接你的 GitHub 倉庫
4. 設定環境變數：
   - `TELEGRAM_BOT_TOKEN`: 你的 bot token
   - `TELEGRAM_CHAT_ID`: 你的 chat ID
5. 設定構建和啟動命令：
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium && playwright install-deps chromium`
   - **Start Command**: `python main.py`
6. 部署完成後，服務會自動運行並持續監控

### 部署計劃
- **免費計劃**: 可以部署但會自動休眠
- **付費計劃**: 持續運行，適合生產環境

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
5. 在 Render 上部署時，免費計劃會自動休眠，付費計劃可持續運行

## 故障排除

### 爬蟲無法獲取數據
- 檢查網路連接
- 確認 Gate.io 網站可訪問
- 查看日誌文件中的錯誤信息

### Telegram 通知失敗
- 檢查 bot token 是否正確
- 確認 chat ID 是否正確
- 驗證機器人是否已添加到群組/頻道

### Render 部署問題
- 確認環境變數設定正確
- 檢查構建日誌是否有錯誤
- 確認 Playwright 依賴安裝成功

## 技術特點

- **智能爬蟲**: 使用 Playwright 自動化瀏覽器，支援動態內容
- **語言優先**: 自動檢測並優先顯示中文內容
- **反爬蟲對策**: 模擬真實用戶行為，避免被檢測
- **異步處理**: 使用 asyncio 提高性能和穩定性
- **錯誤處理**: 完善的異常處理和重試機制
- **雲端就緒**: 支援 Render 等雲端平台部署

## 更新日誌

### v1.1.0
- ✅ 新增持續監控模式 (`main.py`)
- ✅ 支援 Render 雲端部署
- ✅ 改進錯誤處理和日誌記錄
- ✅ 優化資源管理和優雅關閉

### v1.0.0
- ✅ 實現基本爬蟲功能
- ✅ 支援 Telegram 通知
- ✅ 繁體中文界面
- ✅ 智能內容過濾
- ✅ 歷史記錄管理

## 授權

MIT License
