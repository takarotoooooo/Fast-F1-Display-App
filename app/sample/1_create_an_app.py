import streamlit as st
import numpy as np
import pandas as pd

DATE_COLUMN = 'date/time'
DATA_URL = (
    'https://s3-us-west-2.amazonaws.com/'
    'streamlit-demo-data/uber-raw-data-sep14.csv.gz')

st.set_page_config(
    page_title="Create an app",
    page_icon="👋",
)


@st.cache_data
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    data.rename(lambda x: str(x).lower(), axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data


def render():
    st.title('Create an app')
    st.text('https://docs.streamlit.io/library/get-started/create-an-app')

    data_load_state = st.text('Loading data...')
    # Load 10,000 rows of data into the dataframe.
    data = load_data(10000)
    # Notify the reader that the data was successfully loaded.
    data_load_state.text('Loading data...done!')

    if st.checkbox('Show raw data'):
        st.subheader('Raw data')
        st.write(data)

    st.subheader('Number of pickups by hour')
    hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0, 24))[0]
    st.bar_chart(hist_values)

    hour_to_filter = st.slider('hour', 0, 23, 17)  # min: 0h, max: 23h, default: 17h
    filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]
    st.subheader(f'Map of all pickups at {hour_to_filter}:00')
    st.map(filtered_data)


def main():
    render()


if __name__ == "__main__":
    main()
