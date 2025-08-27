"""
Gate.io 期貨上市監控爬蟲
使用 Playwright 來爬取 Gate.io 的期貨上市公告
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright, Browser, Page
from config import GateFuturesConfig
from logger import setup_gate_logger
import re

logger = setup_gate_logger(__name__)


class GateFuturesScraper:
    """Gate.io 期貨上市爬蟲類"""

    def __init__(self):
        """初始化爬蟲"""
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context: Optional[Any] = None  # 新增 context 屬性
        
        # 確保數據目錄存在
        os.makedirs(GateFuturesConfig.DATA_DIR, exist_ok=True)
        
        # 歷史數據文件路徑
        self.history_file = os.path.join(GateFuturesConfig.DATA_DIR, GateFuturesConfig.HISTORY_FILE)

    async def _setup_browser(self):
        """初始化瀏覽器"""
        try:
            logger.info("正在初始化瀏覽器...")
            playwright = await async_playwright().start()
            
            # 採用 GateioWebScraper 的成功設定
            self.browser = await playwright.chromium.launch(
                channel='chrome',
                headless=True,  # 改為無頭模式
                args=['--no-sandbox']
            )
            
            # 創建上下文，設定語言和時區
            self.context = await self.browser.new_context(
                locale="zh-TW",
                timezone_id="Asia/Taipei",
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"),
                extra_http_headers={"Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"}
            )
            
            self.page = await self.context.new_page()
            
            # gate.com（Next.js）常用 NEXT_LOCALE，提前設 localStorage
            await self.page.add_init_script("try { localStorage.setItem('NEXT_LOCALE', 'zh-tw'); } catch(e) {}")
            
            # 同時對 gate.io / gate.com 都設定語言 cookie
            await self.context.add_cookies([
                {"name": "lang", "value": "zh-tw", "domain": ".gate.io", "path": "/"},
                {"name": "lang", "value": "zh-tw", "domain": ".gate.com", "path": "/"}
            ])
            
            logger.info("瀏覽器初始化完成")
        except Exception as e:
            logger.error(f"瀏覽器初始化失敗: {e}")
            raise

    async def _cleanup(self):
        """清理資源"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("瀏覽器資源清理完成")
        except Exception as e:
            logger.error(f"清理資源時發生錯誤: {e}")

    async def scrape_futures_listings(self) -> List[Dict[str, Any]]:
        """爬取期貨上市列表"""
        try:
            if not self.page:
                await self._setup_browser()
            
            # 訪問期貨上市頁面
            futures_url = "https://www.gate.com/zh-tw/announcements/newfutureslistings"
            logger.info(f"開始訪問頁面: {futures_url}")
            await self.page.goto(futures_url, timeout=60000, wait_until="domcontentloaded")
            
            # 等待頁面加載
            await asyncio.sleep(3)
            
            # 使用 GateioWebScraper 的成功選擇器
            selector = "a[href*='/announcements/article/']"
            title_selector = "p"
            
            try:
                await self.page.wait_for_selector(selector, timeout=10000)
                logger.info("找到目標選擇器")
            except Exception as e:
                logger.warning(f"等待選擇器超時: {e}")
            
            # 提取數據
            links = await self.page.query_selector_all(selector)
            logger.info(f"找到 {len(links)} 個鏈接元素")
            
            futures_data = []
            for link in links:
                title_el = await link.query_selector(title_selector)
                href = await link.get_attribute("href")
                
                if title_el and href:
                    title = await title_el.inner_text()
                    title = title.strip()
                    logger.info(f"找到公告: {title}")
                    
                    # 檢查是否包含期貨相關關鍵詞
                    has_futures_keywords = any(keyword in title for keyword in 
                        ['永續合約', '上線', 'Contract', 'Futures', 'Perpetual'])
                    
                    if has_futures_keywords:
                        # 檢測語言（優先中文）
                        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', title))
                        is_english = bool(re.search(r'[a-zA-Z]', title))
                        
                        futures_data.append({
                            'title': title,
                            'url': 'https://www.gate.com' + href,
                            'language': 'zh' if is_chinese else ('en' if is_english else 'unknown'),
                            'element_type': 'a',
                            'class_name': await link.get_attribute('class') or '',
                            'scraped_at': datetime.now().isoformat()
                        })
            
            # 按語言排序：中文優先
            futures_data.sort(key=lambda x: (x['language'] != 'zh', x['language'] != 'en'))
            
            logger.info(f"成功提取 {len(futures_data)} 條期貨上市信息")
            
            # 顯示提取到的內容用於調試
            for i, item in enumerate(futures_data[:5]):
                logger.info(f"提取項 {i+1}: {item.get('title', '')[:50]}...")
                logger.info(f"  URL: {item.get('url', '')}")
                logger.info(f"  語言: {item.get('language', '')}")
                logger.info(f"  元素類型: {item.get('element_type', '')}")
            
            return futures_data
            
        except Exception as e:
            logger.error(f"爬取期貨上市信息失敗: {e}")
            return []

    def save_to_history(self, futures_data: List[Dict[str, Any]]):
        """保存數據到歷史文件"""
        try:
            # 讀取現有歷史數據
            existing_data = []
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # 添加新數據
            for item in futures_data:
                # 檢查是否已存在（基於標題和URL）
                if not any(existing['title'] == item['title'] and existing['url'] == item['url'] 
                          for existing in existing_data):
                    existing_data.append(item)
            
            # 保存到文件
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存 {len(futures_data)} 條數據到歷史文件")
            
        except Exception as e:
            logger.error(f"保存歷史數據失敗: {e}")

    def get_new_listings(self, futures_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """獲取新的上市信息（與歷史數據比較）"""
        try:
            if not os.path.exists(self.history_file):
                return futures_data
            
            # 讀取歷史數據
            with open(self.history_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # 找出新數據
            new_listings = []
            for item in futures_data:
                if not any(existing['title'] == item['title'] and existing['url'] == item['url'] 
                          for existing in existing_data):
                    new_listings.append(item)
            
            logger.info(f"發現 {len(new_listings)} 條新的期貨上市信息")
            return new_listings
            
        except Exception as e:
            logger.error(f"獲取新上市信息失敗: {e}")
            return futures_data
