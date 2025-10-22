# book.py
from dataclasses import dataclass, field, asdict
from typing import Dict, List
import json

@dataclass
class Book:
    name_book: str = ""
    author: str = ""
    illustrator: str = ""
    volumes: Dict[str, List[Dict]] = field(default_factory=dict)
    url: str = ""
    cover_url: str = ""

    def to_dict(self):
        return asdict(self)

    def to_json(self, indent=4):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def save_json(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
