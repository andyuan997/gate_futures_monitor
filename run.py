#!/usr/bin/env python3
"""
Gate.io 期貨上市監控主程序
用於測試爬蟲和 Telegram 通知功能
"""

import asyncio
import argparse
import sys
from scraper import GateFuturesScraper
from telegram_bot import TelegramBot
from logger import setup_gate_logger

logger = setup_gate_logger(__name__)


async def test_scraper():
    """測試爬蟲功能"""
    try:
        logger.info("開始測試爬蟲功能...")
        
        scraper = GateFuturesScraper()
        futures_data = await scraper.scrape_futures_listings()
        
        if futures_data:
            logger.info(f"爬蟲測試成功，獲取到 {len(futures_data)} 條數據")
            
            # 顯示前幾個示例
            for i, item in enumerate(futures_data[:3], 1):
                logger.info(f"示例 {i}: {item.get('title', '')}")
        else:
            logger.warning("爬蟲測試完成，但未獲取到數據")
            
        await scraper._cleanup()
        
    except Exception as e:
        logger.error(f"爬蟲測試失敗: {e}")
        return False
    
    return True


async def test_telegram():
    """測試 Telegram 通知功能"""
    try:
        logger.info("開始測試 Telegram 通知功能...")
        
        bot = TelegramBot()
        
        # 測試連接
        if not await bot.test_connection():
            logger.error("Telegram 連接測試失敗")
            return False
        
        # 發送測試消息
        test_message = "🧪 這是 Gate.io 期貨監控的測試消息\n\n如果收到此消息，說明配置正確！"
        
        if await bot.send_message(test_message):
            logger.info("Telegram 測試消息發送成功！")
            return True
        else:
            logger.error("Telegram 測試消息發送失敗")
            return False
            
    except Exception as e:
        logger.error(f"Telegram 測試失敗: {e}")
        return False


async def main():
    """主程序"""
    parser = argparse.ArgumentParser(description="Gate.io 期貨上市監控")
    parser.add_argument("--scrape", action="store_true", help="測試爬蟲功能")
    parser.add_argument("--telegram", action="store_true", help="測試 Telegram 通知")
    parser.add_argument("--all", action="store_true", help="測試所有功能")
    
    args = parser.parse_args()
    
    if not any([args.scrape, args.telegram, args.all]):
        print("請指定要測試的功能:")
        print("  --scrape    測試爬蟲功能")
        print("  --telegram  測試 Telegram 通知")
        print("  --all       測試所有功能")
        return
    
    success_count = 0
    total_tests = 0
    
    if args.scrape or args.all:
        total_tests += 1
        if await test_scraper():
            success_count += 1
    
    if args.telegram or args.all:
        total_tests += 1
        if await test_telegram():
            success_count += 1
    
    # 顯示測試結果
    print(f"\n📊 測試結果: {success_count}/{total_tests} 項測試通過")
    
    if success_count == total_tests:
        print("🎉 所有測試都通過了！")
        sys.exit(0)
    else:
        print("❌ 部分測試失敗，請檢查配置和網絡連接")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  程序被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 程序運行時發生錯誤: {e}")
        sys.exit(1)
