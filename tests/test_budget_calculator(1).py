import pytest
from playwright.sync_api import Page, expect
from pages.budget_page import BudgetPage


# ==============================================================================
# SMOKE — does the app load and show the right things
# ==============================================================================

class TestSmoke:

    @pytest.mark.smoke
    def test_app_loads(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        title = page.title()
        assert "Budget" in title or "Student" in title or title != ""  # streamlit sets this from set_page_config

    @pytest.mark.smoke
    def test_info_banner_visible(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        banner = bp.get_banner_text()
        assert len(banner) > 0  # banner shows uni / city / program on load

    @pytest.mark.smoke
    def test_four_metric_cards_present(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        labels = page.locator('[data-testid="stMetricLabel"] p').all()
        texts = [l.inner_text() for l in labels]

        assert any("Monthly" in t for t in texts), "missing Monthly card"
        assert any("8 Months" in t for t in texts), "missing 8 Months card"
        assert any("4 Months" in t for t in texts), "missing 4 Months card"
        assert any("Annual" in t for t in texts), "missing Annual Total card"

    @pytest.mark.smoke
    def test_three_tabs_exist(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        tabs = page.get_by_role("tab").all()
        tab_texts = [t.inner_text() for t in tabs]

        assert any("Breakdown" in t for t in tab_texts), "missing Breakdown tab"
        assert any("Charts" in t for t in tab_texts), "missing Charts tab"
        assert any("Export" in t for t in tab_texts), "missing Export tab"

    @pytest.mark.smoke
    def test_sidebar_has_number_inputs(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        inputs = page.locator('input[type="number"]').all()
        assert len(inputs) >= 5  # rent, tuition, dining, entertainment, social at minimum

    @pytest.mark.smoke
    def test_no_exceptions_on_load(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        assert not bp.has_exceptions()  # usually means a bad import or s3 failure


# ==============================================================================
# CALCULATION — are the numbers actually correct
# ==============================================================================

class TestCalculations:

    @pytest.mark.calculation
    def test_monthly_is_nonzero_on_load(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        monthly = bp.get_metric("Monthly")
        assert monthly is not None, "couldnt read Monthly metric"
        assert monthly > 0  # default values should give something reasonable

    @pytest.mark.calculation
    def test_annual_greater_than_monthly(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        monthly = bp.get_metric("Monthly")
        annual = bp.get_metric("Annual Total")

        assert monthly is not None and annual is not None
        assert annual > monthly  # annual = 8mo + summer + tuition so always bigger

    @pytest.mark.calculation
    def test_8_months_roughly_8x_monthly(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        monthly = bp.get_metric("Monthly")
        eight_mo = bp.get_metric("8 Months")

        assert monthly is not None and eight_mo is not None

        expected = monthly * 8
        tolerance = expected * 0.05  # 5% wiggle room for rounding
        assert abs(eight_mo - expected) <= tolerance, f"8mo ({eight_mo}) too far from 8x monthly ({expected})"

    @pytest.mark.calculation
    def test_annual_includes_tuition(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        annual = bp.get_metric("Annual Total")
        eight = bp.get_metric("8 Months")
        four = bp.get_metric("4 Months")

        assert all(v is not None for v in [annual, eight, four])

        # annual = 8mo + 4mo + tuition, so subtracting living costs should leave tuition
        implied_tuition = annual - eight - four
        assert implied_tuition > 1000, f"implied tuition only ${implied_tuition:.0f} — tuition might not be added"

    @pytest.mark.calculation
    def test_metric_values_start_with_dollar(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        values = page.locator('[data-testid="stMetricValue"]').all()
        assert len(values) >= 4

        for v in values[:4]:
            text = v.inner_text().strip()
            assert text.startswith("$"), f"metric value '{text}' doesnt start with $"
            assert "None" not in text and "nan" not in text.lower()  # would mean a calculation failed


# ==============================================================================
# UI — do tabs, tables, charts, and selects render correctly
# ==============================================================================

class TestUI:

    @pytest.mark.ui
    def test_breakdown_tab_shows_table(self, page: Page):
        bp = BudgetPage(page)
        bp.load()
        bp.click_tab("Breakdown")

        assert bp.is_dataframe_visible()  # should show monthly expenses table

    @pytest.mark.ui
    def test_export_tab_shows_download_button(self, page: Page):
        bp = BudgetPage(page)
        bp.load()
        bp.click_tab("Export")

        page.wait_for_timeout(1000)
        assert bp.is_download_visible()  # csv download button should be there

    @pytest.mark.ui
    def test_charts_tab_no_crash(self, page: Page):
        bp = BudgetPage(page)
        bp.load()
        bp.click_tab("Charts")

        page.wait_for_timeout(1500)  # matplotlib takes a sec to render
        assert not bp.has_exceptions()

    @pytest.mark.ui
    def test_selectboxes_present(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        selects = page.locator('[data-testid="stSelectbox"]').all()
        assert len(selects) >= 2  # at least university + program dropdowns


# ==============================================================================
# EDGE CASES — unusual inputs and boundary values
# ==============================================================================

class TestEdgeCases:

    @pytest.mark.edge_case
    def test_zero_rent_no_crash(self, page: Page):
        bp = BudgetPage(page)
        bp.load()
        bp.set_rent(0)

        assert not bp.has_exceptions()
        assert bp.get_metric("Monthly") is not None  # metric should still show up

    @pytest.mark.edge_case
    def test_large_rent_no_crash(self, page: Page):
        bp = BudgetPage(page)
        bp.load()
        bp.set_rent(9999)

        assert not bp.has_exceptions()

        monthly = bp.get_metric("Monthly")
        assert monthly is not None and monthly > 0

    @pytest.mark.edge_case
    def test_all_lifestyle_zero(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        # zero out all the optional lifestyle costs
        bp.set_dining(0)
        bp.set_entertainment(0)
        bp.set_social(0)
        bp.set_shopping(0)
        bp.set_misc(0)

        assert not bp.has_exceptions()
        assert bp.get_metric("Monthly") is not None  # rent + city costs still keep it nonzero

    @pytest.mark.edge_case
    def test_tuition_zero_lowers_annual(self, page: Page):
        bp = BudgetPage(page)
        bp.load()

        annual_before = bp.get_metric("Annual Total")
        bp.set_tuition(0)
        annual_after = bp.get_metric("Annual Total")

        assert annual_before is not None and annual_after is not None
        assert annual_after < annual_before  # removing tuition should bring annual down

    @pytest.mark.edge_case
    def test_s3_data_loaded(self, page: Page):
        s3_statuses = []

        def track(response):
            if "amazonaws.com" in response.url or "s3." in response.url:  # only care about s3
                s3_statuses.append(response.status)

        page.on("response", track)  # attach before load so we catch everything

        bp = BudgetPage(page)
        bp.load()

        assert any(s == 200 for s in s3_statuses), f"no successful s3 requests — got: {s3_statuses}"
