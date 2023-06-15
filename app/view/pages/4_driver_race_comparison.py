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
import helper.speed_visualization_on_track_map
import importlib
importlib.reload(f1)
importlib.reload(helper.speed_visualization_on_track_map)


def init_session():
    query_params = st.experimental_get_query_params()

    if 'year' not in st.session_state:
        if 'year' in query_params:
            st.session_state.year = int(query_params['year'][0])
        else:
            st.session_state.year = f1.available_years()[0]

    global races
    races = f1.season_races_df(st.session_state.year)
    if 'race_name' not in st.session_state:
        if 'round' in query_params:
            race = races.query(f"RoundNumber == {query_params['round'][0]}").iloc[0]
            st.session_state.race_name = race['EventName']
        else:
            st.session_state.race_name = races['EventName'].values[0]

    if 'round' not in st.session_state:
        if 'round' in query_params:
            st.session_state.round = int(query_params['round'][0])
        else:
            race = races.query(f'EventName == "{st.session_state.race_name}"').iloc[0]
            st.session_state.round = int(race['RoundNumber'])

    global drivers
    drivers = f1.season_drivers_df(st.session_state.year)
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
    race = races.query(f'EventName == "{st.session_state.race_name}"').iloc[0]
    st.session_state.round = int(race['RoundNumber'])


def render():
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)
    race = races.query(f"RoundNumber == {st.session_state.round}").iloc[0]
    driver = drivers.query(f'Abbreviation == "{st.session_state.driver}"').iloc[0]
    target_driver = drivers.query(f'Abbreviation == "{st.session_state.target_driver}"').iloc[0]
    target_driver_result = f1.season_results_df(st.session_state.year).query(f'Abbreviation == "{st.session_state.target_driver}"').iloc[0]
    st.set_page_config(
        page_title=f'{st.session_state.year} | {race["EventName"]} | {driver["Abbreviation"]} - {target_driver["Abbreviation"]}',
        layout='wide'
    )

    st.title(f'{st.session_state.year} | {race["EventName"]} | {driver["Abbreviation"]} - {target_driver["Abbreviation"]}')
    st.sidebar.selectbox('Year', f1.available_years(), key='year')
    st.sidebar.selectbox('Race', races['EventName'].values, key='race_name', on_change=race_name_change_hundler)
    st.sidebar.selectbox('Driver', drivers['Abbreviation'].values, key='driver')
    st.sidebar.selectbox('TargetDriver', drivers['Abbreviation'].values, key='target_driver')

    try:
        with st.spinner('Loading data...'):
            session = fastf1.get_session(
                st.session_state.year,
                st.session_state.round,
                'R')
            session.load()

            driver_laps = pd.DataFrame(session.laps.pick_driver(st.session_state.driver).reset_index())
            target_driver_laps = pd.DataFrame(session.laps.pick_driver(st.session_state.target_driver).reset_index())
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

            drive_fastest_lap = session.laps.pick_driver(st.session_state.driver).pick_quicklaps().reset_index().pick_fastest()
            drive_fastest_lap_tel = drive_fastest_lap.get_telemetry()
            target_drive_fastest_lap = session.laps.pick_driver(st.session_state.target_driver).pick_quicklaps().reset_index().pick_fastest()
            target_drive_fastest_lap_tel = target_drive_fastest_lap.get_telemetry()
            for c in ['SessionTime', 'Time']:
                drive_fastest_lap_tel[c] = drive_fastest_lap_tel[c].dt.total_seconds()
                target_drive_fastest_lap_tel[c] = target_drive_fastest_lap_tel[c].dt.total_seconds()

    except fastf1.core.DataNotLoadedError:
        st.text('レース情報を取得できませんでした')
        return

    laps_comparison = pd.merge(driver_laps, target_driver_laps, on=['LapNumber'], how='left')
    laps_comparison['TimeGap'] = laps_comparison['Time_x'] - laps_comparison['Time_y']
    laps_comparison['LapTimeGap'] = laps_comparison['LapTime_x'] - laps_comparison['LapTime_y']
    laps_comparison = laps_comparison.rename(columns={
        'Position_x': 'Position',
        'Position_y': 'TargetPosition',
        'LapTime_x': 'LapTime',
        'LapTime_y': 'TargetLapTime',
    })

    st.header('Time gap each lap end')
    fig, ax = plt.subplots()
    ax.bar(
        laps_comparison['LapNumber'],
        laps_comparison['TimeGap'],
        color=f'#{target_driver_result["TeamColor"]}',
        label=target_driver['Abbreviation'])

    ax.set_xlabel('LapNumber')
    ax.set_ylabel('TimeGap(s)')
    y_limit = max([abs(laps_comparison['TimeGap'].min()), abs(laps_comparison['TimeGap'].max())])
    y_limit = y_limit * 1.2
    ax.set_ylim(-1 * y_limit, y_limit)

    ax.legend()
    st.pyplot(fig)

    st.header('Comparison data')
    lap_columns = [
        'Driver',
        'Time',
        'LapNumber',
        'Position',
        'Stint',
        'TyreLife',
        'Compound',
        'LapTime',
        'Sector1Time',
        'Sector2Time',
        'Sector3Time']
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(st.session_state.driver)
        st.subheader('Laps')
        st.dataframe(driver_laps[lap_columns], use_container_width=True, hide_index=True)
        st.subheader('Fastest lap')
        st.dataframe(drive_fastest_lap, use_container_width=True, hide_index=True)
        st.subheader('Fastest lap metrics')
        st.dataframe(drive_fastest_lap_tel, use_container_width=True, hide_index=True)
        helper.speed_visualization_on_track_map.render(target_lap=drive_fastest_lap)

    with col2:
        st.subheader(st.session_state.target_driver)
        st.subheader('Laps')
        st.dataframe(target_driver_laps[lap_columns], use_container_width=True, hide_index=True)
        st.subheader('Fastest lap')
        st.dataframe(target_drive_fastest_lap, use_container_width=True, hide_index=True)
        st.subheader('Fastest lap metrics')
        st.dataframe(target_drive_fastest_lap_tel, use_container_width=True, hide_index=True)
        helper.speed_visualization_on_track_map.render(target_lap=target_drive_fastest_lap)

    st.header('Comparison each lap')
    st.dataframe(
        laps_comparison[[
            'LapNumber',
            'TimeGap',
            'LapTimeGap',
            'Position',
            'TargetPosition',
            'LapTime',
            'TargetLapTime']],
        use_container_width=True)


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
