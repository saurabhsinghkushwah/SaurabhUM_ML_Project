"""Run with: streamlit run app.py"""
from io import BytesIO
import pandas as pd
import plotly.express as px
import streamlit as st
from data_utils import load_data, segment_summary, preference, AGE_LABELS, LEVEL_ORDER
st.set_page_config(page_title='EduPro Learner Intelligence',page_icon='📚',layout='wide')
st.title('EduPro | Learner demographics & enrollment behavior')
st.caption('Descriptive analytics • Enrollment = recorded transaction • No prediction or monetization')

@st.cache_data(show_spinner=False)
def read_workbook(payload):
    return load_data(BytesIO(payload) if payload is not None else None)

uploaded=st.sidebar.file_uploader('Upload EduPro workbook (.xlsx)',type=['xlsx'])
try:
    users,courses,tx,enrollments,audit=read_workbook(uploaded.getvalue() if uploaded else None)
except Exception as exc:
    st.error(f'Unable to load a validated workbook: {exc}')
    st.info('Place the original workbook beside app.py, or upload it with the sidebar.')
    st.stop()
st.sidebar.header('Filters')
ages=st.sidebar.multiselect('Age groups',AGE_LABELS,default=AGE_LABELS)
genders=st.sidebar.multiselect('Recorded gender',sorted(users.Gender.unique()),default=sorted(users.Gender.unique()))
categories=st.sidebar.multiselect('Course category',sorted(courses.CourseCategory.unique()),default=sorted(courses.CourseCategory.unique()))
levels=st.sidebar.multiselect('Course level',LEVEL_ORDER,default=LEVEL_ORDER)
types=st.sidebar.multiselect('Course type',sorted(courses.CourseType.unique()),default=sorted(courses.CourseType.unique()))
st.sidebar.caption('Empty selection means no matching records. Use the × controls to narrow selections.')
selected_users=users.loc[users.AgeGroup.isin(ages)&users.Gender.isin(genders)]
selected_courses=courses.loc[courses.CourseCategory.isin(categories)&courses.CourseLevel.isin(levels)&courses.CourseType.isin(types)]
f=enrollments.loc[enrollments.UserID.isin(selected_users.UserID)&enrollments.CourseID.isin(selected_courses.CourseID)]
registered=len(selected_users); active=f.UserID.nunique()
a,b,c,d,e=st.columns(5)
a.metric('Registered learners in segment',f'{registered:,}')
b.metric('Learners with matching enrollments',f'{active:,}')
c.metric('Matching enrollments',f'{len(f):,}')
d.metric('Enrollments / registered learner',f'{len(f)/registered:.2f}' if registered else 'N/A')
e.metric('Matching participation rate',f'{active/registered*100:.1f}%' if registered else 'N/A')
st.info('Denominators: registered learners respond only to age/gender filters. Course filters narrow enrollments and matching active learners, not the registered learner base. Participation is at least one matching transaction in the workbook period.')
st.caption(f'Workbook coverage: {tx.TransactionDate.min():%Y-%m-%d} to {tx.TransactionDate.max():%Y-%m-%d}. No attendance, completion or skill status is implied.')
tabs=st.tabs(['Learner overview','Age-wise enrollment','Gender preferences','Category & level popularity','Activity & quality'])
with tabs[0]:
    st.subheader('Registered learner demographics')
    if registered:
        a,b=st.columns(2)
        by_age=selected_users.groupby('AgeGroup',observed=False).size().rename('Learners').reset_index()
        by_gender=selected_users.groupby('Gender').size().rename('Learners').reset_index()
        a.plotly_chart(px.bar(by_age,x='AgeGroup',y='Learners',title='Registered learners by age group'),use_container_width=True)
        b.plotly_chart(px.bar(by_gender,x='Gender',y='Learners',title='Registered learners by recorded gender'),use_container_width=True)
        st.dataframe(selected_users.Age.describe().to_frame('Age (years)'),use_container_width=True)
    else: st.warning('No registered learners match these demographic filters.')
with tabs[1]:
    st.subheader('Age participation and course preferences')
    if registered:
        summary=segment_summary(selected_users,f,'AgeGroup')
        st.dataframe(summary,use_container_width=True)
        st.plotly_chart(px.bar(summary.reset_index(),x='AgeGroup',y='Enrollments',title='Matching enrollments by age group'),use_container_width=True)
    if len(f):
        _,pct=preference(f,'AgeGroup','CourseCategory',AGE_LABELS)
        st.plotly_chart(px.imshow(pct,aspect='auto',text_auto='.1f',color_continuous_scale='Blues',labels={'color':'Share (%)'},title='Within-age category enrollment share (%)'),use_container_width=True)
    else: st.warning('No enrollments match the selected filters.')
with tabs[2]:
    st.subheader('Gender-based course selection')
    if len(f):
        for col in ['CourseCategory','CourseLevel']:
            counts,pct=preference(f,'Gender',col,col_order=LEVEL_ORDER if col=='CourseLevel' else None)
            long=pct.rename_axis('Gender').reset_index().melt(id_vars='Gender',var_name=col,value_name='SharePct')
            st.plotly_chart(px.bar(long,x='Gender',y='SharePct',color=col,barmode='group',title=f'{col}: within-gender enrollment shares (%)'),use_container_width=True)
            st.dataframe(counts,use_container_width=True)
    else: st.warning('No enrollments match the selected filters.')
    st.caption('Only recorded gender labels are shown. Small descriptive differences do not demonstrate a causal gender effect.')
with tabs[3]:
    st.subheader('Popularity and catalog context')
    if len(f):
        for col in ['CourseCategory','CourseType','CourseLevel']:
            counts=f.groupby(col).size().rename('Enrollments').to_frame()
            counts['EnrollmentSharePct']=counts.Enrollments/len(f)*100
            counts['CatalogCourses']=selected_courses.groupby(col).CourseID.nunique()
            counts['EnrollmentsPerCatalogCourse']=counts.Enrollments/counts.CatalogCourses
            counts=counts.sort_values('Enrollments',ascending=False)
            st.plotly_chart(px.bar(counts.reset_index(),x=col,y='Enrollments',title=f'Enrollment distribution: {col}'),use_container_width=True)
            st.dataframe(counts,use_container_width=True)
        _,pct=preference(f,'CourseLevel','CourseType',LEVEL_ORDER)
        st.write('Course type within recorded course level (%)')
        st.dataframe(pct,use_container_width=True)
    else: st.warning('No enrollments match the selected filters.')
    st.caption('Category popularity index is enrollment share (%). Course level is metadata, not a learner skill assessment.')
with tabs[4]:
    st.subheader('Activity concentration')
    if active:
        activity=f.groupby('UserID').size().sort_values(ascending=False)
        n=max(1,__import__('math').ceil(.10*active))
        st.metric('Enrollment share of top 10% matching active learners',f'{activity.iloc[:n].sum()/len(f)*100:.2f}%')
        dist=activity.value_counts().sort_index().rename_axis('EnrollmentsPerLearner').reset_index(name='Learners')
        st.plotly_chart(px.bar(dist,x='EnrollmentsPerLearner',y='Learners',title='Matching enrollments per active learner'),use_container_width=True)
        st.caption(f'Top 10% uses {n:,} learners, rounded up. Learners are ranked by matching enrollment count.')
    st.write('Workbook validation (unfiltered)')
    st.dataframe(audit,use_container_width=True,hide_index=True)
    st.warning('Coverage limits: supplied ages are 15–35; empty older groups are not evidence of low demand. No completion, learning-goal or outcome data. Course titles may conflict with assigned levels (e.g., Advanced Python is labeled Beginner).')
    st.write('Aggregate exports only — no learner names, emails or identifiers.')
    if registered:
        st.download_button('Download filtered age summary (CSV)',segment_summary(selected_users,f,'AgeGroup').to_csv().encode('utf-8'),file_name='filtered_age_summary.csv',mime='text/csv')
    if len(f):
        export=f.groupby(['AgeGroup','Gender','CourseCategory','CourseLevel','CourseType'],observed=True).size().rename('Enrollments').reset_index()
        st.download_button('Download filtered aggregate enrollments (CSV)',export.to_csv(index=False).encode('utf-8'),file_name='filtered_enrollment_aggregates.csv',mime='text/csv')
