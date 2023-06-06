import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import cm
import seaborn as sns
import numpy as np
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


def set_query_string():
    st.experimental_set_query_params(
        year=st.session_state.year,
        round=st.session_state.round
    )


def race_name_change_hundler():
    race = races.query(f'OfficialEventName == "{st.session_state.race_name}"')
    st.session_state.round = int(race['RoundNumber'].values[0])


def render():
    race = races.query(f"RoundNumber == {st.session_state.round}")
    st.title(race['OfficialEventName'].values[0])
    st.sidebar.selectbox('Year', f1.available_years(), key='year')
    st.sidebar.selectbox('Race', races['OfficialEventName'].values, key='race_name', on_change=race_name_change_hundler)

    with st.spinner('Loading data...'):
        session = fastf1.get_session(
            st.session_state.year,
            st.session_state.round,
            'R')
        session.load()
        event = session.event

    st.subheader('Race information')
    st.table(
        pd.Series(
            {
                'RoundNumber': event['RoundNumber'],
                'Country': event['Country'],
                'Location': event['Location'],
                'Laps': session.total_laps
            }
        ))

    st.subheader('Race results')
    race_result_pd = pd.DataFrame(
        session.results[['DriverNumber', 'FullName', 'TeamName', 'GridPosition', 'Position', 'Points']]
    ).sort_values(['Position'])
    race_result_pd[['GridPosition', 'Position', 'Points']] = \
        race_result_pd[['GridPosition', 'Position', 'Points']].astype('int')
    st.table(race_result_pd)

    st.subheader('Position changes during a race')
    fig, ax = plt.subplots(figsize=(8.0, 4.9))
    for drv in session.drivers:
        drv_laps = session.laps.pick_driver(drv)

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
    lap = session.laps.pick_fastest()
    fastest_lap_pd = pd.Series(lap)
    fastest_lap_pd["LapTime(s)"] = fastest_lap_pd["LapTime"].total_seconds()
    fastest_lap_pd['LapNumber'] = fastest_lap_pd['LapNumber'].astype('int')
    st.table(fastest_lap_pd[['Driver', 'LapTime(s)', 'LapNumber', 'Compound']])

    # Gear shifts
    st.subheader('Gear shifts on track')
    fig, ax = plt.subplots(figsize=(8.0, 4.9))
    tel = lap.get_telemetry()
    x = np.array(tel['X'].values)
    y = np.array(tel['Y'].values)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    gear = tel['nGear'].to_numpy().astype(float)
    cmap = cm.get_cmap('Paired')
    lc_comp = LineCollection(segments, norm=plt.Normalize(1, cmap.N + 1), cmap=cmap)
    lc_comp.set_array(gear)
    lc_comp.set_linewidth(4)

    fig.gca().add_collection(lc_comp)
    ax.axis('equal')
    ax.tick_params(labelleft=False, left=False, labelbottom=False, bottom=False)

    fig.suptitle(
        f"Fastest Lap Gear Shift Visualization\n"
        f"{lap['Driver']} - {session.event['EventName']} {session.event.year}"
    )
    cbar = fig.colorbar(mappable=lc_comp, label="Gear", boundaries=np.arange(1, 10))
    cbar.set_ticks(np.arange(1.5, 9.5))
    cbar.set_ticklabels(np.arange(1, 9))
    st.pyplot(fig)

    # Tyre strategies
    st.subheader('Tyre strategies during a race')
    fig, ax = plt.subplots(figsize=(5, 10))
    laps = session.laps
    drivers = [session.get_driver(driver)["Abbreviation"] for driver in session.drivers]
    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
    stints = stints.groupby(["Driver", "Stint", "Compound"])
    stints = stints.count().reset_index()
    stints = stints.rename(columns={"LapNumber": "StintLength"})
    for driver in drivers:
        driver_stints = stints.loc[stints["Driver"] == driver]

        previous_stint_end = 0
        for idx, row in driver_stints.iterrows():
            # each row contains the compound name and stint length
            # we can use these information to draw horizontal bars
            plt.barh(
                y=driver,
                width=row["StintLength"],
                left=previous_stint_end,
                color=fastf1.plotting.COMPOUND_COLORS[row["Compound"]],
                edgecolor="black",
                fill=True
            )

            previous_stint_end += row["StintLength"]
    fig.suptitle(f"{session.event['EventName']} {session.event.year}")
    ax.set_xlabel("Lap Number")
    ax.grid(False)
    # invert the y-axis so drivers that finish higher are closer to the top
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader('Qualifying results overview')

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
