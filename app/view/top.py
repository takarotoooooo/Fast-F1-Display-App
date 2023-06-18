import streamlit as st
import sys
from pathlib import Path
if str(Path().resolve()) not in sys.path:
    sys.path.append(str(Path().resolve()))
if '/app/fast-f1-display-app/app' not in sys.path:
    sys.path.append('/app/fast-f1-display-app/app')
import module.fastf1 as f1
import importlib
importlib.reload(f1)

st.set_page_config(layout='wide')


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
    st.title(f"{st.session_state.year} Season")

    st.sidebar.selectbox('Year', f1.available_years(), key='year')

    with st.spinner('Loading data...'):
        races = f1.season_races_df(year=st.session_state.year)
        races['LinkToRacePage'] = races['RoundNumber'].apply(make_url_to_race_page)
        races = races[['RoundNumber', 'EventName', 'RaceStartDate', 'LinkToRacePage']]

        drivers = f1.season_drivers_df(year=st.session_state.year)
        drivers['LinkToDriverPage'] = drivers['Abbreviation'].apply(make_url_to_driver_page)

        teams = f1.season_teams_df(year=st.session_state.year)

    st.header('Races')
    st.dataframe(
        races,
        column_config={'LinkToRacePage': st.column_config.LinkColumn('LinkToRacePage')},
        use_container_width=True,
        hide_index=True
    )

    st.header('Drivers')
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

    st.header('Teams')
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
