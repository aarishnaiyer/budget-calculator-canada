import pytest
from playwright.sync_api import sync_playwright


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: quick sanity checks")
    config.addinivalue_line("markers", "calculation: math and output correctness")
    config.addinivalue_line("markers", "ui: visual and layout tests")
    config.addinivalue_line("markers", "edge_case: boundary and unusual inputs")


# fresh browser for every test so they cant affect each other
@pytest.fixture(scope="function")
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        pg = context.new_page()
        yield pg
        context.close()
        browser.quit()
