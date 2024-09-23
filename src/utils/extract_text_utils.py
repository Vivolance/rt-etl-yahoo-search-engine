import logging
from typing import Any

from bs4 import BeautifulSoup, Tag

from src.models.extractor_data_classes.extracted_text import ExtractedText
from src.models.extractor_data_classes.extracted_text_group import ExtractedTextGroup
from src.models.extractor_data_classes.text_classification import TextClassification
from src.utils.get_search_results import get_search_results
from src.utils.logger_utils import setup_logger


def bs4_recursive_extract_text(html_content: str) -> list[ExtractedTextGroup]:
    """
    Assume only search results have "[0-9]+_li"
    """
    extracted_text: list[ExtractedText] = _bs4_recursive_extract_text(html_content)
    current_identifier = ""
    current_group: ExtractedTextGroup | None = None
    all_groups: list[ExtractedTextGroup] = []
    for current_extracted_text in extracted_text:
        # if the tag is not even "0-9_li" continue
        if not current_extracted_text.is_search_result:
            continue
        # Tags each extracted text to categorize it
        identifier: str = current_extracted_text.identifier_tags
        # if different from prev identifier, create new
        if current_identifier != identifier:
            if current_group is not None:
                all_groups.append(current_group)
            current_group = ExtractedTextGroup(identifier)
            current_identifier = identifier
        # categorizes the extracted text into different parts of the search result,
        # such as the date, URL, or body text.
        # QUESTION THIS
        if (
            current_extracted_text.classification == TextClassification.date
            and current_group
            and len(current_group.date) == 0
        ):
            # append to appropriate list within the ExtractedTextGroup
            current_group.date.append(current_extracted_text)
        elif (
            current_group
            and current_extracted_text.classification == TextClassification.url
        ):
            current_group.link.append(current_extracted_text)
        elif current_group:
            current_group.body.append(current_extracted_text)
    # appends the last group
    if current_group is not None:
        all_groups.append(current_group)
    return all_groups


def _bs4_recursive_extract_text(html_content: str) -> list[ExtractedText]:
    """
    Approach 3: Use BS4 with recursion

    Gives the feature of the parent HTMl tags a given str belongs to
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # This function will recursively walk through the soup tree
    def recurse_through_soup(
        soup_element: BeautifulSoup | Tag,
    ) -> list[ExtractedText]:
        texts: list[ExtractedText] = []
        for index, element in enumerate(soup_element.children):
            if isinstance(
                element, str
            ):  # If the element is a NavigableString, capture it
                text: str = element.strip()
                if text:  # Avoid capturing empty or whitespace-only strings
                    texts.append(ExtractedText(parent_tags=["str"], text=text))
            else:  # You can add more tags as needed
                # Recursively process each element and join its texts with a newline
                parent_tag: str = (
                    f"{index}_{element.name}"  # type: ignore[attr-defined]
                    if soup_element.name == "ul" or soup_element.name == "ol"
                    else element.name  # type: ignore[attr-defined]
                )
                # we are sure that the element here is always a Tag, and will have the .children attribute
                # so, we tell mypy to ignore this error
                sub_texts: list[ExtractedText] = recurse_through_soup(element)  # type: ignore[arg-type]
                for sub_text in sub_texts:
                    sub_text.parent_tags.append(parent_tag)
                if sub_texts:
                    texts.extend(sub_texts)
        return texts

    extracted_texts: list[ExtractedText] = recurse_through_soup(soup)
    for extracted_text in extracted_texts:
        extracted_text.parent_tags = list(reversed(extracted_text.parent_tags))

    return extracted_texts


LOGGER: logging.Logger = logging.Logger(__name__)
setup_logger(LOGGER)

if __name__ == "__main__":
    """
    Steps to implement a machine learning feature, or any feature for that matter

    Step 1: Take the project and cut it down into multiple parts
    Step 2: Isolate the most difficult part of the project
    - The most difficult part here, is cleaning the HTML on behalf of the user
    Step 3: Come up with possible approaches for the implementation

    Approach 1: Use a HTML Parser, no ML. Brute force the HTMl and come up with a hard-coded HTMl parser
    - This is not great; it breaks once yahoo or google changes it's HTML layout

    Approach 2: Use a bazooka to kill the ant. Send the whole payload into ChatGPT3.5 and make it extract it
    - This is still not great; ChatGPT3.5 API costs a sub-cent per call

    Approach 3: Using Classical Machine Learning / Simpler Deep Learning
    - We transform the data into features ourselves, the same features ChatGPT would have learnt by itself
    - No choice, as using a more stupid model means we have to make the task easy for it right?

    Features:
    - text -> tokens (tokens are like sub-words, elephant -> ele phant, 2 tokens)
    - convert tokens into vectors; these vectors represent the meaning behind the word

    spacy has 3 models
    - en-core-web-sm -> smallest model, Convolutional neural network small
        - small model is light in RAM usage, and very fast
    - en-core-web-lg -> larger model, Convolutional neural network
        - recommended default, and it's a good balance between speed and quality
    - en-core-web-trf -> one of the larger models, Transformer
        - performs better than en-core-web-lg, but slower
    """
    results: dict[str, Any] = get_search_results("tesla earning reports")
    print(f"Results: {results}")
    # nlp: Language = spacy.load("en_core_web_lg")
    yahoo_html: str = results["result"]
    """
    Step 1: Convert HTML into Text + HTML
    - If we pass each segment into bs4_extract_text at a time, it might be better
    - Having both text and HTML versions gives you flexibility in how you handle and manipulate 
    the data. You can work with the text version for analysis or display purposes, while still 
    having access to the original HTML for tasks like reformatting, re-parsing, or extracting 
    additional information.
    """
    raw_text: list[ExtractedTextGroup] = bs4_recursive_extract_text(yahoo_html)

    for single_result in raw_text:
        LOGGER.info("=====")
        LOGGER.info(single_result)
