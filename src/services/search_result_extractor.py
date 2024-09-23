from src.models.extractor_data_classes.extracted_search_result import (
    ExtractedSearchResult,
)
from src.models.extractor_data_classes.extracted_text_group import ExtractedTextGroup
from src.services.abstract_extractor import SearchResultExtractor
from src.utils.extract_text_utils import bs4_recursive_extract_text


class BS4SearchResultExtractor(SearchResultExtractor):
    """
    Approach 1: BS4 HTML traversal (Non-ML)
    Use BS4 to traverse HTML as a tree
    - Recursively traverse the HTML, saving the parent tags of each HTML component

    Assume Search Results from Yahoo always appears in a <ul> or <ol>
    - Each component within the same <li> are a single search result
    - Search results have at least a body + date; filter out those that don't
    """

    def extract(self, html: str, user_id: str) -> list[ExtractedSearchResult]:
        unfiltered_group: list[ExtractedTextGroup] = bs4_recursive_extract_text(html)
        filtered_group: list[ExtractedTextGroup] = [
            # for any group with >= 2 header, append it
            group
            for group in unfiltered_group
            if group.information_count >= 2
        ]
        # Changing from list[ExtractedTextGroup] to list[ExtractedSearchResult]
        extracted_search_results: list[ExtractedSearchResult] = [
            ExtractedSearchResult.from_extracted_text_group(user_id, group)
            for group in filtered_group
        ]
        return extracted_search_results
