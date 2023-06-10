import streamlit as st
import fastf1
import fastf1.plotting
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

    global drivers
    drivers = f1.drivers(st.session_state.year)
    if 'driver' not in st.session_state:
        if 'driver' in query_params:
            st.session_state.driver = query_params['driver'][0]
        else:
            st.session_state.driver = drivers['Abbreviation'].values[0]


def set_query_string():
    st.experimental_set_query_params(
        year=st.session_state.year,
        driver=st.session_state.driver
    )


def make_url_to_driver_race_page(value):
    return f'/driver_race?year={st.session_state.year}&driver={st.session_state.driver}&round={value}'


def render():
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)
    driver = drivers.query(f'Abbreviation == "{st.session_state.driver}"')

    st.title(f"{driver['FullName'].values[0]} in {st.session_state.year}")
    st.sidebar.selectbox('Year', f1.available_years(), key='year')
    st.sidebar.selectbox('Driver', drivers['Abbreviation'].values, key='driver')

    results = f1.results(st.session_state.year)
    driver_results = results[results['Abbreviation'] == st.session_state.driver]
    for c in ['Q1', 'Q2', 'Q3', 'Time']:
        driver_results[c] = driver_results[c].dt.total_seconds()
    columns = ['GridPosition', 'Position', 'Points']
    driver_results[columns] = driver_results[columns].astype('int')
    driver_results['Link'] = driver_results['RoundNumber'].apply(make_url_to_driver_race_page)
    st.dataframe(
        driver_results[['RoundNumber', 'EventName', 'TeamName', 'GridPosition', 'Position', 'Points', 'Link']],
        column_config={'Link': st.column_config.LinkColumn('Link')}
    )


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
