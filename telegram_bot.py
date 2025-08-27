"""
Telegram 機器人通知模組
用於發送 Gate.io 期貨上市通知
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
from config import GateFuturesConfig
from logger import setup_gate_logger

logger = setup_gate_logger(__name__)


class TelegramBot:
    """Telegram 機器人類"""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        """初始化 Telegram 機器人
        
        Args:
            bot_token: Telegram 機器人 token
            chat_id: 聊天室 ID
        """
        self.bot_token = bot_token or GateFuturesConfig.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or GateFuturesConfig.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, message: str) -> bool:
        """發送消息到 Telegram
        
        Args:
            message: 要發送的消息內容
            
        Returns:
            bool: 發送是否成功
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.info("Telegram 消息發送成功")
                        return True
                    else:
                        logger.error(f"Telegram API 返回錯誤: {result}")
                        return False
                else:
                    logger.error(f"Telegram API 請求失敗，狀態碼: {response.status_code}")
                    return False
                        
        except Exception as e:
            logger.error(f"發送 Telegram 消息時發生錯誤: {e}")
            return False

    async def send_futures_notification(self, futures_data: Dict[str, Any]) -> bool:
        """發送期貨上市通知
        
        Args:
            futures_data: 期貨上市數據
            
        Returns:
            bool: 發送是否成功
        """
        try:
            # 構建通知消息
            title = futures_data.get("title", "未知期貨")
            url = futures_data.get("url", "")
            
            # 使用發送當下時間
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"""
            🚀 <b>Gate.io 新期貨上市通知</b>

            📈 <b>新期貨:</b> {title}
            🕐 <b>發送時間:</b> {current_time}

            🔗 <b>連結:</b> <a href="{url}">   點擊查看</a>

            #GateIO #期貨 #新上市
            """.strip()
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"構建期貨通知消息時發生錯誤: {e}")
            return False

    async def send_batch_notification(self, futures_list: list) -> bool:
        """批量發送期貨上市通知
        
        Args:
            futures_list: 期貨上市數據列表
            
        Returns:
            bool: 發送是否成功
        """
        try:
            if not futures_list:
                logger.info("沒有新的期貨上市信息需要通知")
                return True
            
            # 構建批量通知消息
            message = f"🚀 <b>Gate.io 新期貨上市通知</b>\n\n"
            message += f"📊 發現 <b>{len(futures_list)}</b> 個新期貨上市\n\n"
            
            for i, futures in enumerate(futures_list[:10], 1):  # 最多顯示10個
                title = futures.get("title", "未知期貨")
                url = futures.get("url", "")
                
                # 處理日期顯示
                discovered_at = futures.get("discovered_at", "")
                date_display = ""
                if discovered_at:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(discovered_at.replace('Z', '+00:00'))
                        date_display = dt.strftime("%m-%d %H:%M")
                    except:
                        date_display = discovered_at[:16] if len(discovered_at) > 16 else discovered_at
                
                message += f"{i}. <b>{title}</b>\n"
                if date_display:
                    message += f"   🕐 {date_display}\n"
                message += f"   🔗 <a href=\"{url}\">查看詳情</a>\n\n"
            
            if len(futures_list) > 10:
                message += f"... 還有 {len(futures_list) - 10} 個期貨上市信息\n\n"
            
            message += "#GateIO #期貨 #新上市"
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"構建批量通知消息時發生錯誤: {e}")
            return False

    async def test_connection(self) -> bool:
        """測試 Telegram 連接
        
        Returns:
            bool: 連接是否成功
        """
        try:
            url = f"{self.base_url}/getMe"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        bot_info = result.get("result", {})
                        bot_name = bot_info.get("first_name", "未知")
                        bot_username = bot_info.get("username", "未知")
                        logger.info(f"Telegram 機器人連接成功: {bot_name} (@{bot_username})")
                        return True
                    else:
                        logger.error(f"Telegram API 返回錯誤: {result}")
                        return False
                else:
                    logger.error(f"Telegram API 請求失敗，狀態碼: {response.status_code}")
                    return False
                        
        except Exception as e:
            logger.error(f"測試 Telegram 連接時發生錯誤: {e}")
            return False
