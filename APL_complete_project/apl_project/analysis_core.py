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
