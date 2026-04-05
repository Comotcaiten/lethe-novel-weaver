import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from urllib.parse import urljoin
import re
from book import Book
import json

from playwright.sync_api import sync_playwright

class Crawl:
    def __init__(self, URL):
        self.URL = URL
        self.book = None
        self.BASE_URL = "https://ln.hako.vn"

    def crawl_book(self):
        name_book = ''
        author = ''
        illustrator = ''
        volume_list = {}
        cover_url = None

        url = self.URL
        res = self.get_requests(url)
        soup = BeautifulSoup(res.text, "html.parser")

        # Tên tiểu thuyết
        name_book = soup.select(".series-name")[0].get_text(strip=True)

        # ── Lấy ảnh bìa ──────────────────────────────────────────────
        # Ưu tiên 1: thẻ <div class="img-in-ratio"> với data-bg hoặc style background
        cover_tag = soup.select_one(".img-in-ratio")
        if cover_tag:
            cover_url = (
                cover_tag.get("data-bg")
                or cover_tag.get("data-src")
                or cover_tag.get("data-lazy-bg")
            )
            if not cover_url:
                # fallback: parse inline style="background-image: url(...)"
                style = cover_tag.get("style", "")
                m = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                if m:
                    cover_url = m.group(1)

        # Ưu tiên 2: og:image meta tag (luôn có và đáng tin cậy)
        if not cover_url:
            og = soup.select_one('meta[property="og:image"]')
            if og:
                cover_url = og.get("content")

        # Chuẩn hoá URL
        if cover_url:
            cover_url = urljoin(self.BASE_URL, cover_url)
            cover_url = cover_url.replace("i.hako.vn", "i2.hako.vip")
            print(f"🖼️  Bìa tìm thấy: {cover_url}")
        else:
            print("⚠️  Không tìm thấy ảnh bìa.")

        # Tác giả, hoạ sĩ
        info = soup.select_one("div.series-information")
        if info:
            for div in info.select("div.info-item"):
                label = div.select_one("span.info-name").get_text(strip=True)
                value = div.select_one("span.info-value").get_text(strip=True)
                if "Tác giả" in label:
                    author = value
                elif "Họa sĩ" in label or "Minh họa" in label:
                    illustrator = value

        # Volume / chương
        section_volume_list = soup.select("section.volume-list")
        print(f"📖 Tìm thấy {len(section_volume_list)} volume section.\n")

        for idx, section in enumerate(section_volume_list, 1):
            vol_title_tag = section.find("span", class_='sect-title')
            vol_title = vol_title_tag.get_text(strip=True) if vol_title_tag else f"Volume {idx}"
            vol_title = f"<Volume> {vol_title}"
            chapters = []
            for ch in section.select("ul.list-chapters li a"):
                chapters.append({
                    "title": ch.get_text(strip=True),
                    "url": urljoin(self.BASE_URL, ch["href"])
                })
            volume_list[vol_title] = chapters

        self.book = Book(
            name_book=name_book,
            author=author,
            illustrator=illustrator,
            volumes=volume_list,
            cover_url=cover_url,
            URL=self.URL
        )

    # -------------------------
    # Crawl nội dung 1 chương (Playwright vì Livewire render JS)
    # -------------------------
    def crawl_chapter(self, ch_url, epub_book, img_counter):
        print(f"  📄 Crawling: {ch_url}")

        html = self.get_html_rendered(ch_url)
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.select_one("h4.title-item") or soup.select_one("h1.chapter-title")
        title = title_tag.get_text(strip=True) if title_tag else "Không có tiêu đề"

        content_block = soup.select_one("div#chapter-content")
        if not content_block:
            print(f"  ⚠️  Không tìm thấy #chapter-content tại {ch_url}")
            return None, img_counter

        html_parts = []
        for child in content_block.children:
            if not hasattr(child, 'name') or child.name is None:
                text = str(child).strip()
                if text:
                    html_parts.append(f"<p>{text}</p>")
                continue

            if child.name in ["p", "div", "span"]:
                imgs = child.find_all("img")
                if imgs:
                    for img in imgs:
                        img_url = img.get("src") or img.get("data-src", "")
                        if not img_url:
                            continue
                        img_url = urljoin(self.BASE_URL, img_url)
                        img_url = img_url.replace("i.hako.vn", "i2.hako.vip")
                        print(f"  🖼️  Ảnh: {img_url}")
                        try:
                            headers = {"User-Agent": "Mozilla/5.0", "Referer": ch_url}
                            img_data = requests.get(img_url, headers=headers, timeout=120).content
                            img_name = f"image_{img_counter}.jpg"
                            img_counter += 1
                            img_item = epub.EpubImage()
                            img_item.file_name = f"images/{img_name}"
                            img_item.media_type = "image/jpeg"
                            img_item.content = img_data
                            epub_book.add_item(img_item)
                            html_parts.append(
                                f'<div style="text-align:center;"><img src="images/{img_name}" alt="Ảnh"/></div>'
                            )
                        except Exception as e:
                            print(f"  ❌ Không tải được ảnh: {e}")
                            html_parts.append(f"<p>[Không tải được ảnh: {img_url}]</p>")
                else:
                    text = child.get_text(strip=True)
                    if text:
                        html_parts.append(f"<p>{text}</p>")

        return {"title": title, "content": "\n".join(html_parts)}, img_counter

    # -------------------------
    # Tạo EPUB (kèm ảnh bìa)
    # -------------------------
    def create_epub(self, volume_list, output_file="novel.epub"):
        book = epub.EpubBook()
        book.set_identifier("ln-hako-novel")
        book.set_title(self.book.get_name_book() if self.book else "Light Novel")
        book.set_language("vi")
        if self.book and self.book.get_author():
            book.add_author(self.book.get_author())

        # ── Đặt ảnh bìa ──────────────────────────────────────────────
        cover_url = self.book.get_cover_url() if self.book else None
        if cover_url:
            try:
                headers = {"User-Agent": "Mozilla/5.0", "Referer": self.BASE_URL}
                cover_data = requests.get(cover_url, headers=headers, timeout=120).content

                # Xác định đuôi file từ URL
                ext = cover_url.split("?")[0].rsplit(".", 1)[-1].lower()
                mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                            "png": "image/png", "webp": "image/webp"}
                mime = mime_map.get(ext, "image/jpeg")
                cover_filename = f"cover.{ext}"

                book.set_cover(cover_filename, cover_data, create_page=True)
                print(f"✅ Đã đặt ảnh bìa: {cover_filename} ({mime})")
            except Exception as e:
                print(f"⚠️  Không tải được ảnh bìa: {e}")
        else:
            print("⚠️  Bỏ qua bìa (không có URL).")

        epub_chapters = []
        img_counter = 1

        for vol, chapters in volume_list.items():
            print(f"\n📦 Volume: {vol}")
            vol_filename = re.sub(r'[^a-zA-Z0-9]+', '_', vol)
            vol_intro = epub.EpubHtml(title=vol, file_name=f"{vol_filename}.xhtml", lang="vi")
            vol_intro.content = f"<h1>{vol}</h1>"
            book.add_item(vol_intro)
            epub_chapters.append(vol_intro)

            for ch in chapters:
                print(f"  ➡️  {ch['title']}")
                data, img_counter = self.crawl_chapter(ch["url"], book, img_counter)
                if not data:
                    continue

                safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', ch['title'])
                c = epub.EpubHtml(
                    title=data["title"],
                    file_name=f"{safe_name}.xhtml",
                    lang="vi"
                )
                c.content = f"<h2>{data['title']}</h2>\n" + data["content"]
                book.add_item(c)
                epub_chapters.append(c)

        book.toc = epub_chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav"] + epub_chapters
        
        direction = "/lib/hako/"

        epub.write_epub(direction + output_file, book, {})
        print(f"\n✅ Đã tạo file: {output_file}")

    # -------------------------
    # Helpers
    # -------------------------
    def get_requests(self, url):
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print("❌ Không tải được trang.")
        return res

    def get_html_rendered(self, url):
        """
        Playwright để lấy HTML sau khi JS render xong.
        Bắt buộc với trang chương vì dùng Livewire.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=120000)
            try:
                page.wait_for_function(
                    """
                    () => {
                        const el = document.querySelector('#chapter-content');
                        return el && el.innerText.trim().length > 200;
                    }
                    """,
                    timeout=120000
                )
            except Exception as e:
                print(f"  ⚠️  Timeout khi chờ #chapter-content: {e}")
            html = page.content()
            browser.close()
            return html

    def get_book(self):
        return self.book

    def start(self):
        self.crawl_book()
        output_name = (self.book.name_book + ".epub") if self.book else "novel.epub"
        self.create_epub(self.book.volumes, output_name)