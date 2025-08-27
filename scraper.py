"""
Gate.io 期貨上市爬蟲模組
使用 Selenium 進行網頁爬取
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from logger import setup_gate_logger
import asyncio

logger = setup_gate_logger(__name__)


class GateFuturesScraper:
    """Gate.io 期貨上市爬蟲"""

    def __init__(self):
        """初始化爬蟲"""
        self.browser = None
        self.driver = None
        self.history_file = os.path.join("data", "futures_history.json")
        
        # 確保數據目錄存在
        os.makedirs("data", exist_ok=True)

    async def _setup_browser(self):
        """初始化瀏覽器"""
        try:
            logger.info("正在初始化瀏覽器...")
            
            # 配置 Chrome 選項
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-default-browser-check')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-component-update')
            chrome_options.add_argument('--disable-domain-reliability')
            
            # 檢查是否在 Render 環境中
            if os.environ.get('RENDER'):
                logger.info("檢測到 Render 環境，使用容器化瀏覽器設定")
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-setuid-sandbox')
            
            # 設置用戶代理
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36')
            
            # 自動下載和管理 ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # 創建瀏覽器實例
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 設置語言偏好
            self.driver.execute_script("Object.defineProperty(navigator, 'language', {get: function() {return 'zh-TW';}});")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['zh-TW', 'zh', 'en'];}});")
            
            logger.info("瀏覽器初始化完成")
            
        except Exception as e:
            logger.error(f"瀏覽器初始化失敗: {e}")
            raise

    async def scrape_futures_listings(self) -> List[Dict[str, Any]]:
        """爬取期貨上市信息
        
        Returns:
            List[Dict[str, Any]]: 期貨上市信息列表
        """
        try:
            if not self.driver:
                await self._setup_browser()
            
            logger.info("開始訪問頁面: https://www.gate.com/zh-tw/announcements/newfutureslistings")
            
            # 訪問頁面
            self.driver.get("https://www.gate.com/zh-tw/announcements/newfutureslistings")
            
            # 等待頁面加載
            wait = WebDriverWait(self.driver, 20)
            
            # 等待目標選擇器出現
            selector = "a[href*='/announcements/article/']"
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            logger.info("找到目標選擇器")
            
            # 滾動頁面以加載更多內容
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)
            
            # 提取數據
            links = self.driver.find_elements(By.CSS_SELECTOR, selector)
            logger.info(f"找到 {len(links)} 個鏈接元素")
            
            futures_data = []
            for link in links:
                try:
                    title_el = link.find_element(By.CSS_SELECTOR, "p")
                    href = link.get_attribute("href")
                    
                    if title_el and href:
                        title = title_el.text.strip()
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
                                'url': href,
                                'article_id': href.split('/')[-1] if href else '',
                                'language': 'zh' if is_chinese else ('en' if is_english else 'unknown'),
                                'element_type': 'a',
                                'class_name': link.get_attribute('class') or ''
                            })
                            
                except Exception as e:
                    logger.warning(f"處理鏈接時出錯: {e}")
                    continue
            
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

    def get_new_listings(self, futures_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """獲取新的期貨上市信息（與歷史數據比較）
        
        Args:
            futures_data: 當前爬取到的期貨上市列表
            
        Returns:
            List[Dict[str, Any]]: 新的期貨上市信息列表
        """
        try:
            if not os.path.exists(self.history_file):
                logger.info("歷史文件不存在，所有數據都視為新數據")
                return futures_data
            
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
            for item in futures_data:
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
            return futures_data

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

    async def _cleanup(self):
        """清理資源"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("瀏覽器資源清理完成")
        except Exception as e:
            logger.error(f"清理資源時發生錯誤: {e}")

