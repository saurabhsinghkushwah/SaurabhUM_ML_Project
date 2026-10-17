"""Run: streamlit run app.py"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from analysis_core import load_csv, clean_data, summarize, customer_table, kpis, discount_scenario

st.set_page_config(page_title='APL | Profitability Intelligence', layout='wide')
st.title('Customer, Product & Profitability Intelligence')
st.caption('Record-level reported economics • Currency unspecified • Not audited financial statements')

@st.cache_data
def prepare(source):
    return clean_data(load_csv(source))

upload = st.sidebar.file_uploader('Upload the supplied CSV', type='csv')
paths = [Path('APL_Logistics (1).csv'), Path('../APL_Logistics (1).csv'), Path(__file__).parent.parent / 'APL_Logistics (1).csv']
path = next((p for p in paths if p.exists()), None)
if upload is None and path is None:
    st.info('Upload the CSV to begin.')
    st.stop()
d, audit, rejected = prepare(upload if upload is not None else str(path))
st.sidebar.header('Filters')
for col in ['Customer Segment', 'Category Name', 'Product Name', 'Market', 'Order Region', 'Order Status']:
    options = sorted(d[col].dropna().unique().tolist())
    selected = st.sidebar.multiselect(col, options, default=[], help='Empty means all values.')
    if selected:
        d = d[d[col].isin(selected)]
low, high = st.sidebar.slider('Observed discount rate (%)', 0, 100, (0, 100))
d = d[d['discount_rate'].between(low / 100, high / 100)]
if d.empty:
    st.warning('No records match these filters. Broaden the filters.')
    st.stop()
k = kpis(d)
a, b, c, e = st.columns(4)
a.metric('Gross sales', f"{k['gross_sales']:,.2f}")
b.metric('Net revenue', f"{k['net_revenue']:,.2f}")
c.metric('Reported profit', f"{k['profit']:,.2f}")
e.metric('Net margin', f"{k['margin_pct']:.2f}%")
st.caption(f"{len(d):,} records | {k['customers']:,} customers | All order statuses included unless filtered. No date field: time trends unavailable.")
tabs = st.tabs(['Overview', 'Customers', 'Products & categories', 'Discount diagnostics', 'Markets & quality'])
with tabs[0]:
    seg = summarize(d, ['Customer Segment'])
    st.plotly_chart(px.bar(seg, x='Customer Segment', y=['net_revenue', 'profit'], barmode='group'), use_container_width=True)
    st.dataframe(summarize(d, ['Order Status']), use_container_width=True)
    st.info('Profit and sales aliases are not added together. Category margins are revenue-weighted. These are records, not verified distinct orders.')
with tabs[1]:
    customers = customer_table(d)
    left, right = st.columns(2)
    left.plotly_chart(px.bar(customers.head(10), x=customers.head(10)['Customer Id'].astype(str), y='profit', title='Top customers'), use_container_width=True)
    bottom = customers.nsmallest(10, 'profit')
    right.plotly_chart(px.bar(bottom, x=bottom['Customer Id'].astype(str), y='profit', title='Bottom customers'), use_container_width=True)
    st.dataframe(customers, use_container_width=True)
    st.caption('CVI = aggregate reported customer profit; high value = positive-profit customers at or above the filtered 80th percentile. Low margin = positive profit and margin below 5%.')
with tabs[2]:
    products = summarize(d, ['Product Name'])
    st.plotly_chart(px.scatter(products, x='net_revenue', y='margin_pct', size='rows', color='profit', hover_name='Product Name', title='Product revenue versus margin'), use_container_width=True)
    heat = summarize(d, ['Category Name', 'Market']).pivot(index='Category Name', columns='Market', values='margin_pct')
    st.plotly_chart(px.imshow(heat, color_continuous_scale='RdYlGn', color_continuous_midpoint=0, aspect='auto', title='Category × market net margin (%)'), use_container_width=True)
    st.dataframe(products, use_container_width=True)
with tabs[3]:
    bands = summarize(d, ['discount_band']).sort_values('discount_band')
    st.plotly_chart(px.bar(bands, x='discount_band', y='margin_pct', title='Observed weighted margin by discount band'), use_container_width=True)
    sample = d.sample(min(len(d), 10000), random_state=42)
    st.plotly_chart(px.scatter(sample, x='discount_rate', y='margin_pct', opacity=.2, title='Discount vs record margin (sample ≤10,000)'), use_container_width=True)
    st.dataframe(bands, use_container_width=True)
    rate = st.slider('Scenario: replace ALL filtered discounts with (%)', 0.0, 50.0, 10.0, .5)
    st.dataframe(discount_scenario(d, rate / 100).to_frame('value'), use_container_width=True)
    st.warning('Scenario only: prices, quantities, implied costs and customer mix stay fixed. Observed associations do not establish a causal discount effect.')
with tabs[4]:
    level = st.selectbox('Geographic dimension', ['Market', 'Order Region', 'Order Country'])
    geo = summarize(d, [level])
    st.plotly_chart(px.bar(geo, x=level, y='profit'), use_container_width=True)
    st.dataframe(geo, use_container_width=True)
    st.subheader('Full-upload validation (before dashboard filters)')
    st.dataframe(audit, use_container_width=True)
    st.write(f'Quarantined records: {len(rejected):,}')
    st.caption('No dates, currency codes, order/line IDs or shipping cost. No PII addresses/names are displayed. No automatic FX conversion or completed-sale recognition is asserted.')
st.download_button('Download filtered summary (no customer PII)', summarize(d, ['Market', 'Category Name']).to_csv(index=False), 'filtered_summary.csv', 'text/csv')
