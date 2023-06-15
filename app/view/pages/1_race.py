import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import seaborn as sns

import sys
from pathlib import Path
if str(Path().resolve()) not in sys.path:
    sys.path.append(str(Path().resolve()))
import module.fastf1 as f1
import helper.gear_shifts_on_track
import helper.tyre_strategies_during_race
import importlib
importlib.reload(f1)
importlib.reload(helper.tyre_strategies_during_race)


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


def set_query_string():
    st.experimental_set_query_params(
        year=st.session_state.year,
        round=st.session_state.round
    )


def race_name_change_hundler():
    race = races.query(f'EventName == "{st.session_state.race_name}"').iloc[0]
    st.session_state.round = int(race['RoundNumber'])


def make_url_to_driver_race_page(value):
    return f'/driver_race?year={st.session_state.year}&round={st.session_state.round}&driver={value}'


def render():
    race = races.query(f"RoundNumber == {st.session_state.round}").iloc[0]
    st.set_page_config(
        page_title=f'{st.session_state.year} | {race["EventName"]}',
        layout='wide'
    )

    st.title(race['OfficialEventName'])
    st.sidebar.selectbox('Year', f1.available_years(), key='year')
    st.sidebar.selectbox('Race', races['EventName'].values, key='race_name', on_change=race_name_change_hundler)

    with st.spinner('Loading data...'):
        session = fastf1.get_session(
            st.session_state.year,
            st.session_state.round,
            'R')
        session.load()

        season_results = f1.season_results_df(st.session_state.year)
        race_results = season_results.query(f'RoundNumber == {st.session_state.round}')
        race_results[['GridPosition', 'Position', 'Points']] = race_results[['GridPosition', 'Position', 'Points']].astype('int')
        race_results['LinkToDriverRacePage'] = race_results['Abbreviation'].apply(make_url_to_driver_race_page)

        laps = session.laps
        fastest_lap = laps.pick_fastest()

    st.subheader('Race information')
    st.dataframe(race, use_container_width=True)

    st.subheader('Race results')
    st.dataframe(
        race_results[['DriverNumber', 'FullName', 'TeamName', 'GridPosition', 'Position', 'Points', 'LinkToDriverRacePage']],
        column_config={'LinkToDriverRacePage': st.column_config.LinkColumn('LinkToDriverRacePage')},
        use_container_width=True,
        hide_index=True)

    visualization_tab, row_data_tab = st.tabs(['Visualization', 'RowData'])
    with visualization_tab:
        st.subheader('Position changes during a race')
        fig, ax = plt.subplots(figsize=(8.0, 4.9))
        for drv in session.drivers:
            drv_laps = laps.pick_driver(drv)

            abb = drv_laps['Driver'].iloc[0]
            try:
                color = fastf1.plotting.driver_color(abb)
            except KeyError:
                color = '#000000'

            ax.plot(drv_laps['LapNumber'], drv_laps['Position'],
                    label=abb, color=color)
        ax.set_ylim([20.5, 0.5])
        ax.set_yticks([1, 5, 10, 15, 20])
        ax.set_xlabel('Lap')
        ax.set_ylabel('Position')
        ax.legend(bbox_to_anchor=(1.0, 1.02))
        plt.tight_layout()
        st.pyplot(fig)

        st.subheader('Fastest Lap')
        fastest_lap["LapTime(s)"] = fastest_lap["LapTime"].total_seconds()
        fastest_lap['LapNumber'] = fastest_lap['LapNumber'].astype('int')
        st.dataframe(fastest_lap[['Driver', 'LapTime(s)', 'LapNumber', 'Compound']], use_container_width=True)

        # Gear shifts
        st.subheader('Gear shifts on track')
        helper.gear_shifts_on_track.render(target_lap=fastest_lap)

        # Tyre strategies
        st.subheader('Tyre strategies during a race')
        drivers = [session.get_driver(driver)["Abbreviation"] for driver in session.drivers]
        helper.tyre_strategies_during_race.render(laps=laps, drivers=drivers)

        st.subheader('Driver Laptimes Distribution Visualization')
        fig, ax = plt.subplots(figsize=(10, 5))
        driver_laps = session.laps.pick_drivers(session.drivers).pick_quicklaps().reset_index()
        drivers = [session.get_driver(driver)["Abbreviation"] for driver in session.drivers]
        driver_laps["LapTime(s)"] = driver_laps["LapTime"].dt.total_seconds()
        driver_colors = {}
        for abb in drivers:
            try:
                color = fastf1.plotting.driver_color(abb)
            except KeyError:
                color = '#000000'
            driver_colors[abb] = color

        sns.violinplot(
            data=driver_laps,
            x="Driver",
            y="LapTime(s)",
            inner=None,
            scale="area",
            order=drivers,
            palette=driver_colors)
        # st.write(driver_laps)
        # sns.swarmplot(
        #     data=driver_laps,
        #     x="Driver",
        #     y="LapTime(s)",
        #     order=drivers,
        #     hue="Compound",
        #     palette=fastf1.plotting.COMPOUND_COLORS,
        #     hue_order=["SOFT", "MEDIUM", "HARD"],
        #     linewidth=0,
        #     size=5)
        ax.set_xlabel("Driver")
        ax.set_ylabel("Lap Time (s)")
        fig.suptitle(f"{session.event['EventName']} {session.event.year}")
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
        st.pyplot(fig)

    with row_data_tab:
        st.subheader('Fastest lap')
        st.dataframe(fastest_lap, use_container_width=True)

        st.subheader('Race results')
        st.dataframe(race_results, use_container_width=True, hide_index=True)

        st.subheader('Driver laps')
        st.dataframe(laps, use_container_width=True, hide_index=True)

        # st.subheader('Drivers')
        # st.write(session.drivers)

        # st.subheader('Laps')
        # st.write(session.laps)

        # st.subheader('Weather')
        # weather_data_telemetry = session.weather_data
        # st.code(weather_data_telemetry)

        # st.subheader('Car')
        # for car_number, d in session.car_data.items():
        #     st.text(car_number)
        #     st.write(d)

        # st.subheader('Session status')
        # st.code(session.session_status)

        # st.subheader('Track')
        # st.code(session.track_status)

        # st.subheader('Race Control')
        # st.write(session.race_control_messages)


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
