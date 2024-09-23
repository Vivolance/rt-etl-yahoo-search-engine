from dataclasses import dataclass, field

from src.models.extractor_data_classes.extracted_text import ExtractedText


@dataclass
class ExtractedTextGroup:
    """
    Represents a candidate SingleSearchResult
    This data class is implemented using @dataclass decorator
    """

    identifier: str
    link: list[ExtractedText] = field(default_factory=list)
    body: list[ExtractedText] = field(default_factory=list)
    date: list[ExtractedText] = field(default_factory=list)

    @property
    def link_str(self) -> str:
        return " ".join([current_link.text for current_link in self.link])

    @property
    def body_str(self) -> str:
        return " ".join([current_link.text for current_link in self.body])

    @property
    def date_str(self) -> str:
        return " ".join([current_link.text for current_link in self.date])

    @property
    def information_count(self) -> int:
        """
        Number of link, body, and date present
        Number from 0 to 3
        """
        information_count: int = 0
        if self.link:
            information_count += 1
        if self.body:
            information_count += 1
        if self.date:
            information_count += 1
        return information_count

    def __str__(self) -> str:
        return f"Identifier: {self.identifier}\n\nDate: {self.date_str}\n\nLink: {self.link_str}\n\nBody: {self.body_str}\n\n"
