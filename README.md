# Kani | Python, Data Analytics & Software Development

Computer science student building practical skills in Python, SQL, data analysis, and software testing. My projects span data-quality workflows, interactive applications, and research into how models perform—and where they fail.

**Explore:** [Interactive portfolio (Streamlit)](https://data-analytics-portfolio-e3nhrkkeemhxhhk2hh6og5.streamlit.app/) · [GitHub projects](https://github.com/patelkavitarepo/Data-analytics-portfolio) · [GitHub profile](https://github.com/patelkavitarepo)

## Technical focus

- **Programming:** Python, SQL/SQLite, application logic, input validation, and automated testing
- **Data and reporting:** pandas, NumPy, data cleaning, exploratory analysis, Streamlit, Plotly, and Power BI
- **Research practice:** reproducible workflows, chronological evaluation, failure analysis, and clear documentation

## Featured published work

### 01 · Stock Volatility Forecasting and Failure Analysis

[Project overview & code](optiver-realized-volatility/README.md) · [Results and limitations](optiver-realized-volatility/research/forecast-D008/RESULTS.md)

Compared three approaches to forecasting **five-session stock volatility**, evaluating **111,428 historical stock-date observations across 482 stocks**. On the internal 2015 evaluation set, the stock-specific Ridge approach recorded **0.5688 RMSPE**, compared with **0.8774** for the historical-volatility baseline.

**What it demonstrates:** Python research workflows, data-quality controls, model comparisons, chronological evaluation, and analysis of cases where a model underperforms. These are **historical internal results**, not live forecasting or untouched-holdout performance; the highest-volatility outcomes remained difficult.

### 02 · Synthetic Portfolio Risk Research

[Project overview & code](markowitz-synthetic-showcase/README.md) · [Case study](markowitz-synthetic-showcase/CASE_STUDY.md)

Published a reproducible showcase of **five synthetic investigations** into portfolio optimization stability, correlation changes, resampling choices, and risk estimation.

**What it demonstrates:** simulation, statistical reasoning, automated checks, interpreting counterexamples, and communicating uncertainty. The work uses **synthetic data only**: it does not establish real ETF returns or investment performance.

## Software engineering work in progress

### DataOps Sentinel · Python data validation and auditing

[Review the draft project and evidence (PR #16)](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/16)

A general Python application for bounded CSV/JSON ingestion, record validation, transactional SQLite auditing, exact-input replay, and a Streamlit interface. The feature is **in draft review**, not merged into `main` and **not claimed as a publicly deployed app**.

## About the work

My interests include finance and analytics, but the skills I am developing—programming, databases, testing, validation, and problem-solving—apply beyond financial datasets.

The research questions, evaluation decisions, and interpretations are human-led; AI-assisted implementation is disclosed in the individual project documentation. I aim to separate measured findings from assumptions and unfinished work.

---

**For recruiters:** The links above lead to source code, documentation, tests, results, and explicitly stated limitations. The [interactive portfolio](https://data-analytics-portfolio-e3nhrkkeemhxhhk2hh6og5.streamlit.app/) is an additional entry point.
