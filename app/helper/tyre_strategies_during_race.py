import streamlit as st
import matplotlib.pyplot as plt
import fastf1.plotting


def render(laps, drivers):
    fig, ax = plt.subplots(figsize=(10, len(drivers)))
    stints = laps[['Driver', 'Stint', 'Compound', 'LapNumber']] \
        .groupby(['Driver', 'Stint', 'Compound']) \
        .count() \
        .reset_index() \
        .rename(columns={'LapNumber': 'StintLength'})

    for driver in drivers:
        driver_stints = stints.loc[stints['Driver'] == driver]

        previous_stint_end = 0
        for idx, row in driver_stints.iterrows():
            plt.barh(
                y=driver,
                width=row['StintLength'],
                left=previous_stint_end,
                color=fastf1.plotting.COMPOUND_COLORS[row['Compound']],
                edgecolor='black',
                fill=True
            )

            previous_stint_end += row['StintLength']
    ax.set_xlabel('Lap Number')
    ax.grid(False)
    # invert the y-axis so drivers that finish higher are closer to the top
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
