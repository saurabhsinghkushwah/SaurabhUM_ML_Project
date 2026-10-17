# Cell-by-cell companion. In Jupyter, run notebook cells in order.

# %% [markdown]
# # APL Logistics: Customer, Product & Profitability Performance
# ## Run each numbered code cell in order
# This notebook follows the supplied brief. Monetary amounts are **dataset currency units**, not assumed USD. All statuses are included in the primary analysis; a COMPLETE/CLOSED sensitivity view is separate. Record-level economics are not verified recognized revenue. No dates or order IDs are available, so no time trends or distinct-order counts are fabricated.
# 
# **Execution:** unzip the project, place the supplied CSV in the project directory or its parent, and open this notebook in Jupyter. The commented Python companion contains the same numbered cells.

# %% [markdown]
# ### Cell 01 — Install dependencies (run once)

# %%
# Run in terminal: python -m pip install -r requirements.txt

# %% [markdown]
# ### Cell 02 — Import libraries and configure display

# %%
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, Markdown
sns.set_theme(style="whitegrid", palette="deep")
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda x: f"{x:,.3f}")
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

# %% [markdown]
# ### Cell 03 — Define all validation and analysis functions

# %%
"""Shared, auditable calculations for the notebook and dashboard."""
from pathlib import Path
import numpy as np
import pandas as pd

TOLERANCE = 0.02
NUMERIC = ['Sales', 'Order Item Total', 'Order Profit Per Order', 'Benefit per order',
           'Sales per customer', 'Order Item Discount', 'Order Item Discount Rate',
           'Order Item Product Price', 'Order Item Quantity', 'Order Item Profit Ratio',
           'Customer Id', 'Order Customer Id']
GROUPS = ['Customer Segment', 'Category Name', 'Product Name', 'Market',
          'Order Region', 'Order Country', 'Order Status']

def load_csv(source):
    """Read a local path or Streamlit upload without silently replacing bad bytes."""
    try:
        return pd.read_csv(source, encoding='utf-8', dtype={'Customer Zipcode': 'string'})
    except UnicodeDecodeError:
        if hasattr(source, 'seek'):
            source.seek(0)
        return pd.read_csv(source, encoding='cp1252', dtype={'Customer Zipcode': 'string'})

def clean_data(raw):
    """Keep losses and incomplete statuses; quarantine invalid financial records."""
    d = raw.copy()
    required = set(NUMERIC + GROUPS)
    missing = required - set(d.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')
    for column in d.select_dtypes(include=['object', 'string']).columns:
        d[column] = d[column].astype('string').str.strip().replace('', pd.NA)
    for column in NUMERIC:
        d[column] = pd.to_numeric(d[column], errors='coerce')
    for column in GROUPS:
        d[column] = d[column].fillna('Unknown')
    checks = pd.DataFrame(index=d.index)
    checks['missing_or_nonfinite_numeric'] = ~np.isfinite(d[NUMERIC].to_numpy(dtype=float)).all(axis=1)
    checks['nonpositive_sales'] = d['Sales'].le(0) | d['Order Item Total'].le(0)
    checks['invalid_quantity'] = d['Order Item Quantity'].le(0) | d['Order Item Quantity'].mod(1).ne(0)
    checks['invalid_discount'] = ~d['Order Item Discount Rate'].between(0, 1) | d['Order Item Discount'].lt(0)
    checks['gross_net_mismatch'] = (d['Sales'] - d['Order Item Discount'] - d['Order Item Total']).abs().gt(TOLERANCE)
    checks['price_quantity_mismatch'] = (d['Sales'] - d['Order Item Product Price'] * d['Order Item Quantity']).abs().gt(TOLERANCE)
    checks['profit_alias_mismatch'] = (d['Benefit per order'] - d['Order Profit Per Order']).abs().gt(TOLERANCE)
    checks['net_sales_alias_mismatch'] = (d['Sales per customer'] - d['Order Item Total']).abs().gt(TOLERANCE)
    checks['customer_id_mismatch'] = d['Customer Id'].ne(d['Order Customer Id'])
    invalid = checks.any(axis=1)
    # Do not remove identical rows: without a line ID they could be valid repeated items.
    audit = pd.DataFrame({'issue': checks.columns, 'rows_flagged': checks.sum().values})
    rejected = d.loc[invalid].copy()
    rejected['rejection_reason'] = [
        '; '.join(row.index[row]) for _, row in checks.loc[invalid].iterrows()
    ]
    d = d.loc[~invalid].copy()
    d['gross_sales'] = d['Sales']
    d['net_revenue'] = d['Order Item Total']
    d['profit'] = d['Order Profit Per Order']
    d['discount_amount'] = d['Order Item Discount']
    d['discount_rate'] = d['Order Item Discount Rate']
    d['margin_pct'] = 100 * d['profit'] / d['net_revenue']
    d['implied_cost'] = d['net_revenue'] - d['profit']
    d['discount_band'] = pd.cut(d['discount_rate'], bins=[-0.000001, 0, .05, .10, .15, .20, 1],
                               labels=['0%', '>0–5%', '>5–10%', '>10–15%', '>15–20%', '>20%'])
    d['Customer Id'] = d['Customer Id'].astype('int64')
    return d, audit, rejected

def summarize(d, keys):
    result = d.groupby(keys, observed=True, dropna=False).agg(
        rows=('profit', 'size'), customers=('Customer Id', 'nunique'),
        gross_sales=('gross_sales', 'sum'), net_revenue=('net_revenue', 'sum'),
        profit=('profit', 'sum'), discounts=('discount_amount', 'sum'),
        units=('Order Item Quantity', 'sum')).reset_index()
    result['margin_pct'] = 100 * result['profit'] / result['net_revenue']
    result['profit_to_gross_pct'] = 100 * result['profit'] / result['gross_sales']
    result['effective_discount_pct'] = 100 * result['discounts'] / result['gross_sales']
    return result.sort_values('profit', ascending=False)

def customer_table(d):
    c = summarize(d, ['Customer Id'])
    # Explicit project definition; not an externally standardized index.
    c['customer_value_index'] = c['profit']
    positive = c.loc[c['profit'] > 0, 'profit']
    cutoff = positive.quantile(.8) if len(positive) else np.inf
    c['value_tier'] = np.select([c['profit'].le(0), c['profit'].ge(cutoff)],
                                 ['Nonpositive profit', 'High value'], default='Positive core')
    c['low_margin'] = c['profit'].gt(0) & c['margin_pct'].lt(5)
    positive_total = c['profit'].clip(lower=0).sum()
    c['cumulative_positive_profit_pct'] = (100 * c['profit'].clip(lower=0).cumsum() / positive_total
                                           if positive_total else np.nan)
    return c

def kpis(d):
    gross, net, profit = d['gross_sales'].sum(), d['net_revenue'].sum(), d['profit'].sum()
    discount = d['discount_amount'].sum()
    # Fixed-cost, fixed-volume counterfactual: restoring discounts adds discount dollars to profit.
    baseline_profit = profit + discount
    return {'rows': len(d), 'customers': d['Customer Id'].nunique(),
            'gross_sales': gross, 'net_revenue': net, 'profit': profit,
            'discounts': discount, 'margin_pct': 100 * profit / net if net else np.nan,
            'profit_to_gross_pct': 100 * profit / gross if gross else np.nan,
            'discount_impact_ratio_pct': 100 * discount / baseline_profit if baseline_profit else np.nan,
            'modeled_margin_erosion_pp': 100 * baseline_profit / gross - 100 * profit / net if gross and net else np.nan}

def discount_scenario(d, new_rate):
    """Uniform replacement rate; costs/quantities unchanged, no demand response."""
    gross = d['gross_sales'].sum()
    modeled_net = gross * (1 - new_rate)
    modeled_profit = modeled_net - d['implied_cost'].sum()
    return pd.Series({'scenario_discount_pct': 100 * new_rate,
                      'scenario_net_revenue': modeled_net, 'scenario_profit': modeled_profit,
                      'profit_change': modeled_profit - d['profit'].sum(),
                      'scenario_margin_pct': 100 * modeled_profit / modeled_net if modeled_net else np.nan})

def resolve_data():
    candidates = [Path('APL_Logistics (1).csv'), Path('../APL_Logistics (1).csv')]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError('Put APL_Logistics (1).csv beside the notebook or one directory above it.')

# %% [markdown]
# ### Cell 04 — Load the supplied CSV

# %%
DATA_PATH = resolve_data()
raw = load_csv(DATA_PATH)
print("Dataset:", DATA_PATH)
print("Rows and columns:", raw.shape)
display(raw.head().drop(columns=["Customer Fname", "Customer Lname", "Customer Street", "Customer Zipcode", "Latitude", "Longitude"]))

# %% [markdown]
# ### Cell 05 — Inspect schema, missingness and duplicates

# %%
display(raw.dtypes.to_frame("dtype"))
missing = raw.isna().sum().sort_values(ascending=False).to_frame("missing_rows")
display(missing[missing["missing_rows"] > 0])
print("Exact duplicate rows:", raw.duplicated().sum())
print("Dates present:", [c for c in raw.columns if "date" in c.lower()])
print("Do not deduplicate without a verified line identifier.")

# %% [markdown]
# ### Cell 06 — Clean and quarantine invalid financial records

# %%
df, audit, rejected = clean_data(raw)
display(audit)
print(f"Retained: {len(df):,}; quarantined: {len(rejected):,}")
audit.to_csv(OUT / "validation_audit.csv", index=False)
# Raw rejected data may contain PII; save only counts/reasons.
rejected["rejection_reason"].value_counts().to_csv(OUT / "rejection_reasons.csv")
assert len(df) + len(rejected) == len(raw)
assert np.allclose(df["gross_sales"] - df["discount_amount"], df["net_revenue"], atol=.02)
assert (df["net_revenue"] > 0).all()

# %% [markdown]
# **Definitions.** Gross revenue = sum of `Sales` (the brief's total-revenue KPI). Net revenue = sum of `Order Item Total`. Reported profit = sum of `Order Profit Per Order` once; `Benefit per order` duplicates it. Net margin = 100 × total profit / net revenue, not the simple average of item ratios. Customer Value Index (project definition) = aggregate reported profit per customer. Discount Impact Ratio = 100 × discounts / (reported profit + discounts), a fixed-cost/no-demand-response modeled profit reduction. Modeled margin erosion compares no-discount margin with observed net margin; neither establishes causality. Costs inferred as net revenue minus profit are not observed shipping costs.

# %% [markdown]
# ### Cell 07 — Calculate core financial KPIs

# %%
metrics = kpis(df)
display(pd.Series(metrics, name="value").to_frame())
print("Aggregate rounding residual (gross - discounts - net):", metrics["gross_sales"] - metrics["discounts"] - metrics["net_revenue"])
(OUT / "kpis.json").write_text(json.dumps(metrics, indent=2, default=float))

# %% [markdown]
# ### Cell 08 — Visualize gross sales, discounts, net revenue and profit

# %%
fig, ax = plt.subplots(figsize=(10, 5))
labels = ["Gross sales", "Discounts", "Net revenue", "Reported profit"]
values = [metrics[k] for k in ["gross_sales", "discounts", "net_revenue", "profit"]]
sns.barplot(x=labels, y=values, ax=ax)
ax.set(ylabel="Dataset currency units", title="Revenue and profit overview (all statuses)")
fig.tight_layout()
fig.savefig(OUT / "financial_overview.png", dpi=160)
plt.show()
print("Time trends cannot be computed: no date column was supplied.")

# %% [markdown]
# ### Cell 09 — Analyze order-status sensitivity

# %%
status_summary = summarize(df, ["Order Status"])
display(status_summary)
finalized_proxy = df[df["Order Status"].isin(["COMPLETE", "CLOSED"])]
display(pd.DataFrame({"all_statuses": kpis(df), "complete_closed_proxy": kpis(finalized_proxy)}))
print("COMPLETE/CLOSED is a sensitivity proxy, not a verified accounting recognition policy.")
status_summary.to_csv(OUT / "status_summary.csv", index=False)

# %% [markdown]
# ### Cell 10 — Aggregate product and category profitability

# %%
products = summarize(df, ["Product Name"])
categories = summarize(df, ["Category Name"])
display(products.head(15))
display(categories)
products.to_csv(OUT / "product_profitability.csv", index=False)
categories.to_csv(OUT / "category_profitability.csv", index=False)

# %% [markdown]
# ### Cell 11 — Find loss-makers and high-revenue/low-margin products

# %%
high_revenue_cutoff = products["net_revenue"].quantile(.75)
low_margin_cutoff = products["margin_pct"].quantile(.25)
priority_products = products[(products["net_revenue"] >= high_revenue_cutoff) & (products["margin_pct"] <= low_margin_cutoff)]
print("High revenue = top quartile; low margin = bottom quartile (product-level).")
print("Revenue cutoff:", high_revenue_cutoff, "Margin cutoff:", low_margin_cutoff)
display(priority_products)
print("Loss-making categories:")
display(categories[categories["profit"] < 0])
priority_products.to_csv(OUT / "priority_products.csv", index=False)

# %% [markdown]
# ### Cell 12 — Plot category-by-market weighted margin heatmap

# %%
category_market = summarize(df, ["Category Name", "Market"])
heat = category_market.pivot(index="Category Name", columns="Market", values="margin_pct")
fig, ax = plt.subplots(figsize=(11, 16))
sns.heatmap(heat, cmap="RdYlGn", center=0, ax=ax, cbar_kws={"label": "Net margin (%)"})
ax.set_title("Category × market weighted profit margin")
fig.tight_layout()
fig.savefig(OUT / "category_market_heatmap.png", dpi=160)
plt.show()

# %% [markdown]
# ### Cell 13 — Calculate customer contribution and value tiers

# %%
customers = customer_table(df)
display(customers.head(10))
display(customers.nsmallest(10, "profit"))
tiers = customers.groupby("value_tier").agg(customers=("Customer Id", "size"), net_revenue=("net_revenue", "sum"), profit=("profit", "sum"))
tiers["margin_pct"] = 100 * tiers["profit"] / tiers["net_revenue"]
display(tiers)
customers.to_csv(OUT / "customer_profitability.csv", index=False)
tiers.to_csv(OUT / "customer_tiers.csv")

# %% [markdown]
# ### Cell 14 — Measure customer profit concentration

# %%
positive = customers[customers["profit"] > 0].copy()
top_n = max(1, int(np.ceil(len(positive) * .20)))
positive_pool = positive["profit"].sum()
share = 100 * positive.head(top_n)["profit"].sum() / positive_pool
print(f"Top 20% of positive-profit customers produce {share:.2f}% of the positive-profit pool.")
print("Loss-making customer count:", (customers["profit"] < 0).sum())
fig, ax = plt.subplots(figsize=(9, 5))
x = 100 * np.arange(1, len(positive) + 1) / len(positive)
y = 100 * positive["profit"].cumsum() / positive_pool
ax.plot(x, y)
ax.set(xlabel="Positive-profit customers, ranked (%)", ylabel="Cumulative positive profit (%)", title="Customer profit concentration")
fig.tight_layout()
fig.savefig(OUT / "customer_concentration.png", dpi=160)
plt.show()

# %% [markdown]
# ### Cell 15 — Compare customer segments

# %%
segments = summarize(df, ["Customer Segment"])
display(segments)
segments.to_csv(OUT / "segment_profitability.csv", index=False)
fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(data=segments, x="Customer Segment", y="margin_pct", ax=ax)
ax.set_title("Weighted margin by customer segment")
plt.show()

# %% [markdown]
# ### Cell 16 — Compare observed discount bands and no-discount records

# %%
discount_bands = summarize(df, ["discount_band"]).sort_values("discount_band")
display(discount_bands)
discount_bands.to_csv(OUT / "discount_bands.csv", index=False)
discount_comparison = summarize(df.assign(discount_group=np.where(df["discount_amount"] > 0, "Discounted", "No discount")), ["discount_group"])
display(discount_comparison)
print("Groups have different customer/product mix: observational comparison, not causal treatment effect.")

# %% [markdown]
# ### Cell 17 — Inspect associations and candidate erosion thresholds

# %%
correlations = df[["discount_rate", "margin_pct", "Order Item Profit Ratio"]].corr(method="spearman")
display(correlations)
rate_summary = summarize(df, ["discount_rate"]).sort_values("discount_rate")
rate_summary["margin_change_from_prior_pp"] = rate_summary["margin_pct"].diff()
display(rate_summary)
negative_bands = discount_bands[discount_bands["profit"] < 0]
print("Observed loss-making bands (if any):")
display(negative_bands)
print("No universally causal discount threshold can be inferred from this cross-sectional dataset.")
rate_summary.to_csv(OUT / "discount_rate_diagnostics.csv", index=False)

# %% [markdown]
# ### Cell 18 — Examine discount patterns within product/market groups

# %%
within_group = summarize(df, ["Product Name", "Market", "discount_band"])
within_group = within_group[within_group["rows"] >= 30]
display(within_group.head(20))
print("Minimum 30 records per displayed cell; stratification reduces but does not eliminate confounding.")
within_group.to_csv(OUT / "within_product_market_discounts.csv", index=False)

# %% [markdown]
# ### Cell 19 — Run transparent discount what-if scenarios

# %%
scenarios = pd.DataFrame([discount_scenario(df, r) for r in [0, .05, .10, .15, .20, .25]])
display(scenarios)
scenarios.to_csv(OUT / "discount_scenarios.csv", index=False)
# Each record's fixed-cost break-even discount = reported profit + existing discount, divided by gross sales.
df["modeled_break_even_discount"] = (df["profit"] + df["discount_amount"]) / df["gross_sales"]
print("Break-even discount percentiles (negative values mean a loss even without discount):")
display((100 * df["modeled_break_even_discount"]).quantile([0, .1, .25, .5, .75, .9, 1]))
print("Assumptions: unchanged gross prices, quantities, mix and implied costs; no demand response.")

# %% [markdown]
# ### Cell 20 — Diagnose markets, regions and destination countries

# %%
markets = summarize(df, ["Market"])
regions = summarize(df, ["Order Region"])
countries = summarize(df, ["Order Country"])
for name, table in [("market", markets), ("region", regions), ("country", countries)]:
    display(table)
    table.to_csv(OUT / f"{name}_profitability.csv", index=False)
weak_markets = markets[(markets["net_revenue"] >= markets["net_revenue"].median()) & (markets["margin_pct"] < metrics["margin_pct"])]
print("Strong-revenue/weak-profit markets: revenue >= market median and margin below portfolio margin.")
display(weak_markets)

# %% [markdown]
# ### Cell 21 — Generate research paper and executive summary

# %%
from report_builder import write_reports
write_reports(df, audit, rejected, OUT)
print("Research paper and executive summary written in outputs, in Markdown and Word formats.")

# %% [markdown]
# ### Cell 22 — Check dashboard source and run it locally

# %%
import subprocess
import sys
subprocess.run([sys.executable, "-m", "py_compile", "app.py", "analysis_core.py"], check=True)
print("Dashboard syntax check passed.")
print("In a terminal in this directory, run: streamlit run app.py")
# Do not launch a long-running server inside this notebook cell.
# The app supports upload, segment/category/product/market/region/status filters,
# an observed-discount slider, customer rankings, product plots, heatmaps, and scenarios.

# %% [markdown]
# ## Submission and interpretation checklist
# - Include the executed notebook, research paper, executive summary, dashboard source and requirements.
# - To host: put the project in a repository, create a Streamlit-hosted app pointing to `app.py`, and upload the CSV through the application. Do not commit private customer data to a public repository.
# - A local app is provided; no public deployment or live URL is claimed.
# - Financial aliases are not double counted; losses are retained; invalid records are quarantined.
# - No unsupported dollar currency, time trend, unique order counts, shipping cost attribution, or causal discount conclusions.
# - Use aggregate results for government stakeholders; keep customer IDs and raw data access restricted.
# - Validate accounting status, cost completeness, currency, licensing/provenance and recognition rules before real decisions.
