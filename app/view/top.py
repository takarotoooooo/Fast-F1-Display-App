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
    st.set_page_config(
        page_title=f'{st.session_state.year} | Top',
        layout='wide'
    )

    st.title(f"{st.session_state.year} | Top")

    st.sidebar.selectbox('Year', f1.available_years(), key='year')

    with st.spinner('Loading data...'):
        races = f1.races(st.session_state.year)
        drivers = f1.drivers(st.session_state.year)
        teams = f1.teams(st.session_state.year)

    races['LinkToRacePage'] = races['RoundNumber'].apply(make_url_to_race_page)
    st.header('Race schedules')
    st.dataframe(
        races[[
            'RoundNumber',
            'OfficialEventName',
            'RaceDate',
            'LinkToRacePage'
        ]],
        column_config={'LinkToRacePage': st.column_config.LinkColumn('LinkToRacePage')},
        use_container_width=True,
        hide_index=True
    )

    drivers['LinkToDriverPage'] = drivers['Abbreviation'].apply(make_url_to_driver_page)
    st.header('Driver lineup')
    st.dataframe(
        drivers,
        column_config={
            'HeadshotUrl': st.column_config.ImageColumn('Headshot'),
            'Teams': st.column_config.ListColumn('Teams'),
            'RaceCount': st.column_config.NumberColumn('RaceCount'),
            'TotalPoint': st.column_config.NumberColumn('TotalPoint'),
            'LinkToDriverPage': st.column_config.LinkColumn('Link')
        },
        use_container_width=True,
        hide_index=True
    )

    st.header('Team lineup')
    st.dataframe(
        teams,
        column_config={
            'Drivers': st.column_config.ListColumn('Drivers'),
            'RaceCount': st.column_config.NumberColumn('RaceCount'),
            'TotalPoint': st.column_config.NumberColumn('TotalPoint')
        },
        use_container_width=True,
        hide_index=True
    )


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()