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

logger = setup_gate_logger(__name__)


class GateFuturesMonitor:
    """Gate.io 期貨上市監控器"""
    
    def __init__(self):
        """初始化監控器"""
        self.scraper = GateFuturesScraper()
        self.telegram_bot = TelegramBot()
        self.running = True
        self.check_interval = GateFuturesConfig.CHECK_INTERVAL
        
        # 設定信號處理
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
            
            # 爬取期貨上市數據
            futures_data = await self.scraper.scrape_futures_listings()
            
            if not futures_data:
                logger.warning("⚠️ 未能獲取到期貨上市信息")
                return
            
            logger.info(f"📊 成功獲取 {len(futures_data)} 條期貨上市信息")
            
            # 檢查是否為第一次運行（沒有歷史文件）
            is_first_run = not os.path.exists(self.scraper.history_file)
            
            if is_first_run:
                logger.info("🆕 首次運行檢測到，只儲存數據，不發送通知")
                # 保存所有數據到歷史記錄
                self.scraper.save_to_history(futures_data)
                logger.info("✅ 首次數據儲存完成，下次運行將開始監控新數據")
                return
            
            # 非首次運行，進行正常的比對和通知流程
            logger.info("📋 檢測到歷史文件，開始比對新數據...")
            
            # 逐條檢查新數據
            new_count = 0
            for item in futures_data:
                # 檢查是否為新數據
                if self.scraper.is_new_listing(item):
                    logger.info(f"🎉 發現新的期貨上市: {item.get('title', '')}")
                    
                    # 立即發送該條通知
                    if await self.telegram_bot.send_futures_notification(item):
                        logger.info(f"✅ 已發送通知: {item.get('title', '')}")
                        new_count += 1
                    else:
                        logger.error(f"❌ 通知發送失敗: {item.get('title', '')}")
                else:
                    logger.debug(f"跳過已存在的期貨: {item.get('title', '')}")
            
            if new_count > 0:
                logger.info(f"🎉 本次檢查發現 {new_count} 條新的期貨上市信息！")
                # 保存所有數據到歷史記錄
                self.scraper.save_to_history(futures_data)
            else:
                logger.info("📝 沒有發現新的期貨上市信息")
                
        except Exception as e:
            logger.error(f"❌ 檢查更新時發生錯誤: {e}")
    
    async def run_monitor(self):
        """運行監控器"""
        logger.info("🚀 Gate.io 期貨上市監控器啟動")
        logger.info(f"📅 檢查間隔: {self.check_interval} 秒")
        logger.info(f"🔗 監控頁面: {GateFuturesConfig.MONITOR_URL}")
        logger.info("💡 按 Ctrl+C 停止監控器")
        
        # 首次檢查
        await self.check_for_updates()
        
        try:
            while self.running:
                # 等待下次檢查
                logger.info(f"⏰ 等待 {self.check_interval} 秒後進行下次檢查...")
                await asyncio.sleep(self.check_interval)
                
                # 檢查更新
                await self.check_for_updates()
                
        except KeyboardInterrupt:
            logger.info("⏹️ 監控器被用戶中斷")
        except Exception as e:
            logger.error(f"💥 監控器運行時發生錯誤: {e}")
        finally:
            logger.info("🛑 Gate.io 期貨上市監控器已停止")
            await self.scraper._cleanup()


async def main():
    """主函數"""
    monitor = GateFuturesMonitor()
    await monitor.run_monitor()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 程序被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 程序運行時發生錯誤: {e}")
        sys.exit(1)
