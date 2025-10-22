import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from urllib.parse import urljoin
import re
from book import Book
import json

class Crawl:
  def __init__(self, URL):
    self.URL = URL
    self.book = None
    self.BASE_URL = "https://ln.hako.vn"
    pass

  def crawl_book(self):
    name_book = ''
    author = ''
    illustrator = ''
    volume_list = {}
    section_volume_list = None
    
    url = self.URL
    
    res = self.get_requests(url)
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Khối thông tin chi tiết của tiểu 
    # Tên tiểu thuyết
    name_book = soup.select(".series-name")[0].get_text(strip=True)
    # Lọc lấy các thông tin như tác giả, hoạ sĩ, ....
    info = soup.select_one("div.series-information")
    if info:
        for div in info.select("div.info-item"):
            label = div.select_one("span.info-name").get_text(strip=True)
            value = div.select_one("span.info-value").get_text(strip=True)
            if "Tác giả" in label:
                author = value
            elif "Họa sĩ" in label or "Minh họa" in label:
                illustrator = value
            # Có thể mở rộng thêm
            elif "Tình trạng" in label:
                continue
            
    # Lấy các section/volume chứa các chương của tiểu thuyết
    section_volume_list = soup.select("section.volume-list")
    print(f"📖 Tìm thấy {len(section_volume_list)} volume section.\n")

    for idx, section in enumerate(section_volume_list, 1):
        vol_title = section.find("span", class_='sect-title').get_text(strip=True) if section.find("h4") else f"Volume {idx}"
        vol_title = f"<Volume> {vol_title}"
        chapters = []
        for ch in section.select("ul.list-chapters li a"):
            chapters.append({
                "title": ch.get_text(strip=True),
                "url": urljoin(self.BASE_URL, ch["href"])
            })
        volume_list[vol_title] = chapters
    
    # print(json.dumps(volume_list, indent=4, ensure_ascii=False))
    
    self.book = Book(name_book=name_book, author=author, illustrator=illustrator, volumes=volume_list, URL=self.URL)
    return

  # -------------------------
  # Hàm crawl nội dung 1 chương + nhúng ảnh
  # -------------------------
  def crawl_chapter(self, ch_url, book, img_counter):
      
      res = self.get_requests(ch_url)
      soup = BeautifulSoup(res.text, "html.parser")

      title_tag = soup.select_one("h4.title-item")
      title = title_tag.get_text(strip=True) if title_tag else "Không có tiêu đề"

      content_block = soup.select_one("div#chapter-content")
      html_parts = []

      if content_block:
          for child in content_block.children:
              if child.name in ["p", "div", "span"]:
                  imgs = child.find_all("img")
                  if imgs:
                      for img in imgs:
                          img_url = urljoin(self.BASE_URL, img.get("src"))

                          # ✅ Fix domain
                          img_url = img_url.replace("i.hako.vn", "i2.hako.vip")

                          print("➡️ Ảnh:", img_url)  # debug

                          try:
                              # ✅ Thêm Referer header
                              headers = {
                                  "User-Agent": "Mozilla/5.0",
                                  "Referer": ch_url
                              }
                              img_data = requests.get(img_url, headers=headers).content
                              img_name = f"image_{img_counter}.jpg"
                              img_counter += 1

                              # Nhúng ảnh
                              img_item = epub.EpubImage()
                              img_item.file_name = f"images/{img_name}"
                              img_item.media_type = "image/jpeg"
                              img_item.content = img_data
                              book.add_item(img_item)

                              html_parts.append(
                                  f'<div style="text-align:center;"><img src="images/{img_name}" alt="Ảnh minh họa"/></div>'
                              )
                          except Exception as e:
                              html_parts.append(f"<p>[Không tải được ảnh: {img_url}]</p>")
                  else:
                      text = child.get_text(strip=True)
                      if text:
                          html_parts.append(f"<p>{text}</p>")

      return {
          "title": title,
          "content": "\n".join(html_parts)
      }, img_counter

  # -------------------------
  # Tạo EPUB
  # -------------------------
  def create_epub(self, volume_list, output_file="novel.epub"):
      book = epub.EpubBook()
      book.set_identifier("ln-hako-demo")
      book.set_title("Light Novel Hako")
      book.set_language("vi")
      book.add_author("Hako Scraper")

      epub_chapters = []
      img_counter = 1

      for vol, chapters in volume_list.items():
          vol_filename = re.sub(r'[^a-zA-Z0-9]+', '_', vol)
          vol_intro = epub.EpubHtml(title=vol, file_name=f"{vol_filename}.xhtml", lang="vi")
          vol_intro.content = f"<h1>{vol}</h1>"
          book.add_item(vol_intro)
          epub_chapters.append(vol_intro)

          for ch in chapters:
              print(f"➡️ Crawl {vol} -> {ch['title']}")
              data, img_counter = self.crawl_chapter(ch["url"], book, img_counter)
              if not data:
                  continue

              safe_chapter_name = re.sub(r'[^a-zA-Z0-9]+', '_', ch['title'])
              c = epub.EpubHtml(
                  title=data["title"],
                  file_name=f"{safe_chapter_name}.xhtml",
                  lang="vi"
              )
              c.content = f"<h2>{data['title']}</h2>" + data["content"]
              book.add_item(c)
              epub_chapters.append(c)

      # Mục lục
      book.toc = epub_chapters
      book.add_item(epub.EpubNcx())
      book.add_item(epub.EpubNav())

      # Spine (thứ tự đọc)
      book.spine = ["nav"] + epub_chapters

      epub.write_epub(output_file, book, {})
      print(f"✅ Đã tạo file {output_file}")


  def get_requests(self, url):
    res = requests.get(url)
    if res.status_code != 200:
        print("❌ Không tải được trang chính.")
        return {}
    return res
  
  def get_book(self):
     return self.book
  
  def start(self):
      self.crawl_book()
      self.create_epub(self.book.volumes, self.book.name_book)
      