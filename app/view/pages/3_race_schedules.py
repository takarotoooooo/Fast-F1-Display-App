import streamlit as st
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


def make_url_to_race_page(value):
    return f'/race?year={st.session_state.year}&round={value}'


def make_url_to_driver_page(value):
    return f'/driver?year={st.session_state.year}&driver={value}'


def render():
    st.title(f"In {st.session_state.year}")

    st.sidebar.selectbox('Year', f1.available_years(), key='year')

    with st.spinner('Loading data...'):
        races = f1.races(st.session_state.year)
        drivers = f1.drivers(st.session_state.year)

    races['Link'] = races['RoundNumber'].apply(make_url_to_race_page)
    st.subheader('Race schedules')
    st.dataframe(
        races,
        column_config={'Link': st.column_config.LinkColumn('Link')}
    )

    drivers['Link'] = drivers['Abbreviation'].apply(make_url_to_driver_page)
    st.subheader('Driver lineup')
    st.dataframe(
        drivers,
        column_config={'Link': st.column_config.LinkColumn('Link')}
    )


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
