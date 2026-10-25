"""Validated, descriptive EduPro data loading; no prediction or revenue analysis."""
from pathlib import Path
import numpy as np
import pandas as pd
AGE_LABELS = ['<18', '18–25', '26–35', '36–45', '46+']
LEVEL_ORDER = ['Beginner', 'Intermediate', 'Advanced']

def find_workbook(path=None):
    if path is not None:
        return path
    for p in [Path('EduPro Online Platform.xlsx'), Path('../EduPro Online Platform.xlsx'),
              Path(__file__).resolve().parent / 'EduPro Online Platform.xlsx',
              Path(__file__).resolve().parent.parent / 'EduPro Online Platform.xlsx']:
        if p.exists():
            return p
    raise FileNotFoundError('Place EduPro Online Platform.xlsx beside the app or supply a path.')

def load_data(path=None):
    source = find_workbook(path)
    users = pd.read_excel(source, sheet_name='Users', usecols=['UserID','Age','Gender'])
    courses = pd.read_excel(source, sheet_name='Courses', usecols=['CourseID','CourseName','CourseCategory','CourseType','CourseLevel'])
    tx = pd.read_excel(source, sheet_name='Transactions', usecols=['TransactionID','UserID','CourseID','TransactionDate'])
    audit = []
    for name, frame, key in [('Users',users,'UserID'),('Courses',courses,'CourseID'),('Transactions',tx,'TransactionID')]:
        for col in frame.select_dtypes(include='object'):
            frame[col] = frame[col].str.strip().replace('', pd.NA)
        missing = int(frame.isna().sum().sum())
        duplicates = int(frame[key].duplicated().sum())
        audit.append({'Check':name+' required-field missing cells','Value':missing})
        audit.append({'Check':name+' duplicate primary IDs','Value':duplicates})
        if missing or duplicates:
            raise ValueError(f'{name}: {missing} missing required cells; {duplicates} duplicate IDs. Resolve before analysis.')
    users['Age'] = pd.to_numeric(users['Age'], errors='raise')
    if not (users.Age.between(0,120) & users.Age.mod(1).eq(0)).all():
        raise ValueError('Age must be an integer from 0 to 120; inspect exceptions.')
    tx['TransactionDate'] = pd.to_datetime(tx.TransactionDate, errors='raise')
    if tx.TransactionDate.isna().any():
        raise ValueError('Missing transaction dates after parsing.')
    for label, key, valid in [('Unmatched UserID','UserID',users.UserID),('Unmatched CourseID','CourseID',courses.CourseID)]:
        n = int((~tx[key].isin(valid)).sum())
        audit.append({'Check':label,'Value':n})
        if n:
            raise ValueError(f'{n} {label} records')
    if not set(courses.CourseLevel).issubset(LEVEL_ORDER):
        raise ValueError('Unexpected CourseLevel; review before ordering levels.')
    users['AgeGroup'] = pd.cut(users.Age, [-np.inf,17,25,35,45,np.inf], labels=AGE_LABELS)
    enrollments = tx.merge(users,on='UserID',how='left',validate='many_to_one').merge(courses,on='CourseID',how='left',validate='many_to_one')
    assert len(enrollments) == len(tx), 'Join unexpectedly changed transaction count'
    audit += [{'Check':'Joined rows','Value':len(enrollments)},
              {'Check':'Repeated user-course pairs (not deleted)','Value':int(tx.duplicated(['UserID','CourseID']).sum())}]
    return users, courses, tx, enrollments, pd.DataFrame(audit)

def segment_summary(users, enrollments, column):
    grouped = users.groupby(column, observed=False).agg(RegisteredLearners=('UserID','size'))
    grouped = grouped.join(enrollments.groupby(column, observed=False).agg(ActiveLearners=('UserID','nunique'),Enrollments=('TransactionID','size'))).fillna(0)
    grouped['LearnerSharePct'] = grouped.RegisteredLearners / len(users) * 100
    grouped['EnrollmentSharePct'] = grouped.Enrollments / len(enrollments) * 100 if len(enrollments) else 0
    grouped['ParticipationRatePct'] = grouped.ActiveLearners / grouped.RegisteredLearners.replace(0,np.nan) * 100
    grouped['EnrollmentsPerRegisteredLearner'] = grouped.Enrollments / grouped.RegisteredLearners.replace(0,np.nan)
    grouped['EnrollmentsPerActiveLearner'] = grouped.Enrollments / grouped.ActiveLearners.replace(0,np.nan)
    return grouped

def demand_summary(enrollments, courses, column):
    out = courses.groupby(column).agg(CatalogCourses=('CourseID','nunique')).join(enrollments.groupby(column).agg(Enrollments=('TransactionID','size'),ActiveLearners=('UserID','nunique'))).fillna(0)
    out['EnrollmentSharePct'] = out.Enrollments / len(enrollments) * 100 if len(enrollments) else 0
    out['EnrollmentsPerCatalogCourse'] = out.Enrollments / out.CatalogCourses
    # Category popularity index = enrollment share as a percentage, not an unexplained score.
    return out.sort_values('Enrollments',ascending=False)

def preference(enrollments, row, col, row_order=None, col_order=None):
    counts = pd.crosstab(enrollments[row],enrollments[col],dropna=False)
    if row_order is not None: counts = counts.reindex(row_order,fill_value=0)
    if col_order is not None: counts = counts.reindex(columns=col_order,fill_value=0)
    shares = counts.div(counts.sum(axis=1).replace(0,np.nan),axis=0)*100
    return counts, shares
