# Gate.io 期货上市监控器

一个独立的 Python 程序，用于监控 [Gate.io 新期货上市页面](https://www.gate.com/zh-tw/announcements/newfutureslistings) 并发送 Telegram 通知。

## 功能特点

- 🚀 自动监控 Gate.io 新期货上市
- 📱 实时 Telegram 通知
- 💾 本地历史记录存储
- 🔄 可配置的检查间隔
- 📊 详细的日志记录

## 安装依赖

```bash
cd gate_futures_monitor
pip install -r requirements.txt
playwright install chromium
```

## 配置

1. 编辑 `config.py` 文件，配置你的 Telegram 机器人：

```python
# Telegram 配置
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # 替换为你的bot token
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"      # 替换为你的chat ID
```

2. 如何获取 Telegram Bot Token：
   - 在 Telegram 中搜索 `@BotFather`
   - 发送 `/newbot` 创建新机器人
   - 获取 bot token

3. 如何获取 Chat ID：
   - 将机器人添加到你的群组或频道
   - 发送一条消息
   - 访问 `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - 找到 `chat.id` 字段

## 使用方法

### 启动监控器
```bash
python run.py
```

### 测试 Telegram 机器人
```bash
python run.py --test
```

### 测试爬虫功能
```bash
python run.py --scrape
```

## 文件结构

```
gate_futures_monitor/
├── __init__.py          # 包初始化文件
├── config.py            # 配置文件
├── logger.py            # 日志工具
├── scraper.py           # 网页爬虫
├── telegram_bot.py      # Telegram 机器人
├── monitor.py           # 主监控器
├── run.py               # 运行脚本
├── requirements.txt     # 依赖列表
├── README.md           # 说明文档
├── data/               # 数据存储目录
└── logs/               # 日志文件目录
```

## 配置选项

在 `config.py` 中可以调整以下设置：

- `CHECK_INTERVAL`: 检查间隔（秒），默认 5 分钟
- `MONITOR_URL`: 监控的网页 URL
- `DATA_DIR`: 数据存储目录
- `LOG_LEVEL`: 日志级别

## 日志

程序会生成详细的日志文件，保存在 `logs/` 目录下，格式为：
- 控制台输出：实时显示
- 文件日志：按日期保存

## 注意事项

1. 确保网络连接稳定
2. 首次运行会创建必要的目录和文件
3. 程序会自动处理重复的期货上市信息
4. 可以通过 Ctrl+C 优雅地停止程序

## 故障排除

### 爬虫无法获取数据
- 检查网络连接
- 确认 Gate.io 网站可访问
- 查看日志文件中的错误信息

### Telegram 通知失败
- 检查 bot token 是否正确
- 确认 chat ID 是否正确
- 验证机器人是否已添加到群组/频道

## 许可证

MIT License
