import streamlit as st
import pandas as pd
import sys
from pathlib import Path
if str(Path().resolve()) not in sys.path:
    sys.path.append(str(Path().resolve()))
import module.fastf1 as f1
import importlib
importlib.reload(f1)

st.title('FastF1 display APP')

year = 2023

st.dataframe(
    f1.teams(year, use_cache=False),
    column_config={
        'Abbreviation': st.column_config.ListColumn('Drivers'),
        'RaceCount': st.column_config.NumberColumn('RaceCount'),
        'TotalPoint': st.column_config.NumberColumn('TotalPoint')
    },
    use_container_width=True
)

st.dataframe(
    f1.drivers(year, use_cache=False),
    column_config={
        'HeadshotUrl': st.column_config.ImageColumn('Headshot'),
        'Teams': st.column_config.ListColumn('Teams'),
        'RaceCount': st.column_config.NumberColumn('RaceCount'),
        'TotalPoint': st.column_config.NumberColumn('TotalPoint')
    },
    use_container_width=True
)

st.dataframe(
    f1.team_drivers(year, use_cache=False),
    column_config={
        'RaceCount': st.column_config.NumberColumn('RaceCount'),
        'TotalPoint': st.column_config.NumberColumn('TotalPoint')
    },
    use_container_width=True
)
