import streamlit as st
import fastf1
import pandas as pd

import sys
from pathlib import Path
if str(Path().resolve()) not in sys.path:
    sys.path.append(str(Path().resolve()))
import module.fastf1 as f1
import importlib
importlib.reload(f1)


def init_session():
    query_params = st.experimental_get_query_params()

    if 'year' not in st.session_state:
        if 'year' in query_params:
            st.session_state.year = int(query_params['year'][0])
        else:
            st.session_state.year = f1.available_years()[0]


def set_query_string():
    st.experimental_set_query_params(
        year=st.session_state.year
    )


def render():
    st.title(f"{st.session_state.year} Schedule")
    st.sidebar.selectbox('Year', f1.available_years(), key='year')

    with st.spinner('Loading data...'):
        races = f1.races(st.session_state.year)

    for race in races.to_dict('records'):
        st.markdown(
            f"""
            - Round : <a href='/race?year={ st.session_state.year }&round={ race['RoundNumber'] }'>{ race['RoundNumber'] }</a>
            - Name : {race['OfficialEventName']}
            - Country : {race['Country']}
            - Location : {race['Location']}
            - Date : {race['Date']}
            """,
            unsafe_allow_html=True)


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
