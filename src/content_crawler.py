# content_crawler.py
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from urllib.parse import urljoin
import re
import logging
import time
from typing import Tuple

logger = logging.getLogger(__name__)

class ContentCrawler:
    def __init__(self, base_url="https://ln.hako.vn", timeout=10, max_retries=3, referer_header=True):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.referer_header = referer_header

    def _get(self, url: str):
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, timeout=self.timeout, headers=headers)
                resp.raise_for_status()
                return resp
            except Exception as e:
                last_exc = e
                logger.debug("GET %s failed: %s (attempt %d/%d)", url, e, attempt, self.max_retries)
                time.sleep(1 * attempt)
        raise last_exc

    def crawl_chapter(self, ch_url: str, epub_book: epub.EpubBook, img_counter: int = 1) -> Tuple[dict, int]:
        """Return dict {title, content_html} and updated img_counter"""
        resp = self._get(ch_url)
        soup = BeautifulSoup(resp.text, "html.parser")

        title_tag = soup.select_one("h4.title-item")
        title = title_tag.get_text(strip=True) if title_tag else "Không có tiêu đề"
        # title = 

        content_block = soup.select_one("div#chapter-content")
        html_parts = []
        if content_block:
            for child in content_block.children:
                # Bỏ qua text node và các node không phải tag
                if not hasattr(child, "name"):
                    continue

                # Chỉ xử lý các tag hợp lệ (p, div, span)
                if child.name not in ["p", "div", "span"]:
                    continue

                # Tìm ảnh bên trong <p> / <div> / <span>
                imgs = child.find_all("img", recursive=False)  # chỉ tìm ảnh cấp 1, không lồng sâu
                if imgs:
                    for img in imgs:
                        src = img.get("src") or img.get("data-src") or ""
                        if not src:
                            continue

                        # Bỏ qua ảnh có đường dẫn ngoài hoặc icon hệ thống
                        if "hako.vn" not in src and not src.startswith("http"):
                            continue

                        img_url = urljoin(self.base_url, src)
                        img_url = img_url.replace("i.hako.vn", "i2.hako.vip")

                        try:
                            headers = {"User-Agent": "Mozilla/5.0", "Referer": ch_url}
                            img_resp = requests.get(img_url, headers=headers, timeout=self.timeout)
                            img_resp.raise_for_status()

                            img_name = f"image_{img_counter}.jpg"
                            img_counter += 1

                            img_item = epub.EpubImage()
                            img_item.file_name = f"images/{img_name}"
                            img_item.media_type = "image/jpeg"
                            img_item.content = img_resp.content
                            epub_book.add_item(img_item)

                            html_parts.append(
                                f'<div style="text-align:center;"><img src="images/{img_name}" alt=""/></div>'
                            )
                        except Exception as e:
                            logger.warning("⚠️ Không tải được ảnh: %s (%s)", img_url, e)
                            html_parts.append(f'<p>[Không tải được ảnh: {img_url}]</p>')

                    # Nếu thẻ <p> đó có text sau ảnh (ví dụ: <p><img ...> ảnh bìa</p>)
                    text_after_img = child.get_text(strip=True)
                    if text_after_img:
                        html_parts.append(f"<p>{text_after_img}</p>")

                else:
                    # Không có ảnh => xử lý text bình thường
                    # print(child)
                    text = child.get_text(strip=True)
                    if text:
                        html_parts.append(f"<p>{text}</p>")

        return {"title": title, "content": "\n".join(html_parts)}, img_counter
