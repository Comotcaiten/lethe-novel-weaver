from book import Book
from crawl_hako import Crawl

from datasets import datasets_genderbender
# -------------------------
# Main
# -------------------------

datasets = [
    # "https://ln.hako.vn/ai-dich/24372-con-dien-o-cai-vo-lam-nay-la-tao-day",
    # "https://ln.hako.vn/truyen/25135-idol-toi-phu-trach-bi-lo-chuyen-hen-ho-nhung-ma-chang-he-han-gi-het-vi-doi-phuong-la-toi-co-quan-ly-dang-gia-trai-ma",
    # "https://ln.hako.vn/ai-dich/22016-thien-than-sieu-cap-lac-quan-se-phu-trach-cham-soc-tinh-than-cho-ma-phap-thieu-nu",
    # "https://ln.hako.vn/truyen/17578-du-cac-nguoi-co-goi-ta-ve-long-hay-khong-ta-van-se-di-ngu",
    # "https://ln.hako.vn/ai-dich/24168-du-cac-nguoi-co-tha-goi-ta-la-ve-long-hay-gi-di-nua-thi-ta-van-se-di-ngu",
    # "https://ln.hako.vn/ai-dich/25266-the-gioi-gia-toc",
    # "https://ln.hako.vn/truyen/24945-quai-vat-cap-tai-uong-muon-duoc-rong-choi",
    # "https://ln.hako.vn/truyen/25627-top-stars-want-to-possess-me",
    # "https://ln.hako.vn/truyen/20337-the-societys-pet-daughter",
    # "https://ln.hako.vn/ai-dich/24249-phi-thuy-chi-kiem",
    # "https://ln.hako.vn/ai-dich/25503-chu-tich-bay-tuoi",
    # "https://ln.hako.vn/ai-dich/20177-tro-thanh-phu-thuy-trong-the-gioi-tran-ngap-ma-quai",
    # "https://ln.hako.vn/truyen/25043-xuyen-thanh-mot-nu-phu-phan-dien-toi-da-tro-thanh-mot-loli-yandere",
    # "https://ln.hako.vn/ai-dich/25779-cai-tao-ac-nu",
    # "https://ln.hako.vn/ai-dich/22448-ac-tam-trong-co-nang-khong-gioi-han",
    # "https://ln.hako.vn/ai-dich/23607-nhung-nu-chinh-truyen-ma-am-anh-toi",
    # "https://ln.hako.vn/truyen/19092-dai-nana-maouji-jirubagiasu-no-maou-keikoku-ki",
    #
    # # to much
    # "https://ln.hako.vn/truyen/22136-man-cap-xuyen-khong-tai-sao-toi-lai-thanh-tieu-thu-muc-su-chu",
    
    "https://ln.hako.vn/ai-dich/19723-ky-si-da-tai-sinh-thanh-ho-ly-nho",
    "https://ln.hako.vn/truyen/11815-orc-eiyuu-monogatari-sontaku-retsuden",
    "https://ln.hako.vn/truyen/8377-orc-eiyuu-monogatari-sontaku-retsuden",
    "https://ln.hako.vn/truyen/19270-orc-eiyuu-monogatari-sontaku-retsuden",
    "https://ln.hako.vn/truyen/14347-magical-girl-tyrant-sylph",
    "https://ln.hako.vn/truyen/18111-nichiasa-reincarnation-ve-chuyen-mot-otaku-cuong-sieu-anh-hung-bi-chuyen-sinh-thanh-nhan-vat-phan-dien",
    "https://ln.hako.vn/truyen/19027-tieu-thu-bang-gia-chuyen-sinh-khong-muon-ai-den-gan",
    "https://ln.hako.vn/truyen/20733-shangri-la-frontier-kusoge-hunter-kamige-ni-idoman-to-su",
    "https://ln.hako.vn/ai-dich/20396-thieu-gia-hung-ac-sao-co-the-la-thanh-nu",
    "https://ln.hako.vn/ai-dich/21454-watashi-ga-koibito-ni-nareru-wakenaijan-muri-muri-muri-janakatta",
    "https://ln.hako.vn/truyen/20291-chi-minh-chong-tuong-lai-moi-khien-co-ay-tro-nen-dang-yeu",
    "https://ln.hako.vn/ai-dich/24129-sau-khi-tai-sinh-toi-tro-thanh-bach-nguyet-quang-cua-co-ban-thanh-mai",
    "https://ln.hako.vn/ai-dich/25239-trung-sinh-roi-moi-phat-hien-minh-co-thanh-mai",
    "https://ln.hako.vn/truyen/21593-soi-va-gia-vi-spring-log",
    "https://ln.hako.vn/ai-dich/25543-nu-vo-su-toc-hong-khon-kiep-cua-hoc-vien",
    "https://ln.hako.vn/ai-dich/25077-he-thong-ta-khong-lam-thanh-nu-nua-dau",
    "https://ln.hako.vn/truyen/11045-adachi-to-shimamura",
    "https://ln.hako.vn/ai-dich/25189-ma-vuong-bai-lan-moi-khong-dung-phai-kiem-thanh-nghi-huu",
    "https://ln.hako.vn/truyen/24840-kaguya-cong-chua-vu-tru",
    "https://ln.hako.vn/ai-dich/22463-yuri-tama-from-third-wheel-to-trifecta",
    "https://ln.hako.vn/ai-dich/24718-nuoi-nang-bach-tuyet",
    "https://ln.hako.vn/ai-dich/24311-loli-phan-dien-nay-qua-yeu-nen-lam-on-dung-bat-nat-toi-co-yandere",
    "https://ln.hako.vn/truyen/1275-the-reincarnated-vampire-wants-an-afternoon-nap",
    "https://ln.hako.vn/ai-dich/14068-tensei-oujo-to-tensai-reijou-no-mahou-kakumei",
    "https://ln.hako.vn/ai-dich/23020-chuyen-sinh-thanh-nam-phu-toi-van-se-khong-tu-bo-giac-mo-lam-my-nu",
    "https://ln.hako.vn/truyen/4657-watashi-no-oshi-wa-akuyaku-reijou",
    "https://ln.hako.vn/truyen/18547-toi-yeu-nu-phan-dien",
    "https://ln.hako.vn/truyen/7401-bishoujo-ni-natta-kedo-netoge-haijin-yattemasu",
    "https://ln.hako.vn/truyen/24045-phap-su-thien-tai-cua-khu-binh-luan",
    "https://ln.hako.vn/ai-dich/25497-anh-trai-em-la-ma-phap-thieu-nu-thi-co-van-de-gi-sao",
]

if __name__ == "__main__":
    # URL = "https://ln.hako.vn/truyen/23373-nguoi-tro-chuyen-thau-dem-voi-thang-it-noi-nhu-toi-lai-la-nu-than-hoan-hao-nhat-lop"
    for url in datasets_genderbender:
        crawl = Crawl(url)
        crawl.start()
