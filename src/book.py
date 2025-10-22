import json

class Book:
    def __init__(self, name_book=None, author=None, illustrator=None, volumes=None, URL=None):
        self.name_book = name_book
        self.author = author
        self.illustrator = illustrator
        self.volumes = volumes

    # Phần Get (Đã có sẵn trong yêu cầu của bạn, chỉ để đầy đủ)
    def get_name_book(self):
        return self.name_book

    def get_author(self):
        return self.author

    def get_illustrator(self):
        return self.illustrator

    def get_volumes(self):
        return self.volumes
    
    def get_info_to_dict(self):
        value = {
            'name_book': self.name_book,
            'author': self.author,
            'illustrator': self.illustrator,
            'volumes': self.volumes
        }
        return value
    
    def get_info_to_json(self):
        value = self.get_info_to_dict()
        return json.dumps(value, indent=4, ensure_ascii=False)

    # Phần Set (Setter)
    
    def set_name_book(self, name):
        """Thiết lập tên sách."""
        self.name_book = name
    
    def set_author(self, author):
        """Thiết lập tác giả."""
        self.author = author
    
    def set_illustrator(self, illustrator):
        """Thiết lập họa sĩ minh họa."""
        self.illustrator = illustrator
    
    def set_volumes(self, volumes):
        self.volumes = volumes