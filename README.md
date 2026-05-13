# 🍁 Canada Student Budget Calculator

A web app that helps international students estimate the cost of studying in Canada. Built with Streamlit and deployed online.

## What it does

Pick a university, program, and city — the app pulls live data from AWS S3 and calculates your estimated costs broken down by month, semester, and full year. You can customize every expense (rent, dining, entertainment, transit, etc.) and export your budget as a CSV.

## Features

- 30+ Canadian universities with real tuition data
- Cost estimates across 11 cities (rent, groceries, transport, utilities)
- Program-based tuition multipliers (e.g. Medicine vs Arts)
- Summer options — staying, moving cities, or going home
- Pie and bar chart visualizations
- CSV export with full budget breakdown

## Tech stack

- Python, Streamlit
- Pandas, Matplotlib
- AWS S3 (data storage)
- Pytest, Playwright (automated test suite)

## Project structure

```
budget-calculator-canada/
├── app.py                          
├── requirements.txt                
├── pytest.ini                      
├── pages/
│   └── budget_page.py              
└── tests/
    ├── conftest.py                 
    └── test_budget_calculator.py   
```

## Running the app

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Running the tests

```bash
pip install pytest playwright pytest-playwright
playwright install chromium
streamlit run app.py &
pytest
```

Run a specific category:

```bash
pytest -m smoke
pytest -m calculation
pytest -m edge_case
```

## Test coverage

| Category | What's tested |
|---|---|
| Smoke | App loads, banner visible, 4 metric cards, 3 tabs, sidebar inputs |
| Calculation | Monthly totals, annual vs monthly, 8-month math, tuition included |
| UI | Breakdown table, CSV download button, charts render without crash |
| Edge cases | Zero rent, zero tuition, all lifestyle costs at zero, S3 data loads |
