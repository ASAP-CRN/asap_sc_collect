# conda create -n sl11 python=3.11 pip streamlit pandas numpy great-expectations


import numpy as np
import pandas as pd
import streamlit as st
import os

from pathlib import Path

from utils.qcutils import validate_table
from utils.io import ReportCollector, read_file, load_css,get_dtypes_dict


# invalid_df = pd.DataFrame({
#     "year": ["2001", "2002", "1999"],
#     "month": ["3", "6", "12"],
#     "day": ["200", "156", "365"],
# })

# transform(invalid_df)

# we use this as data location
DATA_PATH_URL = "/Users/ergonyc/Projects/ASAP/meta-clean/clean"
DATA_DEFAULT = "team-Hafler"

LOAD_DATA = "load metadata table(s)"
VALIDATE = "validate tables"
DOWNLOAD = "download report"

LOG_NAME = "report.md"

load_css("css/css.css")




# Define some custom functions
def read_file(data_file,dtypes_dict):
    if data_file.type == "text/csv":
        df = pd.read_csv(data_file,dtype=dtypes_dict)        
        # df = read_meta_table(table_path,dtypes_dict)
    # assume that the xlsx file remembers the dtypes
    elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(data_file, sheet_name=0)
    return (df)


# @st.cache
# def general_ge_check(df):
#     context = ge.data_context.DataContext()
#     return context


# Download files and make its content available as a string.
@st.cache_data
def load_data(data_file, dtypes):
    tables = [dat_f.name.split('.')[0] for dat_f in data_file]

    dfs = { dat_f.name.split('.')[0]:read_file(dat_f,dtypes) for dat_f in data_file }

    return tables,dfs

@st.cache_data
def setup_report_data(report_dat:dict,table_choice:str, dfs:dict, CDE_df:pd.DataFrame):

    df = dfs[table_choice]
    specific_cde_df = CDE_df[CDE_df['Table'] == table_choice]

    dat = (df,specific_cde_df)

    report_dat[table_choice] = dat
    return report_dat

@st.cache_data
def read_CDE():
    # Construct the path to CSD.csv
    cde_file_path = "ASAP_CDE.csv"
    CDE_df = pd.read_csv(cde_file_path)
    dtypes_dict = get_dtypes_dict(CDE_df)
    return CDE_df, dtypes_dict

# @st.cache_data
# def convert_df(df):
#    return df.to_csv(index=False).encode('utf-8')


def main():
    # Construct the path to CSD.csv

    CDE_df, dtypes_dict = read_CDE()

    # Once we have the dependencies, add a selector for the app mode on the sidebar.
    st.sidebar.title("Upload")
    # st.write(dtypes_dict)
    # st.write(CDE_df)
    data_files = st.sidebar.file_uploader("\tMETADATA tables:", type=['xlsx', 'csv'],accept_multiple_files=True)


    if data_files is None or len(data_files)==0: 
        st.sidebar.error("Please load data first.")
        st.stop()
        tables_loaded = False
    elif len(data_files)>0:
        tables, dfs = load_data(data_files, dtypes_dict)
        tables_loaded = True
        report_dat = dict()
    else: # should be impossible
        st.error('Something went wrong with the file upload. Please try again.')
        st.stop()
        tables_loaded = False


    if tables_loaded:
        st.sidebar.success(f"N={len(tables)} Tables loaded successfully")
        st.sidebar.info(f'loaded Tables : {", ".join(map(str, tables))}')

        col1, col2 = st.columns(2)

        with col1:
            table_choice = st.selectbox( 
                "Choose the TABLE to validate 👇",
                tables,
                # index=None,
                # placeholder="Select TABLE..",
            )
        with col2:  
            st.write('You selected:', table_choice)

    # once tables are loaded make a dropdown to choose which one to validate




    report_dat = setup_report_data(report_dat, table_choice, dfs, CDE_df)


    report = ReportCollector()
    df,CDE = report_dat[table_choice]

    retval = validate_table(df, table_choice, CDE, report)

    if retval == 0:
        report.add_error(f"{table_choice} table has discrepancies!! 👎 Please try again.")


    report.add_divider()
    # # sex for qc
    # st.subheader('Create "biological_sex_for_qc"')
    # st.text('Count per sex group')
    # st.write(data.sex.value_counts())

    # sexes=data.sex.dropna().unique()
    # n_sexes = st.columns(len(sexes))
    # mapdic={}
    # for i, x in enumerate(n_sexes):
    #     with x:
    #         sex = sexes[i]
    #         mapdic[sex]=x.selectbox(f"[{sex}]: For QC, please pick a word below",sexes,key=i)
    #                             # ["Male", "Female","Intersex","Unnown"], key=i)
    # data['sex_qc'] = data.sex.replace(mapdic)

    # # cross-tabulation
    # st.text('=== sex_qc x sex ===')
    # xtab = data.pivot_table(index='sex_qc', columns='sex', margins=True,
    #                         values='subject_id', aggfunc='count', fill_value=0)
    # st.write(xtab)

    # sex_conf = st.checkbox('Confirm sex_qc?')
    # if sex_conf:
    #     st.info('Thank you')


    if retval == 1:
        st.markdown('<p class="medium-font"> You have <it>confirmed</it> your meta-data package meets all the ASAP CRN requirements. </p>', unsafe_allow_html=True )
        #from streamlit.scriptrunner import RerunException
        def cach_clean():
            time.sleep(1)
            st.runtime.legacy_caching.clear_cache()

        print(report)
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button('📥 Download your QC log', data=csv, file_name=LOG_NAME, mime='text/markdown')

    else:
        st.sidebar.error("Please validate data first.")


if __name__ == "__main__":

    # Provide template
    st.markdown('<p class="big-font">ASAP scRNAseq </p>', unsafe_allow_html=True)
    st.title('metadata data QC')
    st.markdown('<p class="medium-font"> This app is intended to make sure ASAP Cloud Platform contributions follow the ASAP CRN CDE convenetions</p>', unsafe_allow_html=True)
    st.markdown('[CDE v0.1](https://docs.google.com/spreadsheets/d/1xjxLftAyD0B8mPuOKUp5cKMKjkcsrp_zr9yuVULBLG8/edit?usp=sharing)')

    main()