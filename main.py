#!/usr/bin/env python3
"""
Gate.io 期貨上市監控主程序
持續運行，定時檢查新的期貨上市信息
"""

import asyncio
import signal
import sys
import time
from datetime import datetime
from scraper import GateFuturesScraper
from telegram_bot import TelegramBot
from config import GateFuturesConfig
from logger import setup_gate_logger
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket

logger = setup_gate_logger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """健康檢查處理器"""
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # 禁用 HTTP 服務器的日誌輸出
        pass

def start_health_server():
    """啟動健康檢查服務器"""
    try:
        # 嘗試綁定到環境變數指定的端口，否則使用 8080
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"🌐 健康檢查服務器啟動在端口 {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"健康檢查服務器啟動失敗: {e}")

class GateFuturesMonitor:
    """Gate.io 期貨上市監控器"""

    def __init__(self):
        """初始化監控器"""
        self.scraper = GateFuturesScraper()
        self.telegram_bot = TelegramBot()
        self.running = True
        
        # 設置信號處理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信號處理器"""
        logger.info(f"收到信號 {signum}，準備優雅關閉...")
        self.running = False

    async def check_for_updates(self):
        """檢查是否有新的期貨上市"""
        try:
            logger.info("🔄 開始檢查 Gate.io 期貨上市更新...")

            futures_data = await self.scraper.scrape_futures_listings()

            if not futures_data:
                logger.warning("⚠️ 未能獲取到期貨上市信息")
                return

            logger.info(f"📊 成功獲取 {len(futures_data)} 條期貨上市信息")

            # 檢查是否為第一次運行（沒有歷史文件）
            is_first_run = not os.path.exists(self.scraper.history_file)

            if is_first_run:
                logger.info("🆕 首次運行檢測到，只儲存數據，不發送通知")
                self.scraper.save_to_history(futures_data)
                logger.info("✅ 首次數據儲存完成，下次運行將開始監控新數據")
                return

            # 非首次運行，進行正常的比對和通知流程
            logger.info("📋 檢測到歷史文件，開始比對新數據...")

            new_count = 0
            for item in futures_data:
                if self.scraper.is_new_listing(item):
                    logger.info(f"🎉 發現新的期貨上市: {item.get('title', '')}")

                    if await self.telegram_bot.send_futures_notification(item):
                        logger.info(f"✅ 已發送通知: {item.get('title', '')}")
                        new_count += 1
                    else:
                        logger.error(f"❌ 通知發送失敗: {item.get('title', '')}")
                else:
                    logger.debug(f"跳過已存在的期貨: {item.get('title', '')}")

            if new_count > 0:
                logger.info(f"🎉 本次檢查發現 {new_count} 條新的期貨上市信息！")
                self.scraper.save_to_history(futures_data)
            else:
                logger.info("📝 沒有發現新的期貨上市信息")

        except Exception as e:
            logger.error(f"❌ 檢查更新時發生錯誤: {e}")

    async def run_monitor(self):
        """運行監控器"""
        logger.info("🚀 Gate.io 期貨上市監控器啟動")
        logger.info(f"📅 檢查間隔: {GateFuturesConfig.CHECK_INTERVAL} 秒")
        logger.info(f"🔗 監控頁面: {GateFuturesConfig.MONITOR_URL}")
        logger.info("💡 按 Ctrl+C 停止監控器")

        while self.running:
            try:
                await self.check_for_updates()
                
                if self.running:
                    logger.info(f"⏰ 等待 {GateFuturesConfig.CHECK_INTERVAL} 秒後進行下次檢查...")
                    await asyncio.sleep(GateFuturesConfig.CHECK_INTERVAL)
                    
            except Exception as e:
                logger.error(f"❌ 監控器運行時發生錯誤: {e}")
                if self.running:
                    await asyncio.sleep(60)  # 發生錯誤時等待 1 分鐘再重試

        logger.info("🛑 監控器已停止")

async def main():
    """主函數"""
    # 啟動健康檢查服務器（在後台線程中）
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # 創建並運行監控器
    monitor = GateFuturesMonitor()
    await monitor.run_monitor()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 用戶中斷程序")
    except Exception as e:
        logger.error(f"❌ 程序運行時發生錯誤: {e}")
        sys.exit(1)
