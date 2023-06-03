import streamlit as st
import fastf1
import pandas

st.title('Race schedules')

if 'year' not in st.session_state:
    query_params = st.experimental_get_query_params()
    if 'year' in query_params:
        st.session_state.year = int(query_params['year'][0])
    else:
        st.session_state.year = 2020

# Add a selectbox to the sidebar:
selected_year = st.sidebar.selectbox(
    'Year',
    (2020, 2021, 2022, 2023),
    key='year'
)

st.experimental_set_query_params(
    year=selected_year
)

if selected_year:
    data_load_state = st.text('Loading data...')
    event_schedule = fastf1.get_event_schedule(selected_year)
    event_schedule_pd = pandas.DataFrame(event_schedule)
    data_load_state.text('')

    st.dataframe(event_schedule_pd)
    for i, record in enumerate(event_schedule_pd.to_dict('records')):
        try:
            event = event_schedule.get_event_by_round(record['RoundNumber'])
        except ValueError:
            continue

        race_session = event.get_race()
        st.markdown(
            f"""
            - Round : <a href='/race?year={ selected_year }&round={ record['RoundNumber'] }'>{ record['RoundNumber'] }</a>
            - Name : {record['OfficialEventName']}
            - Country : {record['Country']}
            - Location : {record['Location']}
            - Date : {race_session.date}
            """,
            unsafe_allow_html=True)
else:
    st.error("Please select year.")
