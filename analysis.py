# %% [markdown]
# # EduPro: learner demographics and enrollment behavior
# Reproducible descriptive analysis of the supplied workbook. Each numbered step
# contains executable Python and displays its output in the companion notebook.
# A transaction is used as an enrollment proxy; it does not prove attendance,
# completion, learning outcomes, or current platform activity.
# %%
# Step 1 — Imports and reproducible output folders
from pathlib import Path
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, Image
from data_utils import load_data, segment_summary, demand_summary, preference, AGE_LABELS, LEVEL_ORDER
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 160)
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
OUT = Path('outputs')
TABLES = OUT/'tables'; FIGS = OUT/'figures'
TABLES.mkdir(parents=True,exist_ok=True); FIGS.mkdir(parents=True,exist_ok=True)
sns.set_theme(style='whitegrid', palette='colorblind', font_scale=1.05)
plt.rcParams.update({'figure.dpi':110,'savefig.dpi':170,'axes.spines.top':False,'axes.spines.right':False})

def save_table(frame,name):
    frame.to_csv(TABLES/f'{name}.csv')
    display(frame)

def show_chart(name):
    plt.tight_layout()
    path = FIGS/f'{name}.png'
    plt.savefig(path,bbox_inches='tight'); plt.close()
    display(Image(filename=str(path)))
print('Output directories ready.')
# %% [markdown]
# ## Step 2 — Load, audit, and integrate
# data_utils.load_data reads only needed fields (not names/emails), trims strings,
# rejects missing required values, duplicate primary keys, invalid ages/dates,
# orphan foreign keys and unexpected course levels, then validates many-to-one
# joins. It never silently deletes or repairs records. See data_utils.py for the
# complete implementation. Teachers and financial fields are outside scope.
# %%
users, courses, transactions, enrollments, audit = load_data()
print(f'Users: {len(users):,}; Courses: {len(courses):,}; Transactions: {len(transactions):,}; Joined rows: {len(enrollments):,}')
print(f'Coverage: {transactions.TransactionDate.min():%Y-%m-%d} to {transactions.TransactionDate.max():%Y-%m-%d}')
save_table(audit,'data_quality')
print('Age range:', int(users.Age.min()), 'to', int(users.Age.max()))
print('Personal names and email addresses excluded from analytical outputs.')
# %% [markdown]
# ## Step 3 — Define age bands and KPI denominators
# Nonoverlapping integer-age bands: <18, 18–25, 26–35, 36–45, and 46+.
# The prompt's “45+” overlaps 36–45, so 46+ is used. No users are older than 35.
# Active = at least one recorded transaction anywhere in the supplied period.
# Average per registered learner includes zero-enrollment learners if present.
# Category popularity index = category enrollments / all enrollments × 100.
# %%
learner_counts = enrollments.groupby('UserID').size().reindex(users.UserID,fill_value=0)
active_counts = learner_counts[learner_counts>0].sort_values(ascending=False)
top_n = math.ceil(0.10*len(active_counts))
kpis = pd.DataFrame({'Value': {
    'Registered learners': len(users),
    'Active learners': enrollments.UserID.nunique(),
    'Total enrollments (transaction proxy)': len(enrollments),
    'Distinct learner-course pairs': len(enrollments[['UserID','CourseID']].drop_duplicates()),
    'Catalog courses': len(courses),
    'Participation rate (%)': enrollments.UserID.nunique()/len(users)*100,
    'Mean enrollments per registered learner': len(enrollments)/len(users),
    'Mean enrollments per active learner': len(enrollments)/enrollments.UserID.nunique(),
    'Median enrollments per registered learner': learner_counts.median(),
    'Top 10% active learner enrollment share (%)': active_counts.iloc[:top_n].sum()/len(enrollments)*100,
    'Mean age': users.Age.mean(),
    'Median age': users.Age.median(),
}})
save_table(kpis,'kpis')
# %% [markdown]
# ## Step 4 — Demographics and age-wise enrollment
# Use both counts and rates: a larger enrollment total may simply reflect a
# larger learner group. Empty age groups have zero counts and undefined rates.
# %%
age_summary = segment_summary(users,enrollments,'AgeGroup')
gender_summary = segment_summary(users,enrollments,'Gender')
save_table(age_summary,'age_summary')
save_table(gender_summary,'gender_summary')
fig,axs=plt.subplots(1,2,figsize=(12,4))
users.Age.value_counts().sort_index().plot.bar(ax=axs[0],color='#147D92')
axs[0].set(title='Registered learners by age',xlabel='Age (years)',ylabel='Learners')
users.Gender.value_counts().sort_index().plot.bar(ax=axs[1],color=['#147D92','#E59A43'],rot=0)
axs[1].set(title='Registered learners by recorded gender',xlabel='',ylabel='Learners')
show_chart('01_demographics')
fig,axs=plt.subplots(1,3,figsize=(14,4))
for ax,col,title in zip(axs,['RegisteredLearners','Enrollments','EnrollmentsPerRegisteredLearner'],['Registered learners','Recorded enrollments','Enrollments per registered learner']):
    age_summary[col].plot.bar(ax=ax,color='#147D92',rot=0)
    ax.set(title=title,xlabel='Age group',ylabel='Count' if col!='EnrollmentsPerRegisteredLearner' else 'Enrollments / learner')
show_chart('02_age_participation')
# %% [markdown]
# ## Step 5 — Course category, type, and level demand
# Report enrollment shares alongside catalog supply. A high total is not proof
# of stronger preference if more courses of that type/level are offered.
# %%
category_summary = demand_summary(enrollments,courses,'CourseCategory')
type_summary = demand_summary(enrollments,courses,'CourseType')
level_summary = demand_summary(enrollments,courses,'CourseLevel')
save_table(category_summary,'category_summary')
save_table(type_summary,'type_summary')
save_table(level_summary,'level_summary')
fig,ax=plt.subplots(figsize=(10,6))
category_summary.Enrollments.sort_values().plot.barh(ax=ax,color='#147D92')
ax.set(title='Category popularity: recorded enrollments',xlabel='Enrollments',ylabel='')
show_chart('03_category_popularity')
fig,axs=plt.subplots(1,2,figsize=(11,4))
type_summary.Enrollments.plot.bar(ax=axs[0],rot=0,color='#147D92')
level_summary.reindex(LEVEL_ORDER).Enrollments.plot.bar(ax=axs[1],rot=0,color='#E59A43')
axs[0].set(title='Enrollment by course type',ylabel='Enrollments',xlabel='')
axs[1].set(title='Enrollment by course level',ylabel='Enrollments',xlabel='')
show_chart('04_type_level')
# %% [markdown]
# ## Step 6 — Age × category preferences
# Row-normalized percentages compare within-group distributions. Empty age
# groups are shown as N/A, not falsely interpreted as zero preference.
# %%
age_cat_counts, age_cat_pct = preference(enrollments,'AgeGroup','CourseCategory',AGE_LABELS)
save_table(age_cat_counts,'age_category_counts')
save_table(age_cat_pct,'age_category_percent')
fig,ax=plt.subplots(figsize=(15,4.6))
sns.heatmap(age_cat_pct,annot=True,fmt='.1f',cmap='YlGnBu',mask=age_cat_pct.isna(),ax=ax,cbar_kws={'label':'Within-age enrollment share (%)'})
ax.set(title='Age × category: within-age enrollment shares (blank = no learners)',xlabel='',ylabel='Age group')
ax.tick_params(axis='x',rotation=40)
show_chart('05_age_category_heatmap')
# %% [markdown]
# ## Step 7 — Gender × category and level; age × level
# Recorded gender has only Female/Male labels. This does not establish that the
# platform fully represents gender diversity. Shares describe enrollments, not
# unique learners per course choice (a learner can select multiple categories).
# %%
gender_cat_counts, gender_cat_pct = preference(enrollments,'Gender','CourseCategory')
gender_level_counts, gender_level_pct = preference(enrollments,'Gender','CourseLevel',col_order=LEVEL_ORDER)
age_level_counts, age_level_pct = preference(enrollments,'AgeGroup','CourseLevel',AGE_LABELS,LEVEL_ORDER)
for name, table in [('gender_category_counts',gender_cat_counts),('gender_category_percent',gender_cat_pct),('gender_level_counts',gender_level_counts),('gender_level_percent',gender_level_pct),('age_level_counts',age_level_counts),('age_level_percent',age_level_pct)]:
    save_table(table,name)
fig,axs=plt.subplots(1,2,figsize=(13,4))
gender_level_pct.plot.bar(ax=axs[0],rot=0)
axs[0].set(title='Level distribution within recorded gender',ylabel='Enrollment share (%)',xlabel='')
age_level_pct.dropna(how='all').plot.bar(ax=axs[1],rot=0)
axs[1].set(title='Level distribution within age group',ylabel='Enrollment share (%)',xlabel='')
axs[0].legend(title='Level'); axs[1].legend(title='Level')
show_chart('06_demographics_level')
fig,ax=plt.subplots(figsize=(15,3.8))
sns.heatmap(gender_cat_pct,annot=True,fmt='.1f',cmap='YlGnBu',ax=ax,cbar_kws={'label':'Within-gender enrollment share (%)'})
ax.set(title='Gender × category: within-group enrollment shares',xlabel='',ylabel='')
ax.tick_params(axis='x',rotation=40)
show_chart('07_gender_category_heatmap')
print('Largest absolute Female–Male category-share gap (percentage points):')
gaps=gender_cat_pct.loc['Female'].sub(gender_cat_pct.loc['Male']).abs().sort_values(ascending=False)
display(gaps.head().to_frame('AbsoluteGapPP'))
gaps.rename('AbsoluteGapPP').to_csv(TABLES/'gender_category_gap_pp.csv')
# %% [markdown]
# ## Step 8 — Beginner-course and advanced-course selection
# “Beginner” means the course's recorded level, NOT a verified learner skill.
# The same learner can take beginner and advanced courses. We have no skill,
# intention, completion or prior-experience fields and cannot infer progression.
# Use recorded CourseLevel even if course titles appear inconsistent.
# %%
level_type_counts, level_type_pct = preference(enrollments,'CourseLevel','CourseType',LEVEL_ORDER,['Free','Paid'])
save_table(level_type_counts,'level_type_counts')
save_table(level_type_pct,'level_type_percent')
level_type_supply = pd.crosstab(courses.CourseLevel,courses.CourseType).reindex(index=LEVEL_ORDER,columns=['Free','Paid'],fill_value=0)
save_table(level_type_supply,'level_type_catalog_supply')
normalized_level_type = level_type_counts / level_type_supply.replace(0,np.nan)
save_table(normalized_level_type,'level_type_enrollments_per_catalog_course')
level_cohorts=[]
for level in LEVEL_ORDER:
    selected=enrollments.loc[enrollments.CourseLevel.eq(level)]
    ids=selected.UserID.unique()
    level_cohorts.append({'CourseLevel':level,'Enrollments':len(selected),'UniqueLearnersSelectingLevel':len(ids),
        'MeanThisLevelEnrollmentsPerSelectingLearner':len(selected)/len(ids),
        'MeanAllLevelEnrollmentsForSelectingLearners':learner_counts.loc[ids].mean()})
level_cohorts=pd.DataFrame(level_cohorts).set_index('CourseLevel')
save_table(level_cohorts,'level_selection_cohorts')
beginner_ids=set(enrollments.loc[enrollments.CourseLevel.eq('Beginner'),'UserID'])
advanced_ids=set(enrollments.loc[enrollments.CourseLevel.eq('Advanced'),'UserID'])
print(f'Learners selecting BOTH beginner and advanced courses: {len(beginner_ids & advanced_ids):,}')
fig,ax=plt.subplots(figsize=(8,4))
level_type_pct.plot.bar(stacked=True,ax=ax,rot=0,color=['#147D92','#E59A43'])
ax.set(title='Free/paid enrollment distribution within course level',ylabel='Enrollment share (%)',xlabel='')
ax.legend(title='Course type')
show_chart('08_level_type')
print('Title/metadata review example:')
display(courses.loc[courses.CourseName.str.contains('Advanced',case=False),['CourseName','CourseLevel']])
# %% [markdown]
# ## Step 9 — Enrollment concentration and individual activity
# Top 10% = ceil(10% × active learners), ranked by enrollment count. Ties at
# the cutoff do not affect the enrollment share because tied counts are equal.
# Aggregate outputs avoid exporting individual identifiers.
# %%
activity_distribution = learner_counts.value_counts().sort_index().rename_axis('EnrollmentsPerLearner').to_frame('Learners')
activity_distribution['ShareOfLearnersPct']=activity_distribution.Learners/len(users)*100
save_table(activity_distribution,'activity_distribution')
concentration=[]
for pct in [1,5,10,20,50]:
    n=math.ceil(pct/100*len(active_counts))
    concentration.append({'TopActiveLearnersPct':pct,'Learners':n,'Enrollments':active_counts.iloc[:n].sum(),'EnrollmentSharePct':active_counts.iloc[:n].sum()/len(enrollments)*100})
concentration=pd.DataFrame(concentration).set_index('TopActiveLearnersPct')
save_table(concentration,'enrollment_concentration')
fig,axs=plt.subplots(1,2,figsize=(12,4))
activity_distribution.Learners.plot.bar(ax=axs[0],color='#147D92',rot=0)
axs[0].set(title='Recorded enrollments per learner',xlabel='Enrollments per learner',ylabel='Learners')
x=np.arange(1,len(active_counts)+1)/len(active_counts)*100
y=active_counts.cumsum().to_numpy()/len(enrollments)*100
axs[1].plot(np.r_[0,x],np.r_[0,y],color='#147D92',label='Observed concentration')
axs[1].plot([0,100],[0,100],'--',color='gray',label='Equal enrollment benchmark')
axs[1].set(title='Cumulative enrollment concentration (highest first)',xlabel='Share of active learners (%)',ylabel='Share of enrollments (%)')
axs[1].legend()
show_chart('09_activity_concentration')
# %% [markdown]
# ## Step 10 — Export reusable tables and summarize findings
# Descriptive observations are not causal effects or formal statistical tests.
# No external research, predictions or monetization analysis is required.
# %%
with pd.ExcelWriter(OUT/'edupro_summary_tables.xlsx',engine='openpyxl') as writer:
    for path in sorted(TABLES.glob('*.csv')):
        pd.read_csv(path).to_excel(writer,sheet_name=path.stem[:31],index=False)
print('KEY FINDINGS')
print(f'{len(enrollments):,} transactions; {len(users):,} registered/active learners; mean {learner_counts.mean():.2f} and median {learner_counts.median():.0f} enrollments.')
print('Largest age group by enrollment: 26–35; highest per-learner rate: <18.')
print('Data Science leads category demand; Marketing and Programming tie for lowest.')
print(f'Top {top_n} active learners account for {active_counts.iloc[:top_n].sum()/len(enrollments)*100:.2f}% of enrollment.')
print('Limitations: one transaction period; no completion/outcome/skill data; no learners over 35; recorded course metadata may need review.')
print('All aggregate tables, charts and the Excel summary workbook were generated successfully.')
