import argparse
import logging
from metadata_crawler import MetadataCrawler
from epub_exporter import EpubExporter
import sys
import os
import unicodedata
import re

LOG_FMT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

def safe_name(name: str):
    # Chuẩn hoá Unicode (tách dấu ra ký tự gốc)
    nfkd_form = unicodedata.normalize('NFKD', name)
    # Giữ lại ký tự Latin cơ bản + số, bỏ dấu
    ascii_form = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    # Thay ký tự không hợp lệ thành "_"
    safe = re.sub(r'[^a-zA-Z0-9_-]+', '_', ascii_form)
    return safe.strip('_')

def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level, format=LOG_FMT)

def main():
    parser = argparse.ArgumentParser(description="Hako.vn novel -> EPUB")
    parser.add_argument("--url", required=True, help="Truyện URL trên ln.hako.vn")
    parser.add_argument("--out", default=None, help="Tên file epub đầu ra (mặc định: tên truyện).epub")
    parser.add_argument("--debug", action="store_true", help="Bật debug logging")
    args = parser.parse_args()

    setup_logging(logging.DEBUG if args.debug else logging.INFO)
    log = logging.getLogger("main")

    crawler = MetadataCrawler(args.url)

    # ⚠️ Kiểm tra domain hợp lệ
    if not crawler.get_accepted_link():
        log.error("URL không được hỗ trợ: %s", args.url)
        sys.exit(1)  # Thoát hẳn để tránh chạy lỗi sau

    log.info("Crawling metadata from %s", args.url)
    try:
        book = crawler.crawl()
    except Exception as e:
        log.error("Metadata crawling failed: %s", e, exc_info=args.debug)
        sys.exit(1)

    out_name = args.out or (book.name_book.replace(" ", "_") + ".epub")
    exporter = EpubExporter(book)

    output_root = os.path.join(os.path.dirname(__file__), "../lib")

    output_dir = os.path.join(output_root, "hako")
    os.makedirs(output_dir, exist_ok=True)

    # Đặt tên file theo truyện
    out_name = safe_name(book.name_book or "novel") + ".epub"
    out_path = os.path.join(output_dir, out_name)

    try:
        exporter.export(out_path)
        log.info("✅ EPUB saved to: %s", out_path)
    except Exception as e:
        log.error("Export failed: %s", e, exc_info=args.debug)
        sys.exit(2)


if __name__ == "__main__":
    main()