import streamlit as st
import fastf1
import pandas

st.title('Race schedules')

# Add a selectbox to the sidebar:
selected_year = st.sidebar.selectbox(
    'Year',
    (2020, 2021, 2022, 2023)
)

if selected_year:
    event_schedule = fastf1.get_event_schedule(selected_year)
    event_schedule_pd = pandas.DataFrame(event_schedule)
    st.dataframe(event_schedule_pd)
    for i, record in enumerate(event_schedule_pd.to_dict('records')):
        try:
            event = event_schedule.get_event_by_round(record['RoundNumber'])
        except ValueError:
            continue

        race_session = event.get_race()
        st.markdown(
            f"""
            - Round : { record['RoundNumber'] }
            - Name : {record['OfficialEventName']}
            - Country : {record['Country']}
            - Location : {record['Location']}
            - Date : {race_session.date}
            """)
else:
    st.error("Please select year.")
