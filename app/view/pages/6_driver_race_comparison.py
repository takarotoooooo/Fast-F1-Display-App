import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
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

    global races
    races = f1.races(st.session_state.year)
    if 'race_name' not in st.session_state:
        if 'round' in query_params:
            race = races.query(f"RoundNumber == {query_params['round'][0]}")
            st.session_state.race_name = race['OfficialEventName'].values[0]
        else:
            st.session_state.race_name = races['OfficialEventName'].values[0]

    if 'round' not in st.session_state:
        if 'round' in query_params:
            st.session_state.round = int(query_params['round'][0])
        else:
            race = races.query(f'OfficialEventName == "{st.session_state.race_name}"')
            st.session_state.round = int(race['RoundNumber'].values[0])

    global drivers
    drivers = f1.drivers(st.session_state.year)
    if 'driver' not in st.session_state:
        if 'driver' in query_params:
            st.session_state.driver = query_params['driver'][0]
        else:
            st.session_state.driver = drivers['Abbreviation'].values[0]

    if 'target_driver' not in st.session_state:
        if 'target_driver' in query_params:
            st.session_state.target_driver = query_params['target_driver'][0]
        else:
            st.session_state.target_driver = drivers['Abbreviation'].values[1]


def set_query_string():
    st.experimental_set_query_params(
        year=st.session_state.year,
        round=st.session_state.round,
        driver=st.session_state.driver,
        target_driver=st.session_state.target_driver
    )


def race_name_change_hundler():
    race = races.query(f'OfficialEventName == "{st.session_state.race_name}"')
    st.session_state.round = int(race['RoundNumber'].values[0])


def render():
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)
    # race = races.query(f"RoundNumber == {st.session_state.round}")
    driver = drivers.query(f'Abbreviation == "{st.session_state.driver}"')
    target_driver = drivers.query(f'Abbreviation == "{st.session_state.target_driver}"')

    st.title(f"Comparison {driver['Abbreviation'].values[0]} and {target_driver['Abbreviation'].values[0]}")
    st.sidebar.selectbox('Year', f1.available_years(), key='year')
    st.sidebar.selectbox('Race', races['OfficialEventName'].values, key='race_name', on_change=race_name_change_hundler)
    st.sidebar.selectbox('Driver', drivers['Abbreviation'].values, key='driver')
    st.sidebar.selectbox('TargetDriver', drivers['Abbreviation'].values, key='target_driver')

    try:
        with st.spinner('Loading data...'):
            session = fastf1.get_session(
                st.session_state.year,
                st.session_state.round,
                'R')
            session.load()
    except fastf1.core.DataNotLoadedError:
        st.text('レース情報を取得できませんでした')
        return

    driver_laps = session.laps.pick_driver(st.session_state.driver).reset_index()
    target_driver_laps = session.laps.pick_driver(st.session_state.target_driver).reset_index()
    columns = [
        'Time',
        'LapTime',
        'PitOutTime',
        'PitInTime',
        'Sector1Time',
        'Sector2Time',
        'Sector3Time',
        'Sector1SessionTime',
        'Sector2SessionTime',
        'Sector3SessionTime',
        'LapStartTime'
    ]
    for c in columns:
        driver_laps[c] = driver_laps[c].dt.total_seconds()
        target_driver_laps[c] = target_driver_laps[c].dt.total_seconds()
    columns = ['LapNumber', 'Stint', 'TyreLife', 'Position']
    driver_laps[columns] = driver_laps[columns].astype('int')
    target_driver_laps[columns] = target_driver_laps[columns].astype('int')

    driver_laps_pd = pd.DataFrame(driver_laps)
    target_driver_laps_pd = pd.DataFrame(target_driver_laps)

    comp_pd = pd.merge(driver_laps_pd, target_driver_laps_pd, on=['LapNumber'], how='left')
    comp_pd['TimeGap'] = comp_pd['Time_x'] - comp_pd['Time_y']
    comp_pd['LapTimeGap'] = comp_pd['LapTime_x'] - comp_pd['LapTime_y']
    comp_pd = comp_pd.rename(columns={
        'Position_x': 'Position',
        'Position_y': 'TargetPosition',
        'LapTime_x': 'LapTime',
        'LapTime_y': 'TargetLapTime',
    })
    columns = [
        'LapNumber',
        'TimeGap',
        'LapTimeGap',
        'Position',
        'TargetPosition',
        'LapTime',
        'TargetLapTime']
    st.table(comp_pd[columns])

    st.subheader('Time gap each lap end')
    fig, ax = plt.subplots()
    ax.bar(
        comp_pd['LapNumber'],
        comp_pd['TimeGap'],
        color='#FFFFFF',
        label=target_driver['Abbreviation'].values[0])

    ax.set_xlabel('TimeGap(s)')
    ax.set_ylabel('LapNumber')
    y_limit = max([abs(comp_pd['TimeGap'].min()), abs(comp_pd['TimeGap'].max())])
    y_limit = y_limit * 1.2
    ax.set_ylim(-1 * y_limit, y_limit)

    ax.legend()
    fig.suptitle(
        f"Time gap each lap end {driver['Abbreviation'].values[0]} and {target_driver['Abbreviation'].values[0]}")
    st.pyplot(fig)

    columns = ['Driver', 'Time', 'LapNumber', 'Position', 'Stint', 'TyreLife', 'Compound', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']
    st.subheader(driver['Abbreviation'].values[0])
    st.table(driver_laps_pd[columns])

    st.subheader(target_driver['Abbreviation'].values[0])
    st.table(target_driver_laps_pd[columns])

    st.table(target_driver_laps_pd)


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
