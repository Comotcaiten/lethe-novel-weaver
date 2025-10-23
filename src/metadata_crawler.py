# metadata_crawler.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from typing import Dict, List
from book import Book
import time
import re

logger = logging.getLogger(__name__)

DEFAULT_BASE = "https://ln.hako.vn"

def is_hako_url(url: str) -> bool:
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    return domain.endswith("ln.hako.vn")

class MetadataCrawler:
    def __init__(self, url: str, base_url: str = DEFAULT_BASE, timeout: int = 10, max_retries: int = 3):
        self.url = url
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.accepted_link = is_hako_url(url)
        if not self.accepted_link:
            raise ValueError(f"URL không hợp lệ: {url} (chỉ chấp nhận domain ln.hako.vn)")
        
    def get_accepted_link(self):
        return self.accepted_link

    def _get(self, url):
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, timeout=self.timeout, headers={"User-Agent":"Mozilla/5.0"})
                resp.raise_for_status()
                return resp
            except Exception as e:
                last_exc = e
                logger.debug("GET %s failed (%s). attempt %d/%d", url, e, attempt, self.max_retries)
                time.sleep(1 * attempt)
        raise last_exc

    def crawl(self) -> Book:        
        resp = self._get(self.url)
        soup = BeautifulSoup(resp.text, "html.parser")

        try:
            name_book = soup.select_one(".series-name").get_text(strip=True)
        except Exception:
            name_book = ""
        
        cover_url = extract_cover_url(soup)
        cover_url = cover_url.replace("i.hako.vn", "i2.hako.vip")
        print(cover_url)

        author = ""
        illustrator = ""
        info = soup.select_one("div.series-information")
        if info:
            for div in info.select("div.info-item"):
                label_tag = div.select_one("span.info-name")
                value_tag = div.select_one("span.info-value")
                if not label_tag or not value_tag:
                    continue
                label = label_tag.get_text(strip=True)
                value = value_tag.get_text(strip=True)
                if "Tác giả" in label:
                    author = value
                elif "Họa sĩ" in label or "Minh họa" in label:
                    illustrator = value

        series_summary = soup.select_one(".series-summary")
        title_summary = f"{series_summary.select_one("h4").get_text()}"
        summary_contents = series_summary.select_one(".summary-content")
        summary_content = []

        for child in summary_contents.children:
            summary_content.append(f"<p>{child.get_text()}</p>")

        # print("title_summary: ", title_summary)
        # print("content_summary: ", summary_content)

        other_fact = []
        other_fact_src = soup.select(".other-facts")
        for fact in other_fact_src:
            # print(fact)
            title_fact = fact.select_one(".fact-name")
            fact_value = fact.select_one(".fact-value")
            fact_content = []
            for content in fact_value.children:
                fact_content.append(f"<div>{content.get_text()}</div>")
            other_fact.append({
                "fact_name": f"{title_fact}",
                "fact_value": fact_content
            })
        
        # print(other_fact)

        section_volume_list = soup.select("section.volume-list")
        logger.info("Found %d volume sections", len(section_volume_list))

        volume_list: Dict[str, List[Dict]] = {}
        for idx, section in enumerate(section_volume_list, start=1):
            vol_title = section.find("span", class_='sect-title').get_text(strip=True) if section.find("h4") else f"Volume {idx}"
            vol_title = f"<Volume> {vol_title}"
            chapters = []
            for a in section.select("ul.list-chapters li a"):
                href = a.get("href")
                if not href:
                    continue
                chapters.append({
                    "title": a.get_text(strip=True),
                    "url": urljoin(self.base_url, href)
                })
            volume_list[vol_title] = chapters

        book = Book(
                name_book=name_book, 
                cover_url=cover_url, 
                author=author, 
                illustrator=illustrator, 
                volumes=volume_list, 
                url=self.url
            )
        
        book.summary_wrapper.series_summary["title"] = title_summary
        book.summary_wrapper.series_summary["summary-content"] = summary_content

        
        book.summary_wrapper.other_facts = other_fact

        # print(book.to_json)
        book.to_json(4)

        return book

def extract_cover_url(soup):
    """Lấy URL ảnh bìa từ trang truyện Hako"""
    cover_div = soup.find("div", class_="volume-cover")
    if not cover_div:
        return None

    # Tìm thẻ div.content.img-in-ratio bên trong
    img_div = cover_div.find("div", class_="content img-in-ratio")
    if not img_div:
        return None

    style = img_div.get("style", "")
    # Dạng style: background-image: url('https://i2.hako.vip/ln/books/covers/...')
    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
    if match:
        return match.group(1)
    
    return None
