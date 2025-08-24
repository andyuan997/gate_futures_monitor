import aiohttp
import asyncio
from typing import List, Dict, Any
from config import GateFuturesConfig
from logger import setup_gate_logger

logger = setup_gate_logger(__name__)

class TelegramBot:
    """Telegram 通知机器人"""
    
    def __init__(self):
        self.config = GateFuturesConfig()
        self.base_url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}"
    
    async def send_message(self, message: str) -> bool:
        """发送消息到 Telegram"""
        try:
            if self.config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
                logger.warning("请先配置 Telegram Bot Token")
                return False
                
            if self.config.TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
                logger.warning("请先配置 Telegram Chat ID")
                return False
            
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("Telegram 消息发送成功")
                            return True
                        else:
                            logger.error(f"Telegram API 返回错误: {result}")
                            return False
                    else:
                        logger.error(f"Telegram API 请求失败，状态码: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"发送 Telegram 消息时发生错误: {e}")
            return False
    
    async def send_futures_notification(self, new_listings: List[Dict[str, Any]]) -> None:
        """发送期货上市通知"""
        if not new_listings:
            logger.info("没有新的期货上市信息需要通知")
            return
        
        logger.info(f"准备发送 {len(new_listings)} 条期货上市通知")
        
        for listing in new_listings:
            # 格式化通知消息
            message = self.config.NOTIFICATION_TEMPLATE.format(
                symbol=listing.get('title', '未知'),
                listing_time=listing.get('time', '未知'),
                url=listing.get('url', '')
            )
            
            # 发送通知
            success = await self.send_message(message)
            if success:
                logger.info(f"成功发送期货上市通知: {listing.get('title', '')}")
            else:
                logger.error(f"发送期货上市通知失败: {listing.get('title', '')}")
            
            # 避免发送过快
            await asyncio.sleep(1)

async def test_telegram_bot():
    """测试 Telegram 机器人"""
    bot = TelegramBot()
    test_message = "🧪 这是 Gate.io 期货监控的测试消息\n\n如果收到此消息，说明配置正确！"
    
    success = await bot.send_message(test_message)
    if success:
        print("✅ Telegram 测试消息发送成功！")
    else:
        print("❌ Telegram 测试消息发送失败，请检查配置")

if __name__ == "__main__":
    asyncio.run(test_telegram_bot())
