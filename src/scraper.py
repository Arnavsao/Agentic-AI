import asyncio
import time
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from loguru import logger
import aiohttp
from tqdm import tqdm
from config import settings


class GAILWebScraper:
    
    def __init__(self):
        self.base_url = settings.gail_base_url
        self.session = None
        self.visited_urls: Set[str] = set()
        self.scraped_data: List[Dict] = []
        self.headers = {
            'User-Agent': settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        logger.info("GAIL Web Scraper initialized")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=settings.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            blocked_exts = [
                '.pdf', '.zip', '.rar', '.7z',
                '.doc', '.docx', '.xls', '.xlsx', '.csv',
                '.ppt', '.pptx',
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
                '.mp4', '.mp3', '.wav', '.avi', '.mov', '.mkv',
                '.css', '.js'
            ]
            url_low = url.lower()
            return (
                parsed.netloc == urlparse(self.base_url).netloc and
                not any(ext in url_low for ext in blocked_exts) and
                '#' not in url
            )
        except Exception:
            return False
    
    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            if self._is_valid_url(full_url):
                links.append(full_url)
        return links
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Dict:
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No Title"
        
        main_content = soup.find('main') or soup.find('div', class_='content') or soup.find('body')
        content_text = main_content.get_text().strip() if main_content else ""
        
        content_text = ' '.join(content_text.split())
        
        headings = []
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            headings.append({
                'level': heading.name,
                'text': heading.get_text().strip()
            })
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""
        
        images = []
        for img in soup.find_all('img', src=True):
            images.append({
                'src': urljoin(url, img['src']),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        
        return {
            'url': url,
            'title': title_text,
            'content': content_text,
            'description': description,
            'headings': headings,
            'images': images,
            'scraped_at': time.time(),
            'word_count': len(content_text.split())
        }
    
    async def scrape_page(self, url: str) -> Optional[Dict]:
        for attempt in range(settings.max_retries):
            try:
                logger.debug(f"Scraping {url} (attempt {attempt + 1})")
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        ctype = response.headers.get('Content-Type', '')
                        if 'text/html' not in ctype:
                            logger.info(f"Skipping non-HTML content: {url} ({ctype})")
                            return None
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        content = self._extract_content(soup, url)
                        links = self._extract_links(soup, url)
                        content['links'] = links
                        
                        logger.info(f"Successfully scraped {url} - {content['word_count']} words")
                        return content
                    
                    elif response.status == 404:
                        logger.warning(f"Page not found: {url}")
                        return None
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout scraping {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error scraping {url} (attempt {attempt + 1}): {str(e)}")
            
            if attempt < settings.max_retries - 1:
                await asyncio.sleep(settings.request_delay * (attempt + 1))
        
        logger.error(f"Failed to scrape {url} after {settings.max_retries} attempts")
        return None
    
    async def discover_urls(self) -> List[str]:
        logger.info("Starting URL discovery for GAIL website")
        
        urls_to_visit = [self.base_url]
        discovered_urls = set()
        
        while urls_to_visit:
            current_batch = urls_to_visit[:10]
            urls_to_visit = urls_to_visit[10:]
            
            tasks = [self.scrape_page(url) for url in current_batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result:
                    discovered_urls.add(result['url'])
                    for link in result.get('links', []):
                        if link not in discovered_urls and link not in urls_to_visit:
                            urls_to_visit.append(link)
            
            await asyncio.sleep(settings.request_delay)
        
        logger.info(f"Discovered {len(discovered_urls)} URLs")
        return list(discovered_urls)
    
    async def scrape_all(self) -> List[Dict]:
        logger.info("Starting comprehensive scraping of GAIL website")
        
        urls = await self.discover_urls()
        scraped_data = []
        
        with tqdm(total=len(urls), desc="Scraping pages") as pbar:
            for i in range(0, len(urls), 5):
                batch = urls[i:i+5]
                tasks = [self.scrape_page(url) for url in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, dict) and result:
                        scraped_data.append(result)
                    pbar.update(1)
                
                await asyncio.sleep(settings.request_delay)
        
        logger.info(f"Scraping completed. Total pages scraped: {len(scraped_data)}")
        self.scraped_data = scraped_data
        return scraped_data
    
    def save_to_file(self, filename: str = "gail_scraped_data.json"):
        import json
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Scraped data saved to {filename}")


async def main():
    logger.info("Starting GAIL website scraper")
    
    async with GAILWebScraper() as scraper:
        scraped_data = await scraper.scrape_all()
        scraper.save_to_file()
        
        total_words = sum(page['word_count'] for page in scraped_data)
        logger.info(f"Scraping Summary:")
        logger.info(f"- Total pages: {len(scraped_data)}")
        logger.info(f"- Total words: {total_words:,}")
        logger.info(f"- Average words per page: {total_words // len(scraped_data) if scraped_data else 0}")


if __name__ == "__main__":
    asyncio.run(main())
