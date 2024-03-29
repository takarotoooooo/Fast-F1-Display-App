import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import seaborn as sns

import sys
from pathlib import Path
import os
base_dir = os.path.dirname(Path(os.path.dirname(Path(os.path.dirname(Path(__file__).resolve())))))
if base_dir not in sys.path:
    sys.path.append(base_dir)
import module.fastf1 as f1  # noqa: E402
import helper.gear_shifts_on_track  # noqa: E402
import helper.tyre_strategies_during_race  # noqa: E402
import helper.speed_visualization_on_track_map  # noqa: E402
import helper.throttle_pedal_pressure_on_track  # noqa: E402
import importlib  # noqa: E402
importlib.reload(f1)
importlib.reload(helper.tyre_strategies_during_race)
importlib.reload(helper.speed_visualization_on_track_map)
importlib.reload(helper.throttle_pedal_pressure_on_track)

st.set_page_config(layout='wide')


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


def set_query_string():
    st.experimental_set_query_params(
        year=st.session_state.year,
        round=st.session_state.round,
        driver=st.session_state.driver
    )


def race_name_change_hundler():
    race = races.query(f'EventName == "{st.session_state.race_name}"').iloc[0]
    st.session_state.round = int(race['RoundNumber'])


def render():
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)
    race = races.query(f"RoundNumber == {st.session_state.round}").iloc[0]
    driver = drivers.query(f'Abbreviation == "{st.session_state.driver}"').iloc[0]

    st.title(f"{st.session_state.year} | {race['EventName']} | {driver['FullName']}")
    st.sidebar.selectbox('Year', f1.available_years(), key='year')
    st.sidebar.selectbox('Race', races['EventName'].values, key='race_name', on_change=race_name_change_hundler)
    st.sidebar.selectbox('Driver', drivers['Abbreviation'].values, key='driver')

    try:
        with st.spinner('Loading data...'):
            session = fastf1.get_session(
                st.session_state.year,
                st.session_state.round,
                'R')
            session.load()

            laps = session.laps
            driver_laps = laps.pick_driver(st.session_state.driver).reset_index()
            driver_quicklaps = laps.pick_driver(st.session_state.driver).pick_quicklaps().reset_index()
            driver_laps["LapTime(s)"] = driver_laps["LapTime"].dt.total_seconds()
            driver_quicklaps["LapTime(s)"] = driver_quicklaps["LapTime"].dt.total_seconds()
            # columns = [
            #     'Time',
            #     'LapTime',
            #     'PitOutTime',
            #     'PitInTime',
            #     'Sector1Time',
            #     'Sector2Time',
            #     'Sector3Time',
            #     'Sector1SessionTime',
            #     'Sector2SessionTime',
            #     'Sector3SessionTime',
            #     'LapStartTime'
            # ]
            # for c in columns:
            #     driver_laps[c] = driver_laps[c].dt.total_seconds()
            #     driver_quicklaps[c] = driver_quicklaps[c].dt.total_seconds()

            # columns = ['LapNumber', 'Stint', 'TyreLife']
            # driver_laps[columns] = driver_laps[columns].astype('int')
            # driver_quicklaps[columns] = driver_quicklaps[columns].astype('int')

            # st.header('Laps')
            # st.dataframe(
            #     driver_laps[['LapNumber', 'Stint', 'TyreLife', 'Compound', 'LapTime(s)', 'Sector1Time', 'Sector2Time', 'Sector3Time']],
            #     use_container_width=True)

            # st.dataframe(
            #     driver_quicklaps[['LapNumber', 'Stint', 'TyreLife', 'Compound', 'LapTime(s)', 'Sector1Time', 'Sector2Time', 'Sector3Time']],
            #     use_container_width=True)

            fastest_lap = driver_quicklaps.pick_fastest()
            fastest_lap_tel = fastest_lap.get_telemetry()
            columns = ['SessionTime', 'Time']
            for c in columns:
                fastest_lap_tel[c] = fastest_lap_tel[c].dt.total_seconds()
    except fastf1.core.DataNotLoadedError:
        st.text('レース情報を取得できませんでした')
        return

    visualization_tab, row_data_tab = st.tabs(['Visualization', 'RowData'])
    with visualization_tab:
        st.subheader('Driver Laptimes')
        fig, ax = plt.subplots(figsize=(8, 8))
        sns.scatterplot(
            data=driver_quicklaps,
            x="LapNumber",
            y="LapTime(s)",
            ax=ax,
            hue="Compound",
            palette=fastf1.plotting.COMPOUND_COLORS,
            s=80,
            linewidth=0,
            legend='auto')
        ax.set_xlabel("Lap Number")
        ax.set_ylabel("Lap Time")
        ax.invert_yaxis()
        ax.grid(color='w', which='major', axis='both')
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
        st.pyplot(fig)

        st.subheader('Tyre strategies during a race')
        helper.tyre_strategies_during_race.render(laps=driver_laps, drivers=[st.session_state.driver])

        st.subheader('Gear shifts on track')
        helper.gear_shifts_on_track.render(target_lap=fastest_lap)

        st.subheader('Speed on track')
        helper.speed_visualization_on_track_map.render(target_lap=fastest_lap)

        st.subheader('Throttle pedal pressure on track')
        helper.throttle_pedal_pressure_on_track.render(target_lap=fastest_lap)

    with row_data_tab:
        st.header('Laptime')
        st.dataframe(driver_laps, use_container_width=True, hide_index=True)

        st.header('FastestLap Telemetry')
        st.dataframe(fastest_lap_tel, use_container_width=True, hide_index=True)


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
