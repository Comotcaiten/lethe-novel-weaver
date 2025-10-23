# book.py
from dataclasses import dataclass, field, asdict
from typing import Dict, List
import json

@dataclass
class Summary:
    series_summary: Dict[str, str] = field(default_factory=lambda: {
        "title": "",
        "summary-content": List[str]
    })
    other_facts: List[Dict[str, List[str]]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

@dataclass
class Book:
    name_book: str = ""
    author: str = ""
    illustrator: str = ""
    volumes: Dict[str, List[Dict]] = field(default_factory=dict)
    url: str = ""
    cover_url: str = ""
    summary_wrapper: Summary = field(default_factory=Summary) 

    def to_dict(self):
        result = asdict(self)
        result["summary_wrapper"] = self.summary_wrapper.to_dict()
        return result

    def to_json(self, indent=4):
        result = json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
        return result

    def save_json(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
