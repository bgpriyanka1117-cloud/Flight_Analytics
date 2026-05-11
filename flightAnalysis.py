import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from datetime import datetime
from streamlit_lottie import st_lottie
import requests
import json

# -----------------------------
# Streamlit Page Configuration
# -----------------------------
st.set_page_config(page_title="✈️ Flight Analytics Dashboard", layout="wide")
#st.title("✈️ Flight Analytics Dashboard")

st.markdown(
    '<h1 style="color:#1E90FF;">✈️ Flight Analytics Dashboard</h1>', 
    unsafe_allow_html=True
)
# =========================
# MySQL Connection
# =========================
@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",  # replace with your password
        database="Air_TrackerFlight_DB",
        port=3305,  # your DB port
        auth_plugin='mysql_native_password'
    )

conn = get_connection()

# =========================
# Load Data from Database
# =========================
@st.cache_data
def load_data():
    flights_query = "SELECT * FROM flights_data"
    airports_query = "SELECT * FROM airport_data"

    flights = pd.read_sql(flights_query, conn)
    airports = pd.read_sql(airports_query, conn)

    # Parse datetime columns safely
    datetime_cols = ['scheduled_departure', 'actual_departure', 'scheduled_arrival', 'actual_arrival']
    for col in datetime_cols:
        if col in flights.columns:
            flights[col] = pd.to_datetime(flights[col], errors='coerce')

    # Calculate delays in minutes
    if 'actual_departure' in flights.columns and 'scheduled_departure' in flights.columns:
        flights['departure_delay'] = (flights['actual_departure'] - flights['scheduled_departure']).dt.total_seconds() / 60
    else:
        flights['departure_delay'] = 0

    if 'actual_arrival' in flights.columns and 'scheduled_arrival' in flights.columns:
        flights['arrival_delay'] = (flights['actual_arrival'] - flights['scheduled_arrival']).dt.total_seconds() / 60
    else:
        flights['arrival_delay'] = 0

    return flights, airports

flights, airports = load_data()

# =========================
# Sidebar: Search & Filter
# =========================
st.sidebar.header("Search & Filter Flights")
search_number = st.sidebar.text_input("Search Flight Number")
search_airline = st.sidebar.text_input("Search Airline Code")
status_filter = st.sidebar.multiselect("Flight Status", options=flights['status'].unique())
origin_filter = st.sidebar.multiselect("Origin Airport", options=flights['origin_iata'].unique())
date_range = st.sidebar.date_input(
    "Date Range",
    [flights['scheduled_departure'].min().date(), flights['scheduled_departure'].max().date()]
)

# Apply filters
filtered = flights.copy()
if search_number:
    filtered = filtered[filtered['flight_number'].str.contains(search_number, case=False, na=False)]
if search_airline:
    filtered = filtered[filtered['airline_code'].str.contains(search_airline, case=False, na=False)]
if status_filter:
    filtered = filtered[filtered['status'].isin(status_filter)]
if origin_filter:
    filtered = filtered[filtered['origin_iata'].isin(origin_filter)]
filtered = filtered[
    (filtered['scheduled_departure'].dt.date >= date_range[0]) &
    (filtered['scheduled_departure'].dt.date <= date_range[1])
]

# =========================
# Homepage Summary
# =========================
#st.header("Summary Statistics")
#col1, col2, col3 = st.columns(3)
#col1.metric("Total Airports", airports.shape[0])
#col2.metric("Total Flights Fetched", flights.shape[0])
#col3.metric("Average Departure Delay (mins)", round(flights['departure_delay'].mean(), 2))

# =========================
# Homepage Summary (Colorful)
# =========================
st.header("Summary Statistics")

# Create 3 columns
col1, col2, col3 = st.columns(3)

# Total Airports
col1.markdown(f"""
<div style='background-color:#FFDEE9; padding:20px; border-radius:10px; text-align:center;'>
    <h3>Total Airports</h3>
    <h1 style='color:#D4145A'>{airports.shape[0]}</h1>
</div>
""", unsafe_allow_html=True)

# Total Flights
col2.markdown(f"""
<div style='background-color:#B5FFFC; padding:20px; border-radius:10px; text-align:center;'>
    <h3>Total Flights Fetched</h3>
    <h1 style='color:#1B998B'>{flights.shape[0]}</h1>
</div>
""", unsafe_allow_html=True)

# Average Departure Delay
avg_delay = round(flights['departure_delay'].mean(), 2)
delay_color = "#FF6B6B" if avg_delay > 30 else "#4ECDC4"  # Red if delay >30 mins else greenish

col3.markdown(f"""
<div style='background-color:#FFE6E6; padding:20px; border-radius:10px; text-align:center;'>
    <h3>Average Departure Delay (mins)</h3>
    <h1 style='color:{delay_color}'>{avg_delay}</h1>
</div>
""", unsafe_allow_html=True)




# =========================
# Airport Details Viewer
# =========================
st.header("Airport Details Viewer")
selected_airport = st.selectbox("Select Airport", airports['iata_code'])
airport_info = airports[airports['iata_code'] == selected_airport].iloc[0]

st.markdown(f"""
**Name:** {airport_info['name']}  
**City:** {airport_info['city']}  
**Country:** {airport_info['country']}  
**Continent:** {airport_info['continent']}  
**Timezone:** {airport_info['timezone']}  
**Linked Flights:** {flights[flights['origin_iata'] == selected_airport].shape[0]}
""")

# =========================
# Delay Analysis
# =========================
st.header("Delay Analysis")
delay_by_airport = flights.groupby('origin_iata')['departure_delay'].agg(['mean', 'count']).reset_index()
fig_delay = px.bar(
    delay_by_airport,
    x='origin_iata',
    y='mean',
    title="Average Departure Delay by Airport",
    text='mean',
    labels={'mean': 'Avg Delay (mins)', 'origin_iata': 'Airport'}
)
st.plotly_chart(fig_delay, use_container_width=True)

# =========================
# Route Leaderboards
# =========================
st.header("Route Leaderboards")

# Busiest Routes
st.subheader("Busiest Routes")
busiest_routes = flights.groupby(['origin_iata', 'destination_iata']).size().reset_index(name='flights_count')
st.dataframe(busiest_routes.sort_values(by='flights_count', ascending=False).head(10))

# Most Delayed Airports
st.subheader("Most Delayed Airports")
most_delayed = flights.groupby('origin_iata')['departure_delay'].mean().reset_index()
st.dataframe(most_delayed.sort_values(by='departure_delay', ascending=False).head(10))

# =========================
# Display Filtered Flights Table
# =========================
st.header("Filtered Flights Table")
st.dataframe(filtered.sort_values(by='scheduled_departure', ascending=False))