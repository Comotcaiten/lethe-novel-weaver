import json

class Book:
    def __init__(self, name_book=None, author=None, illustrator=None, volumes=None, cover_url=None, URL=None):
        self.name_book = name_book
        self.author = author
        self.illustrator = illustrator
        self.volumes = volumes
        self.cover_url = cover_url

    def get_name_book(self):
        return self.name_book

    def get_author(self):
        return self.author

    def get_illustrator(self):
        return self.illustrator

    def get_volumes(self):
        return self.volumes

    def get_cover_url(self):
        return self.cover_url

    def get_info_to_dict(self):
        return {
            'name_book': self.name_book,
            'author': self.author,
            'illustrator': self.illustrator,
            'volumes': self.volumes,
            'cover_url': self.cover_url,
        }

    def get_info_to_json(self):
        return json.dumps(self.get_info_to_dict(), indent=4, ensure_ascii=False)

    def set_name_book(self, name):
        self.name_book = name

    def set_author(self, author):
        self.author = author

    def set_illustrator(self, illustrator):
        self.illustrator = illustrator

    def set_volumes(self, volumes):
        self.volumes = volumes

    def set_cover_url(self, cover_url):
        self.cover_url = cover_url