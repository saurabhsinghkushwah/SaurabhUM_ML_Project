# EduPro: learner demographics and course enrollment behavior

## What to open first

1. **EduPro_step_by_step.ipynb** — ten numbered steps containing executable Python and the **actual executed outputs**, including tables and nine chart files. Download the full package to retain the shared data utility module.
2. **outputs/EduPro_research_paper.pdf** — nine-page research paper with methodology, EDA, findings, limitations and recommendations. An editable Word version is included.
3. **outputs/EduPro_executive_summary.pdf** — one-page briefing for education/government stakeholders; editable Word version included.
4. **outputs/edupro_summary_tables.xlsx** — all aggregate result tables in one workbook.
5. **app.py** — interactive Streamlit dashboard source. Ready to launch, not hosted on a public URL.
6. **step_by_step_code_and_outputs.md** — readable text version of notebook code and executed outputs; charts referenced from outputs/figures.

## Input

Use the original `EduPro Online Platform.xlsx` supplied in the conversation. Put it in this folder beside `app.py` and `analysis.py`. The package deliberately does **not** contain the original workbook or learner-level extracts, because the workbook contains personal information. The app can alternatively accept an uploaded workbook.

Required sheets/fields:
- Users: UserID, Age, Gender.
- Courses: CourseID, CourseName, CourseCategory, CourseType, CourseLevel.
- Transactions: TransactionID, UserID, CourseID, TransactionDate.

Teachers, names, email, prices and payment fields are not required for this scope. The username field mentioned in the brief is unnecessary for any KPI and is deliberately not loaded.

## Setup — step by step

Use Python 3.11 or newer. In a terminal opened in this folder:

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

The tested package versions for the original execution are recorded in `environment_versions.txt`. Version ranges in requirements are compatibility ranges, not an exact lockfile.

### Option A — notebook: code plus outputs

```bash
jupyter notebook EduPro_step_by_step.ipynb
```

The notebook already contains all executed results. Use **Kernel → Restart & Run All** to reproduce them with the original workbook. Run from this folder so the adjacent `data_utils.py` is importable.

### Option B — plain Python analysis

```bash
python analysis.py
```

This regenerates aggregate CSVs, the summary Excel workbook and chart images in `outputs/`. In a terminal, dataframe outputs are printed; figures are saved even if the terminal cannot display IPython images. The notebook is the preferred way to view code and plots together.

### Option C — Streamlit dashboard

```bash
streamlit run app.py
```

Open the local address printed by Streamlit (normally localhost, port 8501).

- Sidebar filters: age group, recorded gender, course category, course level, course type.
- Five tabs: learner overview; age-wise enrollment; gender preferences; category/level popularity; activity/data quality.
- Filters update outputs immediately. No matching records produce informative empty states.
- Registered learner denominators respond to **age and gender** filters only. Course filters narrow transactions and matching active learners, not the registered learner base.
- Download buttons export aggregates, never learner names/emails/IDs.
- No external streaming data source is connected. Upload a new workbook to refresh source data.

### Rebuild reports (optional)

```bash
python build_reports.py
```

Reports contain narrative specific to the supplied workbook. Rerun the analysis first. If the source changes, manually review/update report commentary and benchmark assertions; do not assume the original prose remains valid.

### Run automated checks

```bash
python test_project.py
```

Checks include expected row counts and joins, empty-age-group rates, normalized preference totals, concentration, and four Streamlit smoke-test scenarios. The test expectations deliberately refer to the original supplied workbook.

## Deployment notes

To deploy using a Streamlit-compatible host, select `app.py` as the entry point and install `requirements.txt`. Keep `data_utils.py` beside it. You can omit the workbook from the deployment repository and upload it at runtime. Do not commit learner personal information to a public repository. For sensitive use, use an appropriately authenticated private deployment. No public deployment or hosting account was created as part of this deliverable.

## How to interpret the analysis

- Enrollment = one recorded transaction; all 10,000 learner/course pairs are distinct in this workbook.
- Active = at least one transaction in the observed period, **2025-01-01 through 2025-12-30**, not currently active in October 2026.
- Users sheet is treated as the registered learner base. All 3,000 appear in Transactions, so registered and active means coincide here.
- Age bands: <18, 18–25, 26–35, 36–45, 46+. The last band avoids overlap with age 45.
- No learners are older than 35; older groups have N/A preference/rate outputs, not inferred low demand.
- Course level is a course attribute, not a learner skill label. Beginner and Advanced learner-selection groups overlap.
- Category popularity index is explicitly defined as the category enrollment share (%).
- Catalog supply matters: 38 Free versus 22 Paid courses; level supply is 21 Beginner, 18 Intermediate and 21 Advanced.
- The source labels Advanced Python as Beginner; no automatic relabeling is applied.
- The observed absence of 5–8 enrollments per learner warrants provenance review; no cause is established.
- Recorded gender labels are only Female/Male. This is a source limitation, not a claim about gender diversity.
- No outcomes, completions, learning goals, verified skill levels, causal effects, predictions or monetization are inferred.

## Expected headline outputs

| Metric | Value |
|---|---:|
| Users | 3,000 |
| Courses | 60 |
| Transactions / joined enrollments | 10,000 |
| Distinct enrolled learners | 3,000 |
| Mean / median enrollments | 3.33 / 1 |
| 26–35 enrollment count | 4,799 |
| Under-18 enrollments per learner | 3.39 |
| Data Science enrollments | 916 |
| Beginner-course enrollments | 3,573 |
| Free-course enrollments | 6,403 |
| Top 10% active learner share | 42.34% |
| Learners with one enrollment | 1,620 (54%) |

## Project structure

```text
edupro_analysis/
  README.md
  requirements.txt
  environment_versions.txt
  data_utils.py
  analysis.py
  EduPro_step_by_step.ipynb
  step_by_step_code_and_outputs.md
  app.py
  build_reports.py
  test_project.py
  outputs/
    EduPro_research_paper.pdf / .docx
    EduPro_executive_summary.pdf / .docx
    edupro_summary_tables.xlsx
    validation_results.json
    validation_log.txt
    tables/*.csv
    figures/*.png
```

Sources: user-supplied workbook and project brief only. No external facts or fabricated survey results are used. Government stakeholder relevance is an intended reporting audience, not evidence that EduPro represents a government program.
