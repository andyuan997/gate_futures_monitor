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
            # 強制查找瀏覽器路徑
            import glob
            import os
            import subprocess
            
            # 嘗試強制安裝瀏覽器
            try:
                logger.info("嘗試強制安裝瀏覽器...")
                result = subprocess.run(['playwright', 'install', 'chromium'], 
                                     capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    logger.info("瀏覽器安裝成功")
                else:
                    logger.warning(f"瀏覽器安裝失敗: {result.stderr}")
            except Exception as e:
                logger.warning(f"瀏覽器安裝異常: {e}")
            
            # 查找可能的瀏覽器路徑
            possible_paths = [
                "/opt/render/.cache/ms-playwright/chromium-*/chrome-linux/chrome",
                "/opt/render/.cache/ms-playwright/chromium-*/chrome-linux/chromium",
                "/opt/render/.cache/ms-playwright/chromium-*/chrome-linux/chrome-wrapper",
                "/opt/render/.cache/ms-playwright/chromium-*/chrome-linux/chrome-sandbox"
            ]
            
            browser_path = None
            for path_pattern in possible_paths:
                matches = glob.glob(path_pattern)
                if matches:
                    browser_path = matches[0]
                    logger.info(f"找到瀏覽器路徑: {browser_path}")
                    break
            
            if not browser_path:
                logger.warning("未找到瀏覽器路徑，嘗試使用系統路徑")
                # 嘗試使用系統安裝的瀏覽器
                system_paths = [
                    "/usr/bin/chromium-browser",
                    "/usr/bin/chromium",
                    "/usr/bin/google-chrome",
                    "/usr/bin/chrome"
                ]
                for sys_path in system_paths:
                    if os.path.exists(sys_path):
                        browser_path = sys_path
                        logger.info(f"使用系統瀏覽器: {browser_path}")
                        break
            
            self.browser = await playwright.chromium.launch(
                headless=True,  # 改為無頭模式
                executable_path=browser_path,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-ipc-flooding-protection',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--no-default-browser-check',
                    '--disable-component-update',
                    '--disable-domain-reliability',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-renderer-backgrounding',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-update',
                    '--disable-default-apps',
                    '--disable-domain-reliability',
                    '--disable-features=AudioServiceOutOfProcess',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--disable-web-resources',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--safebrowsing-disable-auto-update',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # 創建上下文，設定語言和時區
            self.context = await self.browser.new_context(
                locale="zh-TW",
                timezone_id="Asia/Taipei",
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                extra_http_headers={
                    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1"
                }
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
            await self.page.goto(futures_url, timeout=180000, wait_until="networkidle")
            
            # 等待頁面加載 - 增加等待時間
            logger.info("等待頁面完全加載...")
            await asyncio.sleep(5)
            
            # 使用 GateioWebScraper 的成功選擇器
            selector = "a[href*='/announcements/article/']"
            title_selector = "p"
            
            # 增加等待時間，並嘗試多種等待策略
            try:
                # 首先等待頁面基本加載
                logger.info("等待頁面網絡加載...")
                await self.page.wait_for_load_state("networkidle", timeout=60000)
                logger.info("頁面網絡加載完成")
                
                # 等待選擇器出現
                logger.info("等待目標選擇器...")
                await self.page.wait_for_selector(selector, timeout=60000)
                logger.info("找到目標選擇器")
                
                # 額外等待確保內容渲染完成
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.warning(f"等待選擇器超時: {e}")
                # 嘗試多種等待策略
                try:
                    logger.info("嘗試等待 DOM 加載...")
                    await self.page.wait_for_load_state("domcontentloaded", timeout=45000)
                    await asyncio.sleep(8)
                    
                    # 嘗試滾動頁面來觸發懶加載
                    logger.info("嘗試滾動頁面...")
                    try:
                        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(3)
                        await self.page.evaluate("window.scrollTo(0, 0)")
                        await asyncio.sleep(3)
                        logger.info("頁面滾動完成")
                    except Exception as scroll_error:
                        logger.warning(f"頁面滾動失敗: {scroll_error}")
                    
                    # 再次嘗試等待選擇器
                    await self.page.wait_for_selector(selector, timeout=45000)
                    logger.info("滾動後找到選擇器")
                    
                except Exception as e2:
                    logger.warning(f"滾動策略失敗: {e2}")
                    try:
                        logger.info("嘗試最終等待策略...")
                        await asyncio.sleep(15)
                        
                        # 嘗試檢查頁面內容
                        page_content = await self.page.content()
                        logger.info(f"頁面內容長度: {len(page_content)}")
                        
                        # 檢查是否有任何鏈接
                        all_links = await self.page.query_selector_all("a")
                        logger.info(f"頁面中找到 {len(all_links)} 個鏈接")
                        
                        # 檢查是否有任何包含 'announcements' 的鏈接
                        announcement_links = await self.page.query_selector_all("a[href*='announcements']")
                        logger.info(f"頁面中找到 {len(announcement_links)} 個公告鏈接")
                        
                        await self.page.wait_for_selector(selector, timeout=45000)
                        logger.info("最終等待後找到選擇器")
                        
                    except Exception as e3:
                        logger.error(f"所有等待策略都失敗: {e3}")
                        return []
            
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
                            'article_id': href.split('/')[-1] if href else '',
                            'language': 'zh' if is_chinese else ('en' if is_english else 'unknown'),
                            'element_type': 'a',
                            'class_name': await link.get_attribute('class') or ''
                        })
            
            # 按語言排序：中文優先
            futures_data.sort(key=lambda x: (x['language'] != 'zh', x['language'] != 'en'))
            
            logger.info(f"成功提取 {len(futures_data)} 條期貨上市信息")
            
            # 顯示提取到的內容用於調試
            for i, item in enumerate(futures_data[:5]):
                logger.info(f"提取項 {i+1}: {item.get('title', '')}")
                logger.info(f"  URL: {item.get('url', '')}")
                logger.info(f"  語言: {item.get('language', '')}")
                logger.info(f"  元素類型: {item.get('element_type', '')}")
            
            return futures_data
            
        except Exception as e:
            logger.error(f"爬取期貨上市信息失敗: {e}")
            return []
    
    def is_new_listing(self, item: Dict[str, Any]) -> bool:
        """檢查單條數據是否為新的期貨上市
        
        Args:
            item: 要檢查的期貨上市數據
            
        Returns:
            bool: True 表示是新數據，False 表示已存在
        """
        try:
            if not os.path.exists(self.history_file):
                return True
            
            # 讀取歷史數據
            with open(self.history_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            title = item.get('title', '').strip()
            url = item.get('url', '').strip()
            
            if not title or not url:
                return False
            
            # 創建唯一標識符
            unique_id = f"{title}|{url}"
            
            # 檢查是否已存在
            for existing in existing_data:
                existing_title = existing.get('title', '').strip()
                existing_url = existing.get('url', '').strip()
                
                if existing_title and existing_url:
                    existing_unique_id = f"{existing_title}|{existing_url}"
                    if existing_unique_id == unique_id:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"檢查新上市信息失敗: {e}")
            return True  # 出錯時視為新數據

    def get_new_listings(self, current_listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """獲取新的期貨上市信息（與歷史數據比較）
        
        Args:
            current_listings: 當前爬取到的期貨上市列表
            
        Returns:
            List[Dict[str, Any]]: 新的期貨上市信息列表
        """
        try:
            if not os.path.exists(self.history_file):
                logger.info("歷史文件不存在，所有數據都視為新數據")
                return current_listings
            
            # 讀取歷史數據
            with open(self.history_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # 創建已知數據的集合，用於快速查找
            # 只基於標題和URL進行比對
            known_items = set()
            for item in existing_data:
                title = item.get('title', '').strip()
                url = item.get('url', '').strip()
                if title and url:
                    # 創建唯一標識符（標題 + URL）
                    unique_id = f"{title}|{url}"
                    known_items.add(unique_id)
            
            # 找出新數據
            new_listings = []
            for item in current_listings:
                title = item.get('title', '').strip()
                url = item.get('url', '').strip()
                
                if title and url:
                    # 創建唯一標識符
                    unique_id = f"{title}|{url}"
                    
                    # 檢查是否為新數據
                    if unique_id not in known_items:
                        new_listings.append(item)
                        logger.info(f"發現新的期貨上市: {title}")
                    else:
                        logger.debug(f"跳過已存在的期貨上市: {title}")
            
            logger.info(f"總共發現 {len(new_listings)} 條新的期貨上市信息")
            return new_listings
            
        except Exception as e:
            logger.error(f"獲取新上市信息失敗: {e}")
            return current_listings

    def save_to_history(self, futures_data: List[Dict[str, Any]]) -> None:
        """保存數據到歷史文件（只添加新數據）
        
        Args:
            futures_data: 要保存的期貨上市數據列表
        """
        try:
            # 讀取現有歷史數據
            existing_data = []
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # 創建已知數據的集合
            known_items = set()
            for item in existing_data:
                title = item.get('title', '').strip()
                url = item.get('url', '').strip()
                if title and url:
                    unique_id = f"{title}|{url}"
                    known_items.add(unique_id)
            
            # 只添加新數據
            added_count = 0
            for item in futures_data:
                title = item.get('title', '').strip()
                url = item.get('url', '').strip()
                
                if title and url:
                    unique_id = f"{title}|{url}"
                    
                    if unique_id not in known_items:
                        # 添加新數據到歷史記錄
                        existing_data.append(item)
                        added_count += 1
                        logger.debug(f"添加新數據: {title}")
                    else:
                        logger.debug(f"數據已存在，跳過: {title}")
            
            # 保存到文件
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功添加 {added_count} 條新數據到歷史文件，總計 {len(existing_data)} 條")
            
        except Exception as e:
            logger.error(f"保存歷史數據失敗: {e}")

