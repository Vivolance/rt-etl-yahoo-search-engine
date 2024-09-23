from enum import Enum


class TextClassification(str, Enum):
    url = "url"
    body = "body"
    date = "date"
