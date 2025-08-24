#!/usr/bin/env python3
"""
Gate.io 期货上市监控器 - 独立运行脚本

使用方法:
    python run.py                    # 启动监控器
    python run.py --test            # 测试 Telegram 机器人
    python run.py --scrape          # 测试爬虫功能
"""

import asyncio
import sys
import argparse
from monitor import GateFuturesMonitor
from scraper import get_futures_listings
from telegram_bot import TelegramBot
from logger import setup_gate_logger

logger = setup_gate_logger(__name__)

async def test_scraper():
    """测试爬虫功能"""
    logger.info("开始测试爬虫功能...")
    try:
        listings = await get_futures_listings()
        logger.info(f"爬虫测试成功，获取到 {len(listings)} 条数据")
        
        # 显示前几条数据
        for i, listing in enumerate(listings[:3]):
            logger.info(f"示例 {i+1}: {listing.get('title', '')}")
            
        return True
    except Exception as e:
        logger.error(f"爬虫测试失败: {e}")
        return False

async def test_telegram():
    """测试 Telegram 机器人"""
    logger.info("开始测试 Telegram 机器人...")
    try:
        bot = TelegramBot()
        success = await bot.send_message("🧪 Gate.io 期货监控器测试消息\n\n如果收到此消息，说明配置正确！")
        
        if success:
            logger.info("Telegram 测试成功！")
            return True
        else:
            logger.error("Telegram 测试失败")
            return False
    except Exception as e:
        logger.error(f"Telegram 测试失败: {e}")
        return False

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Gate.io 期货上市监控器")
    parser.add_argument("--test", action="store_true", help="测试 Telegram 机器人")
    parser.add_argument("--scrape", action="store_true", help="测试爬虫功能")
    
    args = parser.parse_args()
    
    if args.test:
        await test_telegram()
    elif args.scrape:
        await test_scraper()
    else:
        # 启动监控器
        logger.info("启动 Gate.io 期货上市监控器...")
        monitor = GateFuturesMonitor()
        await monitor.run_monitor()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)
