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

    if 'round' not in st.session_state:
        if 'round' in query_params:
            st.session_state.round = int(query_params['round'][0])
        else:
            st.session_state.round = 1

    if 'driver' not in st.session_state:
        if 'driver' in query_params:
            st.session_state.driver = query_params['driver'][0]
        else:
            st.session_state.driver = 'VER'


def set_query_string():
    st.experimental_set_query_params(
        year=st.session_state.year,
        round=st.session_state.round,
        driver=st.session_state.driver
    )


def render():
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)

    with st.spinner('Loading data...'):
        event_schedule = fastf1.get_event_schedule(st.session_state.year)
        event_schedule_pd = pd.DataFrame(event_schedule)

        available_round_numbers = [
            int(record['RoundNumber'])
            for record in event_schedule_pd.to_dict('records')]

        session = fastf1.get_session(
            st.session_state.year,
            st.session_state.round,
            'R')
        session.load()

        driver_names = f1.drivers(st.session_state.year)['Abbreviation'].values

    st.title('Driver')
    st.sidebar.selectbox('Year', f1.available_years(), key='year')
    st.sidebar.selectbox('Round', available_round_numbers, key='round')
    st.sidebar.selectbox('Driver', driver_names, key='driver')

    driver_laps = session.laps.pick_driver(st.session_state.driver).pick_quicklaps().reset_index()
    driver_laps["LapTime(s)"] = driver_laps["LapTime"].dt.total_seconds()

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

    st.write(driver_laps)

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


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
