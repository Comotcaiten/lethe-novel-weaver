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

        url = self.URL
        res = self.get_requests(url)
        soup = BeautifulSoup(res.text, "html.parser")

        name_book = soup.select(".series-name")[0].get_text(strip=True)

        info = soup.select_one("div.series-information")
        if info:
            for div in info.select("div.info-item"):
                label = div.select_one("span.info-name").get_text(strip=True)
                value = div.select_one("span.info-value").get_text(strip=True)
                if "Tác giả" in label:
                    author = value
                elif "Họa sĩ" in label or "Minh họa" in label:
                    illustrator = value

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
            URL=self.URL
        )

    # -------------------------
    # Crawl nội dung 1 chương dùng Playwright (nội dung render bằng JS/Livewire)
    # -------------------------
    def crawl_chapter(self, ch_url, epub_book, img_counter):
        print(f"  📄 Crawling: {ch_url}")

        html = self.get_html_rendered(ch_url)
        soup = BeautifulSoup(html, "html.parser")

        # Tiêu đề chương
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
                            img_data = requests.get(img_url, headers=headers, timeout=15).content
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
    # Tạo EPUB
    # -------------------------
    def create_epub(self, volume_list, output_file="novel.epub"):
        book = epub.EpubBook()
        book.set_identifier("ln-hako-novel")
        book.set_title(self.book.get_name_book() if self.book else "Light Novel")
        book.set_language("vi")
        if self.book and self.book.get_author():
            book.add_author(self.book.get_author())

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

        epub.write_epub(output_file, book, {})
        print(f"\n✅ Đã tạo file: {output_file}")

    # -------------------------
    # Helpers
    # -------------------------
    def get_requests(self, url):
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print("❌ Không tải được trang chính.")
        return res

    def get_html_rendered(self, url):
        """
        Dùng Playwright để render JavaScript trước khi parse.
        Bắt buộc vì ln.hako.vn dùng Livewire — #chapter-content
        KHÔNG có trong HTML tĩnh, chỉ xuất hiện sau khi JS chạy xong.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            try:
                page.wait_for_function(
                    """
                    () => {
                        const el = document.querySelector('#chapter-content');
                        return el && el.innerText.trim().length > 200;
                    }
                    """,
                    timeout=15000
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
