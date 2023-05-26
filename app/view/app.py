import streamlit as st
import fastf1
import pandas

st.write('Hello')

event_schedule = fastf1.get_event_schedule(2022)
pd = pandas.DataFrame(event_schedule)
st.write(pd)

event = fastf1.get_event(2022, 1)
st.write(event.get_race())
