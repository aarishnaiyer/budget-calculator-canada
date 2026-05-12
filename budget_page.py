from playwright.sync_api import Page, expect


class BudgetPage:
    URL = "http://localhost:8501"

    def __init__(self, page: Page):
        self.page = page

    def load(self):
        self.page.goto(self.URL)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_selector('[data-testid="stInfo"]', timeout=10000)  # banner is last thing to render

    def click_tab(self, name: str):
        self.page.get_by_role("tab", name=name).click()
        self.page.wait_for_timeout(800)  # streamlit reruns on tab switch

    # reading metric cards — streamlit renders them as stMetricLabel + stMetricValue pairs
    def get_metric(self, label: str) -> float | None:
        labels = self.page.locator('[data-testid="stMetricLabel"] p').all()
        values = self.page.locator('[data-testid="stMetricValue"]').all()

        for i, lbl in enumerate(labels):
            if label.lower() in lbl.inner_text().lower():
                raw = values[i].inner_text()  # e.g. "$1,850"
                cleaned = raw.replace("$", "").replace(",", "").strip()
                try:
                    return float(cleaned)
                except ValueError:
                    return None
        return None

    def get_banner_text(self) -> str:
        try:
            return self.page.locator('[data-testid="stInfo"]').inner_text()
        except Exception:
            return ""

    def has_exceptions(self) -> bool:
        return self.page.locator('[data-testid="stException"]').count() > 0  # streamlit crash box

    def is_dataframe_visible(self) -> bool:
        return self.page.locator('[data-testid="stDataFrame"]').count() > 0

    def is_download_visible(self) -> bool:
        # streamlit renders download buttons as anchor tags with a download attribute
        btn = self.page.locator('a[download]')
        text_btn = self.page.get_by_text("Download CSV")
        return btn.count() > 0 or text_btn.count() > 0

    # number inputs — streamlit sidebar renders them in order so we use index
    def _set_input(self, index: int, value: int):
        inputs = self.page.locator('input[type="number"]').all()
        el = inputs[index]
        el.scroll_into_view_if_needed()
        el.triple_click()  # select all existing text first
        el.type(str(value))
        el.press("Tab")  # tab out triggers streamlit rerun
        self.page.wait_for_timeout(1200)  # wait for rerun to finish

    def set_tuition(self, value: int):
        self._set_input(0, value)

    def set_rent(self, value: int):
        self._set_input(1, value)

    def set_dining(self, value: int):
        self._set_input(2, value)

    def set_entertainment(self, value: int):
        self._set_input(3, value)

    def set_social(self, value: int):
        self._set_input(4, value)

    def set_shopping(self, value: int):
        self._set_input(5, value)

    def set_misc(self, value: int):
        self._set_input(6, value)
