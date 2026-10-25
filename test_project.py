"""Run: python test_project.py. Requires the original workbook."""
import json
from pathlib import Path
import pandas as pd
from data_utils import load_data, segment_summary, preference, AGE_LABELS
u,c,t,e,a=load_data()
assert (len(u),len(c),len(t),len(e)) == (3000,60,10000,10000)
assert e.UserID.nunique()==3000
assert t.duplicated(['UserID','CourseID']).sum()==0
assert e.CourseCategory.value_counts()['Data Science']==916
summary=segment_summary(u,e,'AgeGroup')
assert summary.loc['26–35','Enrollments']==4799
assert summary.loc['36–45','RegisteredLearners']==0
assert pd.isna(summary.loc['36–45','EnrollmentsPerRegisteredLearner'])
counts,pct=preference(e,'AgeGroup','CourseCategory',AGE_LABELS)
assert abs(pct.loc['<18'].sum()-100)<1e-8
assert pct.loc['36–45'].isna().all()
assert e.groupby('UserID').size().nlargest(300).sum()==4234
from streamlit.testing.v1 import AppTest
app=AppTest.from_file(str(Path(__file__).parent/'app.py'),default_timeout=60).run()
assert not app.exception
checks=[]
def metrics():return {m.label:m.value for m in app.metric}
checks.append({'Scenario':'Unfiltered dashboard','Pass':True,'Metrics':metrics()})
assert metrics()['Matching enrollments']=='10,000'
app.sidebar.multiselect[0].set_value(['36–45']).run()
assert not app.exception and metrics()['Matching enrollments']=='0'
checks.append({'Scenario':'Empty older age group','Pass':True,'Metrics':metrics()})
app.sidebar.multiselect[0].set_value(['18–25']).run()
app.sidebar.multiselect[2].set_value(['Data Science']).run()
assert not app.exception
assert metrics()['Registered learners in segment']=='1,121'
assert metrics()['Matching enrollments']=='343'
checks.append({'Scenario':'18–25 / Data Science','Pass':True,'Metrics':metrics()})
app.sidebar.multiselect[2].set_value([]).run()
assert not app.exception and metrics()['Matching enrollments']=='0'
assert metrics()['Registered learners in segment']=='1,121'
checks.append({'Scenario':'Empty category selection','Pass':True,'Metrics':metrics()})
Path('outputs/validation_results.json').write_text(json.dumps({'DataAssertions':'PASS','DashboardSmokeTests':checks},indent=2))
print('PASS: dataset counts, validated joins, preference denominators, empty-group rates and concentration.')
for check in checks: print('PASS:',check['Scenario'],check['Metrics'])
