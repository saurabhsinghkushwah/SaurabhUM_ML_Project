from pathlib import Path
import nbformat as nbf
root = Path(__file__).parent
nb = nbf.v4.new_notebook()
cells = []
def md(text): cells.append(nbf.v4.new_markdown_cell(text))
def code(title, text):
    md('### ' + title)
    cells.append(nbf.v4.new_code_cell(text.strip()))
md('''# APL Logistics: Customer, Product & Profitability Performance
## Run each numbered code cell in order
This notebook follows the supplied brief. Monetary amounts are **dataset currency units**, not assumed USD. All statuses are included in the primary analysis; a COMPLETE/CLOSED sensitivity view is separate. Record-level economics are not verified recognized revenue. No dates or order IDs are available, so no time trends or distinct-order counts are fabricated.

**Execution:** unzip the project, place the supplied CSV in the project directory or its parent, and open this notebook in Jupyter. The commented Python companion contains the same numbered cells.''')
code('Cell 01 — Install dependencies (run once)', '''%pip install -r requirements.txt''')
code('Cell 02 — Import libraries and configure display', '''from pathlib import Path
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
OUT.mkdir(exist_ok=True)''')
code('Cell 03 — Define all validation and analysis functions', (root/'analysis_core.py').read_text())
code('Cell 04 — Load the supplied CSV', '''DATA_PATH = resolve_data()
raw = load_csv(DATA_PATH)
print("Dataset:", DATA_PATH)
print("Rows and columns:", raw.shape)
display(raw.head().drop(columns=["Customer Fname", "Customer Lname", "Customer Street", "Customer Zipcode", "Latitude", "Longitude"]))''')
code('Cell 05 — Inspect schema, missingness and duplicates', '''display(raw.dtypes.to_frame("dtype"))
missing = raw.isna().sum().sort_values(ascending=False).to_frame("missing_rows")
display(missing[missing["missing_rows"] > 0])
print("Exact duplicate rows:", raw.duplicated().sum())
print("Dates present:", [c for c in raw.columns if "date" in c.lower()])
print("Do not deduplicate without a verified line identifier.")''')
code('Cell 06 — Clean and quarantine invalid financial records', '''df, audit, rejected = clean_data(raw)
display(audit)
print(f"Retained: {len(df):,}; quarantined: {len(rejected):,}")
audit.to_csv(OUT / "validation_audit.csv", index=False)
# Raw rejected data may contain PII; save only counts/reasons.
rejected["rejection_reason"].value_counts().to_csv(OUT / "rejection_reasons.csv")
assert len(df) + len(rejected) == len(raw)
assert np.allclose(df["gross_sales"] - df["discount_amount"], df["net_revenue"], atol=.02)
assert (df["net_revenue"] > 0).all()''')
md('''**Definitions.** Gross revenue = sum of `Sales` (the brief's total-revenue KPI). Net revenue = sum of `Order Item Total`. Reported profit = sum of `Order Profit Per Order` once; `Benefit per order` duplicates it. Net margin = 100 × total profit / net revenue, not the simple average of item ratios. Customer Value Index (project definition) = aggregate reported profit per customer. Discount Impact Ratio = 100 × discounts / (reported profit + discounts), a fixed-cost/no-demand-response modeled profit reduction. Modeled margin erosion compares no-discount margin with observed net margin; neither establishes causality. Costs inferred as net revenue minus profit are not observed shipping costs.''')
code('Cell 07 — Calculate core financial KPIs', '''metrics = kpis(df)
display(pd.Series(metrics, name="value").to_frame())
print("Aggregate rounding residual (gross - discounts - net):", metrics["gross_sales"] - metrics["discounts"] - metrics["net_revenue"])
(OUT / "kpis.json").write_text(json.dumps(metrics, indent=2, default=float))''')
code('Cell 08 — Visualize gross sales, discounts, net revenue and profit', '''fig, ax = plt.subplots(figsize=(10, 5))
labels = ["Gross sales", "Discounts", "Net revenue", "Reported profit"]
values = [metrics[k] for k in ["gross_sales", "discounts", "net_revenue", "profit"]]
sns.barplot(x=labels, y=values, ax=ax)
ax.set(ylabel="Dataset currency units", title="Revenue and profit overview (all statuses)")
fig.tight_layout()
fig.savefig(OUT / "financial_overview.png", dpi=160)
plt.show()
print("Time trends cannot be computed: no date column was supplied.")''')
code('Cell 09 — Analyze order-status sensitivity', '''status_summary = summarize(df, ["Order Status"])
display(status_summary)
finalized_proxy = df[df["Order Status"].isin(["COMPLETE", "CLOSED"])]
display(pd.DataFrame({"all_statuses": kpis(df), "complete_closed_proxy": kpis(finalized_proxy)}))
print("COMPLETE/CLOSED is a sensitivity proxy, not a verified accounting recognition policy.")
status_summary.to_csv(OUT / "status_summary.csv", index=False)''')
code('Cell 10 — Aggregate product and category profitability', '''products = summarize(df, ["Product Name"])
categories = summarize(df, ["Category Name"])
display(products.head(15))
display(categories)
products.to_csv(OUT / "product_profitability.csv", index=False)
categories.to_csv(OUT / "category_profitability.csv", index=False)''')
code('Cell 11 — Find loss-makers and high-revenue/low-margin products', '''high_revenue_cutoff = products["net_revenue"].quantile(.75)
low_margin_cutoff = products["margin_pct"].quantile(.25)
priority_products = products[(products["net_revenue"] >= high_revenue_cutoff) & (products["margin_pct"] <= low_margin_cutoff)]
print("High revenue = top quartile; low margin = bottom quartile (product-level).")
print("Revenue cutoff:", high_revenue_cutoff, "Margin cutoff:", low_margin_cutoff)
display(priority_products)
print("Loss-making categories:")
display(categories[categories["profit"] < 0])
priority_products.to_csv(OUT / "priority_products.csv", index=False)''')
code('Cell 12 — Plot category-by-market weighted margin heatmap', '''category_market = summarize(df, ["Category Name", "Market"])
heat = category_market.pivot(index="Category Name", columns="Market", values="margin_pct")
fig, ax = plt.subplots(figsize=(11, 16))
sns.heatmap(heat, cmap="RdYlGn", center=0, ax=ax, cbar_kws={"label": "Net margin (%)"})
ax.set_title("Category × market weighted profit margin")
fig.tight_layout()
fig.savefig(OUT / "category_market_heatmap.png", dpi=160)
plt.show()''')
code('Cell 13 — Calculate customer contribution and value tiers', '''customers = customer_table(df)
display(customers.head(10))
display(customers.nsmallest(10, "profit"))
tiers = customers.groupby("value_tier").agg(customers=("Customer Id", "size"), net_revenue=("net_revenue", "sum"), profit=("profit", "sum"))
tiers["margin_pct"] = 100 * tiers["profit"] / tiers["net_revenue"]
display(tiers)
customers.to_csv(OUT / "customer_profitability.csv", index=False)
tiers.to_csv(OUT / "customer_tiers.csv")''')
code('Cell 14 — Measure customer profit concentration', '''positive = customers[customers["profit"] > 0].copy()
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
plt.show()''')
code('Cell 15 — Compare customer segments', '''segments = summarize(df, ["Customer Segment"])
display(segments)
segments.to_csv(OUT / "segment_profitability.csv", index=False)
fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(data=segments, x="Customer Segment", y="margin_pct", ax=ax)
ax.set_title("Weighted margin by customer segment")
plt.show()''')
code('Cell 16 — Compare observed discount bands and no-discount records', '''discount_bands = summarize(df, ["discount_band"]).sort_values("discount_band")
display(discount_bands)
discount_bands.to_csv(OUT / "discount_bands.csv", index=False)
discount_comparison = summarize(df.assign(discount_group=np.where(df["discount_amount"] > 0, "Discounted", "No discount")), ["discount_group"])
display(discount_comparison)
print("Groups have different customer/product mix: observational comparison, not causal treatment effect.")''')
code('Cell 17 — Inspect associations and candidate erosion thresholds', '''correlations = df[["discount_rate", "margin_pct", "Order Item Profit Ratio"]].corr(method="spearman")
display(correlations)
rate_summary = summarize(df, ["discount_rate"]).sort_values("discount_rate")
rate_summary["margin_change_from_prior_pp"] = rate_summary["margin_pct"].diff()
display(rate_summary)
negative_bands = discount_bands[discount_bands["profit"] < 0]
print("Observed loss-making bands (if any):")
display(negative_bands)
print("No universally causal discount threshold can be inferred from this cross-sectional dataset.")
rate_summary.to_csv(OUT / "discount_rate_diagnostics.csv", index=False)''')
code('Cell 18 — Examine discount patterns within product/market groups', '''within_group = summarize(df, ["Product Name", "Market", "discount_band"])
within_group = within_group[within_group["rows"] >= 30]
display(within_group.head(20))
print("Minimum 30 records per displayed cell; stratification reduces but does not eliminate confounding.")
within_group.to_csv(OUT / "within_product_market_discounts.csv", index=False)''')
code('Cell 19 — Run transparent discount what-if scenarios', '''scenarios = pd.DataFrame([discount_scenario(df, r) for r in [0, .05, .10, .15, .20, .25]])
display(scenarios)
scenarios.to_csv(OUT / "discount_scenarios.csv", index=False)
# Each record's fixed-cost break-even discount = reported profit + existing discount, divided by gross sales.
df["modeled_break_even_discount"] = (df["profit"] + df["discount_amount"]) / df["gross_sales"]
print("Break-even discount percentiles (negative values mean a loss even without discount):")
display((100 * df["modeled_break_even_discount"]).quantile([0, .1, .25, .5, .75, .9, 1]))
print("Assumptions: unchanged gross prices, quantities, mix and implied costs; no demand response.")''')
code('Cell 20 — Diagnose markets, regions and destination countries', '''markets = summarize(df, ["Market"])
regions = summarize(df, ["Order Region"])
countries = summarize(df, ["Order Country"])
for name, table in [("market", markets), ("region", regions), ("country", countries)]:
    display(table)
    table.to_csv(OUT / f"{name}_profitability.csv", index=False)
weak_markets = markets[(markets["net_revenue"] >= markets["net_revenue"].median()) & (markets["margin_pct"] < metrics["margin_pct"])]
print("Strong-revenue/weak-profit markets: revenue >= market median and margin below portfolio margin.")
display(weak_markets)''')
code('Cell 21 — Generate research paper and executive summary', '''from report_builder import write_reports
write_reports(df, audit, rejected, OUT)
print("Research paper and executive summary written in outputs, in Markdown and Word formats.")''')
code('Cell 22 — Check dashboard source and run it locally', '''import subprocess
import sys
subprocess.run([sys.executable, "-m", "py_compile", "app.py", "analysis_core.py"], check=True)
print("Dashboard syntax check passed.")
print("In a terminal in this directory, run: streamlit run app.py")
# Do not launch a long-running server inside this notebook cell.
# The app supports upload, segment/category/product/market/region/status filters,
# an observed-discount slider, customer rankings, product plots, heatmaps, and scenarios.''')
md('''## Submission and interpretation checklist
- Include the executed notebook, research paper, executive summary, dashboard source and requirements.
- To host: put the project in a repository, create a Streamlit-hosted app pointing to `app.py`, and upload the CSV through the application. Do not commit private customer data to a public repository.
- A local app is provided; no public deployment or live URL is claimed.
- Financial aliases are not double counted; losses are retained; invalid records are quarantined.
- No unsupported dollar currency, time trend, unique order counts, shipping cost attribution, or causal discount conclusions.
- Use aggregate results for government stakeholders; keep customer IDs and raw data access restricted.
- Validate accounting status, cost completeness, currency, licensing/provenance and recognition rules before real decisions.''')
nb['cells'] = cells
nb['metadata'] = {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}}
nbf.write(nb, root/'APL_cell_by_cell.ipynb')
script = '# Cell-by-cell companion. In Jupyter, run notebook cells in order.\n'
for cell in cells:
    if cell.cell_type == 'markdown':
        script += '\n# %% [markdown]\n' + '\n'.join('# ' + line for line in cell.source.splitlines()) + '\n'
    else:
        source = cell.source
        if source.startswith('%pip'):
            source = '# Run in terminal: python -m pip install -r requirements.txt'
        script += '\n# %%\n' + source + '\n'
(root/'APL_cell_by_cell.py').write_text(script)
print('Notebook and numbered Python companion created.')
