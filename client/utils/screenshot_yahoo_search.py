import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import time
import io

from selenium.webdriver.chrome.service import Service
from src.services.yahoo_search_service import YahooSearchService


def take_and_display_screenshot(search_query: str) -> None:
    with st.spinner("Taking screenshot..."):
        # Set up Selenium WebDriver in headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            url = YahooSearchService.create_url(search_query)
            driver.get(url)
            # Wait for the page to load
            time.sleep(3)  # Adjust this delay as needed
            # Adjust the window size to capture the full page
            S = lambda X: driver.execute_script(
                "return document.body.parentNode.scroll" + X
            )
            driver.set_window_size(S("Width"), S("Height"))
            # Take the screenshot
            png = driver.get_screenshot_as_png()
        finally:
            # Close the WebDriver
            driver.quit()

    if png:
        st.image(
            Image.open(io.BytesIO(png)),
            caption="Yahoo Search Results",
            use_column_width=True,
        )
        st.success("Screenshot taken successfully!")
    else:
        st.text("Loading...")
