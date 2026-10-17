# Customer, Product, and Profitability Performance Analysis in Supply Chain Operations
## Research paper: analysis of the supplied APL Logistics case dataset

## Abstract
This descriptive study evaluates 180,519 retained records and 20,652 customer identifiers from the supplied CSV. Gross sales total 36,784,734.31, net revenue 33,054,402.04, and reported profit 3,966,902.97, producing a weighted net margin of 12.00%. All monetary amounts are dataset currency units; no currency code was provided. The analysis identifies 4,069 loss-making customers, 3 loss-making products and 0 loss-making categories. Results support prioritization and further validation, not audited revenue recognition or causal pricing conclusions.

## 1. Research questions and scope
Which customers, products, categories and destination markets contribute profit rather than merely sales? How are observed discounts associated with reported margins? What does a fixed-cost pricing scenario imply? This study follows the supplied project requirements. The entity label comes from the assignment, and the file's provenance and accounting completeness have not been independently verified. The population is the supplied file, not necessarily the provider's actual operations.

## 2. Data and financial validation
The input contains 40 columns. It has no order date, shipping date, unique order or line identifier, currency identifier, exchange rate, or explicit shipping-cost field. The analysis therefore treats observations as records/apparent item-level economics, does not report distinct orders, and does not construct time trends. Shipping-cost erosion cannot be isolated.

The CSV is read using UTF-8 with a Windows-1252 fallback. Text is trimmed; numeric conversion is explicit. Invalid/missing financial values, nonpositive revenue, invalid quantities, invalid discount rates and inconsistent financial aliases or customer identifiers are quarantined. A two-cent absolute reconciliation tolerance is used for rounded financial fields. Retained records total 180,519; quarantined records total 0. Exact duplicate rows, if encountered, are not automatically removed because identity cannot be established without record keys. Negative profit is retained because loss diagnosis is central to the assignment. Nonfinancial missing names or postal codes do not justify removing financially valid rows.

Sales reconciles to quantity times item price. Net revenue reconciles to Sales minus the discount amount. Benefit per order duplicates Order Profit Per Order, while Sales per customer duplicates Order Item Total. The aliases are not added together. The recorded discount rate is rounded and can differ from discount amount divided by gross sales; monetary reconciliation uses the recorded discount amount. All order statuses remain in the primary scope, with a separate COMPLETE/CLOSED sensitivity proxy.

## 3. Methods and KPI definitions
Gross revenue is the sum of Sales, satisfying the brief's total-revenue definition. Net revenue is the sum of Order Item Total. Profit is the sum of Order Profit Per Order once. The primary margin is total profit divided by total net revenue, multiplied by 100. Profit divided by gross sales is reported separately (10.78%). Category and market margins are revenue-weighted, not unweighted averages of row ratios.

Customer Value Index is explicitly defined here as each customer's aggregate reported profit; it is a project-specific definition rather than a standardized external index. Positive-profit customers at or above their 80th-percentile profit cutoff form the high-value tier. Other profitable customers form the positive core; customers with zero or negative aggregate profit form the nonpositive tier. A secondary low-margin flag uses positive profit with margin below 5%. These are transparent managerial thresholds rather than learned optimal boundaries.

Product prioritization uses the top quartile of product revenue combined with the bottom quartile of product margin. Strong-revenue/weak-margin markets have revenue at or above the market median and margin below the full portfolio. Discount bands and rank correlations are descriptive. Product/market stratification with at least 30 records per cell reduces some mix effects but is not causal identification. No significance tests or causal confidence intervals are asserted.

## 4. Revenue and reported profit results
Gross sales: 36,784,734.31; discounts: 3,730,378.40; net revenue: 33,054,402.04; reported profit: 3,966,902.97. The primary weighted net margin is 12.00%.

Restricting to COMPLETE/CLOSED records yields net revenue 14,476,738.43, reported profit 1,779,716.84, and margin 12.29%. This demonstrates sensitivity to order-status scope, not verified recognized revenue. Pending, canceled and suspected-fraud records should be reconciled with the accounting owner before external reporting. Revenue and margin time trends cannot be assessed in the supplied file.

### Status breakdown
| Order Status | net_revenue | profit | margin_pct |
|---|---|---|---|
| COMPLETE | 10,859,271.62 | 1,321,735.75 | 12.17 |
| PENDING_PAYMENT | 7,286,275.56 | 843,810.24 | 11.58 |
| PROCESSING | 4,051,380.73 | 494,825.87 | 12.21 |
| CLOSED | 3,617,466.81 | 457,981.09 | 12.66 |
| PENDING | 3,704,456.19 | 435,725.85 | 11.76 |
| ON_HOLD | 1,780,237.68 | 208,913.04 | 11.74 |
| SUSPECTED_FRAUD | 741,492.31 | 85,136.71 | 11.48 |
| CANCELED | 668,244.98 | 75,345.63 | 11.28 |
| PAYMENT_REVIEW | 345,576.16 | 43,428.79 | 12.57 |

## 5. Customer contribution
There are 4,069 customers with negative aggregate profit; their combined reported loss is -1,080,299.72. The top 20% of positive-profit customers account for 53.81% of the positive-profit pool. This concentration metric uses positive profits as the denominator so losses do not create misleading contribution percentages. It is not a percentage of net portfolio profit. Customer IDs in detailed outputs require restricted access and should not appear in public executive reports.

### Segment economics
| Customer Segment | net_revenue | profit | margin_pct |
|---|---|---|---|
| Consumer | 17,164,278.19 | 2,073,487.67 | 12.08 |
| Corporate | 10,030,649.80 | 1,202,574.96 | 11.99 |
| Home Office | 5,859,474.05 | 690,840.34 | 11.79 |

## 6. Product and category profitability
The highest-profit category is Fishing with reported profit 756,220.76 and margin 12.14%. The lowest-profit category is Strength Training with profit 332.31. There are 0 negative-profit categories; a low-margin category should not be mislabeled as loss-making when its total profit is positive.

### Top categories by profit
| Category Name | net_revenue | profit | margin_pct |
|---|---|---|---|
| Fishing | 6,226,935.12 | 756,220.76 | 12.14 |
| Cleats | 3,982,856.45 | 494,636.92 | 12.42 |
| Camping & Hiking | 3,700,783.54 | 427,455.57 | 11.55 |
| Cardio Equipment | 3,320,250.72 | 383,011.10 | 11.54 |
| Women's Apparel | 2,828,708.50 | 350,421.03 | 12.39 |
| Water Sports | 2,798,044.10 | 325,146.96 | 11.62 |
| Indoor/Outdoor Games | 2,596,454.04 | 318,451.43 | 12.26 |
| Men's Footwear | 2,598,494.44 | 311,902.82 | 12.00 |
| Shop By Sport | 1,177,185.62 | 129,813.96 | 11.03 |
| Computers | 595,395.00 | 69,656.81 | 11.70 |

### Bottom products by reported profit
| Product Name | net_revenue | profit | margin_pct |
|---|---|---|---|
| SOLE E35 Elliptical | 26,409.85 | -965.12 | -3.65 |
| Bushnell Pro X7 Jolt Slope Rangefinder | 6,062.89 | -255.95 | -4.22 |
| SOLE E25 Elliptical | 9,414.90 | -169.56 | -1.80 |
| GoPro HERO3+ Black Edition Camera | 11,601.68 | 245.63 | 2.12 |
| Diamondback Girls' Clarity 24 Hybrid Bike 201 | 7,624.22 | 284.42 | 3.73 |

## 7. Discount diagnostics and modeled scenarios
The Spearman association between recorded discount rate and record-level net margin is -0.0015. This is observational: discounts may vary with product, customer, geography, transaction status and underlying costs. Different observed group margins cannot be interpreted as the profit caused by discounts.

### Observed discount-band economics
| discount_band | rows | net_revenue | profit | margin_pct |
|---|---|---|---|---|
| 0% | 10,028.00 | 2,042,369.14 | 267,412.40 | 13.09 |
| >0–5% | 50,143.00 | 9,909,225.72 | 1,171,682.08 | 11.82 |
| >5–10% | 40,116.00 | 7,530,117.51 | 926,511.63 | 12.30 |
| >10–15% | 30,087.00 | 5,314,179.64 | 625,339.12 | 11.77 |
| >15–20% | 40,116.00 | 6,725,259.47 | 784,061.02 | 11.66 |
| >20% | 10,029.00 | 1,533,250.56 | 191,896.72 | 12.52 |

Discount Impact Ratio is defined as discounts divided by (reported profit plus discounts), multiplied by 100: 48.46%. It measures the modeled share of no-discount profit removed by recorded discounts, assuming unchanged costs, quantities and prices. It is not the observed margin difference between discounted and non-discounted groups. The corresponding modeled margin erosion is 8.92 percentage points.

A zero-discount scenario gives modeled profit 7,697,235.24. The apparent uplift restores the gross-to-net difference mechanically; it is not a sales forecast. The aggregate residual between gross sales minus recorded discounts and reported net revenue is -46.13 currency units. All individual rows reconcile within the two-cent tolerance, but accumulated rounding means recorded discounts and gross-to-net differences are not identical. The scenario uses reported net revenue and inferred costs; the Discount Impact Ratio uses recorded discount amounts. For each scenario, modeled net revenue equals gross sales times one minus the replacement discount rate. Modeled profit equals this revenue less implied cost, where implied cost equals observed net revenue minus reported profit. Costs are inferred residuals, not independently measured logistics or shipping costs. Demand response, competitor actions, capacity and customer retention are excluded. No universal causal discount threshold can be justified by these records.

## 8. Market and regional diagnostics
| Market | net_revenue | profit | margin_pct |
|---|---|---|---|
| Europe | 9,769,198.23 | 1,169,442.96 | 11.97 |
| LATAM | 9,235,761.99 | 1,123,321.61 | 12.16 |
| Pacific Asia | 7,434,262.58 | 857,753.44 | 11.54 |
| USCA | 4,553,499.87 | 564,313.78 | 12.39 |
| Africa | 2,061,679.37 | 252,071.18 | 12.23 |

Markets meeting the stated high-revenue/weak-margin screening rule: Europe, Pacific Asia. Geography refers to order destination, not the customer's registered country. Country labels are preserved as supplied because standardization needs a reviewed reference mapping. Region and country summaries are exported for more granular review.

## 9. Recommendations and implementation
- Protect profitable high-value relationships with service-level reviews, while avoiding blanket discounts justified only by revenue.
- Investigate loss-making customers and products for cost allocation, returns, fraud/status effects and unusual pricing before withdrawing service or delisting products.
- Review high-revenue/low-margin products and weak-margin markets using the explicit screening rules; validate unit economics against the ledger.
- Pilot discount guardrails in a controlled experiment, accounting for product mix, demand, costs and retention. Do not use descriptive bands as proven optimal price thresholds.
- Use the dashboard to inspect customer tiers, category/market heatmaps, order-status sensitivity and fixed-cost pricing scenarios.
- Obtain dates, order/line keys, currency codes, exchange rates, shipping costs, returns, taxes, and approved recognition rules before extending to time trends or accounting-grade reporting.

## 10. Government-stakeholder governance and limitations
Public-facing reporting should use aggregated markets/categories rather than customer identifiers, names, addresses or coordinates. Restrict access, review retention periods, and confirm dataset licensing and provenance. Findings are a case-study diagnostic rather than evidence of government spending performance or actual corporate financial outcomes. No taxpayer savings, policy impact, causality or currency denomination is inferred. Generalizability beyond the supplied dataset is unknown.

## Conclusion
Sales alone can conceal weak customer and product economics. This reproducible workflow separates gross sales, net revenue and reported profit, retains losses and explains discount assumptions. Further business action depends on validating costs, recognition policies and source-system metadata.

## Sources and reproducibility
1. User-supplied project brief (paste.txt): scope, fields, KPIs and dashboard requirements.
2. User-supplied APL_Logistics (1).csv: all empirical calculations.
3. Accompanying executed notebook, shared analysis functions, validation exports and dashboard source: computational methods.
No external company claims or literature findings are introduced. This is a reproducible analytical case-study paper, not a systematic literature review.
