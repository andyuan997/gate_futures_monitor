import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any
from scraper import get_futures_listings
from telegram_bot import TelegramBot
from config import GateFuturesConfig
from logger import setup_gate_logger

logger = setup_gate_logger(__name__)

class GateFuturesMonitor:
    """Gate.io 期货上市监控器"""
    
    def __init__(self):
        self.config = GateFuturesConfig()
        self.telegram_bot = TelegramBot()
        self.history_file = os.path.join(self.config.DATA_DIR, self.config.HISTORY_FILE)
        self.known_listings = self._load_history()
    
    def _load_history(self) -> List[str]:
        """加载已知的期货上市记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 提取已知的标题作为标识
                    return [item.get('title', '') for item in data if item.get('title')]
            return []
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            return []
    
    def _save_history(self, listings: List[Dict[str, Any]]) -> None:
        """保存期货上市记录到历史文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(listings, f, ensure_ascii=False, indent=2)
            logger.info(f"历史记录已保存到: {self.history_file}")
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def _find_new_listings(self, current_listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """找出新的期货上市信息"""
        new_listings = []
        
        for listing in current_listings:
            title = listing.get('title', '')
            if title and title not in self.known_listings:
                new_listings.append(listing)
                logger.info(f"发现新的期货上市: {title}")
        
        return new_listings
    
    async def check_for_updates(self) -> None:
        """检查是否有新的期货上市"""
        try:
            logger.info("开始检查 Gate.io 期货上市更新...")
            
            # 获取当前期货上市列表
            current_listings = await get_futures_listings()
            
            if not current_listings:
                logger.warning("未能获取到期货上市信息")
                return
            
            # 找出新的上市信息
            new_listings = self._find_new_listings(current_listings)
            
            if new_listings:
                logger.info(f"发现 {len(new_listings)} 个新的期货上市")
                
                # 发送 Telegram 通知
                await self.telegram_bot.send_futures_notification(new_listings)
                
                # 更新已知列表
                self.known_listings.extend([listing.get('title', '') for listing in new_listings])
                
                # 保存更新后的历史记录
                self._save_history(current_listings)
            else:
                logger.info("没有发现新的期货上市")
                
        except Exception as e:
            logger.error(f"检查更新时发生错误: {e}")
    
    async def run_monitor(self) -> None:
        """运行监控器"""
        logger.info("Gate.io 期货上市监控器启动")
        logger.info(f"监控页面: {self.config.MONITOR_URL}")
        logger.info(f"检查间隔: {self.config.CHECK_INTERVAL} 秒")
        
        try:
            while True:
                await self.check_for_updates()
                logger.info(f"等待 {self.config.CHECK_INTERVAL} 秒后进行下次检查...")
                await asyncio.sleep(self.config.CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("监控器被用户中断")
        except Exception as e:
            logger.error(f"监控器运行时发生错误: {e}")
        finally:
            logger.info("Gate.io 期货上市监控器已停止")

async def main():
    """主函数"""
    monitor = GateFuturesMonitor()
    await monitor.run_monitor()

if __name__ == "__main__":
    asyncio.run(main())
