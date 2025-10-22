# epub_exporter.py
from ebooklib import epub
import re
import logging
from typing import Dict, List
from book import Book
from content_crawler import ContentCrawler
import requests

logger = logging.getLogger(__name__)

class EpubExporter:
    def __init__(self, book: Book, author_name: str = "Hako Scraper"):
        self.book = book
        self.author_name = author_name
        self.content_crawler = ContentCrawler()

    def _safe_filename(self, name: str):
        return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_') or "untitled"

    def export(self, output_file: str = "novel.epub"):
        epub_book = epub.EpubBook()
        epub_book.set_identifier(self._safe_filename(self.book.name_book) or "ln-hako")
        epub_book.set_title(self.book.name_book or "Light Novel")
        epub_book.set_language("vi")
        epub_book.add_author(self.book.author or self.author_name)

        if getattr(self.book, "cover_url", None):
                    try:
                        headers = {"User-Agent": "Mozilla/5.0"}
                        resp = requests.get(self.book.cover_url, headers=headers, timeout=10)
                        resp.raise_for_status()

                        cover_item = epub.EpubImage()
                        cover_item.file_name = "images/cover.jpg"
                        cover_item.media_type = "image/jpeg"
                        cover_item.content = resp.content
                        epub_book.add_item(cover_item)

                        # Đặt cover
                        epub_book.set_cover("cover.jpg", resp.content)
                        print(f"✅ Đã thêm ảnh bìa: {self.book.cover_url}")

                    except Exception as e:
                        print(f"⚠️ Không thể tải ảnh bìa: {e}")

        epub_items = []
        img_counter = 1

        for vol_title, chapters in self.book.volumes.items():
            vol_filename = self._safe_filename(vol_title)
            vol_intro = epub.EpubHtml(title=vol_title, file_name=f"{vol_filename}.xhtml", lang="vi")
            vol_intro.content = f"<h1 align='center'>{vol_title}</h1>"
            epub_book.add_item(vol_intro)
            epub_items.append(vol_intro)

            for ch in chapters:
                logger.info("Crawling chapter: %s", ch.get("title"))
                try:
                    data, img_counter = self.content_crawler.crawl_chapter(ch["url"], epub_book, img_counter)
                except Exception as e:
                    logger.warning("Failed to crawl chapter %s: %s", ch.get("url"), e)
                    continue

                safe_name = self._safe_filename(ch.get("title", "chapter"))
                chap = epub.EpubHtml(title=data["title"], file_name=f"{safe_name}.xhtml", lang="vi")
                chap.content = f"<h2 align='center'>{data['title']}</h2>" + data["content"]
                epub_book.add_item(chap)
                epub_items.append(chap)

        epub_book.toc = epub_items
        epub_book.add_item(epub.EpubNcx())
        epub_book.add_item(epub.EpubNav())
        epub_book.spine = ["nav"] + epub_items

        epub.write_epub(output_file, epub_book, {})
        logger.info("Exported EPUB to %s", output_file)
