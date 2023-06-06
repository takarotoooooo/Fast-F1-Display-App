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
        round=st.session_state.round,
        driver=st.session_state.driver
    )


def race_name_change_hundler():
    race = races.query(f'OfficialEventName == "{st.session_state.race_name}"')
    st.session_state.round = int(race['RoundNumber'].values[0])


def render():
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)
    race = races.query(f"RoundNumber == {st.session_state.round}")
    driver = drivers.query(f'Abbreviation == "{st.session_state.driver}"')

    st.title(f"{driver['FullName'].values[0]} at {race['Country'].values[0]} in {st.session_state.year}")
    st.sidebar.selectbox('Year', f1.available_years(), key='year')
    st.sidebar.selectbox('Race', races['OfficialEventName'].values, key='race_name', on_change=race_name_change_hundler)
    st.sidebar.selectbox('Driver', drivers['Abbreviation'].values, key='driver')

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

    driver_laps = session.laps.pick_driver(st.session_state.driver).pick_quicklaps().reset_index()
    driver_laps["LapTime(s)"] = driver_laps["LapTime"].dt.total_seconds()

    st.subheader('Driver Laptimes')
    fig, ax = plt.subplots(figsize=(8, 8))
    sns.scatterplot(
        data=driver_laps,
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

    # The y-axis increases from bottom to top by default
    # Since we are plotting time, it makes sense to invert the axis
    ax.invert_yaxis()
    fig.suptitle(f"{st.session_state.driver} Laptimes in the {st.session_state.year} {session.event['EventName']}")

    # Turn on major grid lines
    ax.grid(color='w', which='major', axis='both')
    sns.despine(left=True, bottom=True)

    plt.tight_layout()
    st.pyplot(fig)

    st.subheader('Tyre strategies during a race')
    fig, ax = plt.subplots(figsize=(10, 2))
    driver_stints = driver_laps[["Driver", "Stint", "Compound", "LapNumber"]]
    driver_stints = driver_stints.groupby(["Driver", "Stint", "Compound"])
    driver_stints = driver_stints.count().reset_index()
    driver_stints = driver_stints.rename(columns={"LapNumber": "StintLength"})
    previous_stint_end = 0
    for idx, row in driver_stints.iterrows():
        ax.barh(
            y=driver['Abbreviation'].values[0],
            width=row["StintLength"],
            left=previous_stint_end,
            color=fastf1.plotting.COMPOUND_COLORS.get(row["Compound"], '#ffffff'),
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

    st.subheader('Gear shifts on track')
    fig, ax = plt.subplots(figsize=(8.0, 4.9))
    fistest_lap = driver_laps.pick_fastest()
    tel = fistest_lap.get_telemetry()
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
        f"{fistest_lap['Driver']} - {session.event['EventName']} {session.event.year}"
    )
    cbar = fig.colorbar(mappable=lc_comp, label="Gear", boundaries=np.arange(1, 10))
    cbar.set_ticks(np.arange(1.5, 9.5))
    cbar.set_ticklabels(np.arange(1, 9))
    st.pyplot(fig)

    driver_laps = session.laps.pick_driver(st.session_state.driver).reset_index()
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
    columns = ['LapNumber', 'Stint', 'TyreLife']
    driver_laps[columns] = driver_laps[columns].astype('int')
    driver_laps_pd = pd.DataFrame(driver_laps)
    st.table(driver_laps_pd[['Driver', 'LapNumber', 'Stint', 'TyreLife', 'Compound', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
