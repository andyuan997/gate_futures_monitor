import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
from config import GateFuturesConfig
from logger import setup_gate_logger

logger = setup_gate_logger(__name__)

class GateFuturesScraper:
    """Gate.io 期货上市页面爬虫"""
    
    def __init__(self):
        self.config = GateFuturesConfig()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # 确保数据目录存在
        if not os.path.exists(self.config.DATA_DIR):
            os.makedirs(self.config.DATA_DIR)
    
    async def _setup_browser(self):
        """初始化浏览器"""
        try:
            logger.info("正在初始化浏览器...")
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,  # 无头模式，不显示浏览器窗口
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.page = await self.browser.new_page()
            
            # 设置用户代理
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            logger.info("浏览器初始化完成")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            raise
    
    async def _cleanup(self):
        """清理资源"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            logger.info("浏览器资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")
    
    async def scrape_futures_listings(self) -> List[Dict[str, Any]]:
        """爬取期货上市列表"""
        try:
            if not self.page:
                await self._setup_browser()
            
            logger.info(f"开始访问页面: {self.config.MONITOR_URL}")
            await self.page.goto(self.config.MONITOR_URL, timeout=30000)
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 提取期货上市信息
            futures_data = await self.page.evaluate("""
                () => {
                    const items = [];
                    // 查找所有公告项
                    const announcements = document.querySelectorAll('a[href*="/announcements/"]');
                    
                    announcements.forEach((announcement, index) => {
                        if (index < 20) { // 只取前20个
                            const title = announcement.textContent?.trim() || '';
                            const url = announcement.href || '';
                            
                            // 提取时间信息（如果有的话）
                            let timeInfo = '';
                            const timeElement = announcement.querySelector('time') || 
                                              announcement.closest('div')?.querySelector('time');
                            if (timeElement) {
                                timeInfo = timeElement.textContent?.trim() || '';
                            }
                            
                            if (title && url) {
                                items.push({
                                    title: title,
                                    url: url,
                                    time: timeInfo,
                                    scraped_at: new Date().toISOString()
                                });
                            }
                        }
                    });
                    
                    return items;
                }
            """)
            
            logger.info(f"成功提取 {len(futures_data)} 条期货上市信息")
            return futures_data
            
        except Exception as e:
            logger.error(f"爬取期货上市信息失败: {e}")
            return []
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._setup_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._cleanup()

async def get_futures_listings() -> List[Dict[str, Any]]:
    """获取期货上市列表的便捷函数"""
    async with GateFuturesScraper() as scraper:
        return await scraper.scrape_futures_listings()
