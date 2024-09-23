from dataclasses import dataclass
import re

from src.models.extractor_data_classes.text_classification import TextClassification

"""
Improvements: Can be improve using spacy's name entity recognition. It is capable to
determining if a unclassified text is a header, url or a date.

import spacy

model = spacy.load("en_core_web_lg")
text: str = "YOUR EXTRACTED TEXT FROM BS4"
tokenized: Doc = model.nlp(text)

classification: Classification | None = None
for item in doc:
    ner: spacy.Label = item.label_
    if ner == spacy.Label.Date:
        # classify as date
        classification = classification.Date
        break
    elif ner == spacy.Label.URL:
        # classify as url
        classification = classification.URL

if classification is None:
    classification = Classification.BODY
"""

DATE_PATTERN: re.Pattern = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s\d{1,2},\s\d{4}\b"
)
LI_PATTERN: re.Pattern = re.compile(r"[0-9]+_li")
URL_PATTERN: re.Pattern = re.compile(
    r"\b(?:www\.)?[\w-]+\.(?:[\w-]+\.)?[a-zA-Z]{2,6}\b"
)


@dataclass
class ExtractedText:
    """
    Intermediate raw text (unclassified), from the HTML
    - This can be a body, header, or date

    (<WE ARE HERE> ExtractedText) -> (ExtractedTextGroup) -> (ExtractedSearchResult)

    Extraction process
    1. From RAW HTML -> Extract only text, ignore the html (ExtractedText)
    - We do this by recursively traversing the HTML as a tree
    - Get all <p> / <span> components containing strings -> text: str
    - The parent components of this <p> / <span> is in parent_tags list[str]
        - This is a key feature, to decide which extracted text should be grouped together

    2. Grouping ExtractedText together by search result -> ExtractedTextGroup
    - 1 header, 1 body, 1 date in each search result
    - We assume all <li> components in a <ul> / <ol> is a single search result

    3. Filter for only search results (ExtractedTextGroup), and classify ExtractedText
    as header, body, or date -> ExtractedSearchResult
    - We assume ExtractedTextGroup with at least 2 components (header, url, date)
    is a search result (PS: you can miss out false negative)
    - We classify text using regex + smart string search heuristic

    4. Return the final transformed type ExtractedTextGroup
    """

    parent_tags: list[str]
    text: str

    @property
    def is_search_result(self) -> bool:
        """
        Assume only search results have "[0-9]+_li" in them
        """
        for tag in self.parent_tags:
            if LI_PATTERN.match(tag):
                return True
        return False

    @property
    def identifier_tags(self) -> str:
        """
        Represents the identifier of the extractedpip3  text
        Text of the same identifier tags are of the same search result

        All tags before and including "[0-9]+_li" is part of the identifier tag
        :return: E.G "html-body-div-div-div-div-div-div-div-div-ul-1_li"
        """
        identifier_tags: list[str] = []
        for tag in self.parent_tags:
            identifier_tags.append(tag)
            if LI_PATTERN.match(tag):
                break
        return "-".join(identifier_tags)

    @property
    def is_date(self) -> bool:
        return DATE_PATTERN.search(self.text) is not None

    @property
    def is_url(self) -> bool:
        return URL_PATTERN.search(self.text) is not None or "› " in self.text

    @property
    def classification(self) -> TextClassification:
        if self.is_date:
            return TextClassification.date
        elif self.is_url:
            return TextClassification.url
        else:
            return TextClassification.body
