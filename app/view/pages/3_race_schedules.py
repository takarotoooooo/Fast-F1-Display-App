import streamlit as st
import fastf1
import pandas as pd

import sys
from pathlib import Path
if str(Path().resolve()) not in sys.path:
    sys.path.append(str(Path().resolve()))
import module.fastf1 as f1


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


def render():
    st.title(f"{st.session_state.year} Schedule")

    with st.spinner('Loading data...'):
        event_schedule = fastf1.get_event_schedule(st.session_state.year)
        event_schedule_pd = pd.DataFrame(event_schedule)

    for i, record in enumerate(event_schedule_pd.to_dict('records')):
        try:
            event = event_schedule.get_event_by_round(record['RoundNumber'])
        except ValueError:
            continue

        race_session = event.get_race()
        st.markdown(
            f"""
            - Round : <a href='/race?year={ st.session_state.year }&round={ record['RoundNumber'] }'>{ record['RoundNumber'] }</a>
            - Name : {record['OfficialEventName']}
            - Country : {record['Country']}
            - Location : {record['Location']}
            - Date : {race_session.date}
            """,
            unsafe_allow_html=True)


def main():
    init_session()
    set_query_string()
    render()


if __name__ == "__main__":
    main()
