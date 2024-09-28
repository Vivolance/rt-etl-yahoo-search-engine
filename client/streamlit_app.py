import streamlit as st

from client.models.client_level_data_classes.output.single_search_result import (
    SingleSearchResult,
)
from client.utils.query_service import get_result
from client.utils.screenshot_yahoo_search import take_and_display_screenshot

st.set_page_config(layout="wide")

# Shows a header component
st.header("Yahoo Search Engine - Extracting structured data from search results")

col1, col2 = st.columns(2)

# normalize search term to None if not set / is empty string
if "search_term" not in st.session_state or st.session_state["search_term"] == "":
    st.session_state["search_term"] = None

with col1:
    search_term: str = st.text_input("Query", "Starbucks")
    if st.button("Search"):
        st.session_state["search_term"] = search_term
        take_and_display_screenshot(st.session_state["search_term"])

with col2:
    if st.session_state["search_term"]:
        st.header("Structured Data:")
        results: list[SingleSearchResult] = get_result(
            search_term=st.session_state["search_term"]
        )
        results_dict = [result.model_dump() for result in results]
        st.json(results_dict)
        st.header("Search Results:")
        for result in results:
            # Url (title)
            st.markdown(
                f"<h3 style='margin-bottom:5px;'>{result.url}</h3>",
                unsafe_allow_html=True
            )
            # Date
            st.markdown(
                f"<a href='{result.url}' style='color:green; font-size:14px;'>{result.date}</a>",
                unsafe_allow_html=True
            )
            # Body
            st.markdown(
                f"<p style='font-size:14px; color:#555;'>{result.body}</p>",
                unsafe_allow_html=True
            )
            # Divider
            st.markdown("<hr>", unsafe_allow_html=True)

