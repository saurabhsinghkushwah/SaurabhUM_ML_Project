# APL Logistics profitability project

## Start here
1. Extract this project folder.
2. Put the original supplied CSV beside the notebook (or one folder above it).
3. Open a terminal in this folder and run:

    python -m pip install -r requirements.txt

4. Open APL_cell_by_cell.ipynb in Jupyter or VS Code. Run numbered cells 01–22 in order. The Python companion contains the same cells as # %% sections. Cell 03 includes the full analysis functions, not just an import.
5. Start the interactive dashboard from a terminal:

    streamlit run app.py

You may also upload the CSV inside the dashboard. Keep analysis_core.py and report_builder.py beside the notebook and app. On Colab, upload the project files and dataset into the same working folder; Streamlit is intended for a local machine or hosted app, not a normal notebook output cell.

## Included
- Executed notebook, cell-by-cell Python companion and full helper source.
- Streamlit dashboard: overview, customers, product/category heatmap, discount diagnostics/scenarios and geography/quality.
- Research paper and government-stakeholder executive summary, in Word and Markdown.
- CSV tables, validation audit, scenario results and charts under outputs.

## Validation
All 22 analysis cells executed successfully in the preparation environment (the installation cell was skipped because analysis dependencies were present). Streamlit was separately installed and its AppTest completed with no dashboard exceptions. This is a runnable dashboard, not a publicly deployed live service. Dependency ranges are provided, not a fully locked environment.

## Important boundaries
All statuses are included by default. COMPLETE/CLOSED is only a sensitivity proxy, not verified recognized revenue. Monetary units are unspecified. Gross sales, net revenue, and reported profit are separate; financial aliases are never added together. Negative profits are retained. No dates, transaction IDs, shipping costs, or currency codes exist in the input. No causal discount or forecasting claim is made. Scenarios hold costs, quantities and gross prices fixed. Row-level reconciliation tolerates 0.02 currency units; accumulated rounding produces a 46.13-unit aggregate gross/discount/net residual.

The original CSV is intentionally not duplicated in this archive; use the supplied input. Customer-level output contains customer identifiers: restrict access. Notebook preview avoids names, street addresses and coordinates. Public reports aggregate findings.
