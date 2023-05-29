import streamlit as st
import fastf1

st.title('Race')

data_load_state = st.text('Loading data...')
session = fastf1.get_session(2021, 22, 'R')
session.load()
data_load_state.text('')

event = session.event
event
session

st.subheader('Race information')
st.markdown(
    f"""
    <table>
        <tbody>
            <tr>
                <th>OfficialEventName</th>
                <td>{event.OfficialEventName}</td>
            </tr>
            <tr>
                <th>Round</th>
                <td>{event.RoundNumber}</td>
            </tr>
            <tr>
                <th>Country</th>
                <td>{event.Country}</td>
            </tr>
            <tr>
                <th>Location</th>
                <td>{event.Location}</td>
            </tr>
            <tr>
                <th>Laps</th>
                <td>{session.total_laps}</td>
            </tr>
        </tbody>
    </table>
    """,
    unsafe_allow_html=True)

st.subheader('Driver lineup')
st.write(session.results[['DriverNumber', 'FullName', 'TeamName', 'GridPosition']].sort_values(['GridPosition']))

st.subheader('Race results')
st.write(session.results[['DriverNumber', 'FullName', 'TeamName', 'GridPosition', 'Position', 'Points']].sort_values(['Position']))

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
