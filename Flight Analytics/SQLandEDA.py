import streamlit as st
import pandas as pd
import mysql.connector

st.set_page_config(page_title="Flight Analytics", layout="wide")

st.title("✈️ Flight Analytics Dashboard")

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
# FUNCTION TO RUN QUERY
# =========================
def run_query(query):
    return pd.read_sql(query, conn)

# =========================
# 1. Flights per Aircraft Model
# =========================
st.header("📊 Flights per Aircraft Model")

q1 = """
SELECT model, COUNT(*) AS total_flights
FROM aircraft_data
GROUP BY model
ORDER BY total_flights DESC;
"""

df1 = run_query(q1)
st.dataframe(df1, use_container_width=True)
st.bar_chart(df1.set_index('model'))


# =========================
# 2. Aircraft with >5 Flights
# =========================

st.header("🛫 Aircraft Used in More Than 5 Flights")

q2 = """
SELECT 
    a.registration,
    a.model,
    COUNT(f.flight_id) AS total_flights
FROM aircraft_data a
JOIN flights_data f
    ON a.registration = f.aircraft_registration
GROUP BY a.registration, a.model
HAVING COUNT(f.flight_id) > 5;
"""

# -------------------------------
# RUN & DISPLAY
# -------------------------------
try:
    df2 = pd.read_sql(q2, conn)

    st.dataframe(df2, use_container_width=True)

    # Optional chart
    st.subheader("📊 Flights per Aircraft")
    st.bar_chart(df2.set_index('registration')['total_flights'])

except Exception as e:
    st.error(f"Error: {e}")

# =========================
# 3. Airports with >5 Outbound Flights
# =========================
st.header("🌍 Airports with More Than 5 Outbound Flights")

q3 = """
SELECT 
    origin_iata AS airport_name,
    COUNT(*) AS outbound_flights
FROM flights_data
GROUP BY origin_iata
HAVING COUNT(*) > 5
ORDER BY outbound_flights DESC;
"""

# -------------------------------
# RUN & DISPLAY
# -------------------------------
try:
    df3 = pd.read_sql(q3, conn)

    st.dataframe(df3, use_container_width=True)

    # Chart
    st.subheader("📊 Airports with >5 Outbound Flights")
    st.bar_chart(df3.set_index('airport_name')['outbound_flights'])

except Exception as e:
    st.error(f"Error: {e}")

# =========================
# Question 4
# Top 3 Destination Airports
# =========================
st.header("🏆 Top 3 Destination Airports by Arrivals")

q4 = """
SELECT 
    a.name AS airport_name,
    a.city,
    COUNT(f.flight_id) AS arriving_flights
FROM flights_data f
JOIN airport_data a
    ON f.destination_iata = a.iata_code
GROUP BY a.name, a.city
ORDER BY arriving_flights DESC
LIMIT 3;
"""

# -------------------------------
# RUN & DISPLAY
# -------------------------------
try:
    df4 = pd.read_sql(q4, conn)

    # Table
    st.dataframe(df4, use_container_width=True)

    # Chart
    st.subheader("📊 Top 3 Destination Airports")
    st.bar_chart(df4.set_index('airport_name')['arriving_flights'])

except Exception as e:
    st.error(f"Error: {e}")

# =========================
# Flight Type Classification
# =========================
st.header("✈️ Flight Type: Domestic vs International")

q5 = """
SELECT 
    f.flight_number,
    f.origin_iata AS origin,
    f.destination_iata AS destination,

    CASE 
        WHEN a1.country = a2.country THEN 'Domestic'
        ELSE 'International'
    END AS flight_type

FROM flights_data f

JOIN airport_data a1 
    ON f.origin_iata = a1.iata_code

JOIN airport_data a2 
    ON f.destination_iata = a2.iata_code;
"""

# -------------------------------
# RUN & DISPLAY
# -------------------------------
try:
    df5 = pd.read_sql(q5, conn)

    # Show table
    st.dataframe(df5, use_container_width=True)

    # Optional: Flight type distribution chart
    st.subheader("📊 Flight Type Distribution")
    st.bar_chart(df5['flight_type'].value_counts())

except Exception as e:
    st.error(f"Error: {e}")

# =========================
# Question 6
# 5 Most Recent Arrivals at DEL
# =========================
st.header("🛬 Latest 5 Arrivals at DEL Airport")

q6 = """
SELECT 
    f.flight_number,
    a.model AS aircraft,
    ap.name AS departure_airport,
    f.actual_arrival AS arrival_time

FROM flights_data f

JOIN aircraft_data a 
    ON f.aircraft_registration = a.registration

JOIN airport_data ap 
    ON f.origin_iata = ap.iata_code

WHERE f.destination_iata = 'DEL'

ORDER BY f.actual_arrival DESC
LIMIT 5;
"""

# -------------------------------
# RUN & DISPLAY
# -------------------------------
try:
    df6 = pd.read_sql(q6, conn)

    # Table
    st.dataframe(df6, use_container_width=True)

    # Optional chart (arrival timeline)
    st.subheader("📊 Arrival Timeline")
    st.line_chart(df6.set_index('arrival_time'))

except Exception as e:
    st.error(f"Error: {e}")

# =========================
#7. Airports with No Arrivals
# =========================
st.header("🚫 Airports with No Arriving Flights")

q7 = """
SELECT 
    a.name AS airport_name,
    a.city,
    a.iata_code
FROM airport_data a
LEFT JOIN flights_data f
    ON a.iata_code = f.destination_iata
WHERE f.destination_iata IS NULL;
"""

try:
    df7 = pd.read_sql(q7, conn)

    st.dataframe(df7, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")

# =========================
# Question 8
# Flights by Status per Airline
# =========================
st.header("✈️ Airline-wise Flight Status")

q8 = """
SELECT 
    f.airline_code,

    COUNT(CASE WHEN f.status = 'On Time' THEN 1 END) AS on_time_flights,
    COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) AS delayed_flights,
    COUNT(CASE WHEN f.status = 'Cancelled' THEN 1 END) AS cancelled_flights

FROM flights_data f

GROUP BY f.airline_code
ORDER BY f.airline_code;
"""

# -------------------------------
# RUN & DISPLAY
# -------------------------------
try:
    df8 = pd.read_sql(q8, conn)

    # Table
    st.dataframe(df8, use_container_width=True)

    # Chart
    st.subheader("📊 Flight Status by Airline")
    st.bar_chart(df8.set_index('airline_code'))

except Exception as e:
    st.error(f"Error: {e}")

# =========================
# 9.Cancelled Flights
# =========================
st.header("❌ Cancelled Flights Overview")

q9 = """
SELECT 
    f.flight_number,
    a.model AS aircraft,

    ap1.name AS departure_airport,
    ap2.name AS arrival_airport,

    f.scheduled_departure AS departure_time

FROM flights_data f

JOIN aircraft_data a
    ON f.aircraft_registration = a.registration

JOIN airport_data ap1
    ON f.origin_iata = ap1.iata_code

JOIN airport_data ap2
    ON f.destination_iata = ap2.iata_code

WHERE f.status = 'Cancelled'

ORDER BY f.scheduled_departure DESC;
"""

# -------------------------------
# RUN & DISPLAY
# -------------------------------
try:
    df9 = pd.read_sql(q9, conn)

    # Table
    st.dataframe(df9, use_container_width=True)

    # Optional chart (count per airport)
    st.subheader("📊 Cancelled Flights by Origin Airport")
    st.bar_chart(df9['origin_airport'].value_counts())

except Exception as e:
    st.error(f"Error: {e}")

# =========================
# City Pairs with Multiple Aircraft Models
# =========================
st.header("🌍 City Pairs with >2 Aircraft Models")

q10 = """
SELECT 
    ap1.city AS origin_city,
    ap2.city AS destination_city,
    COUNT(DISTINCT a.model) AS aircraft_models_count
FROM flights_data f
JOIN aircraft_data a
    ON f.aircraft_registration = a.registration
JOIN airport_data ap1
    ON f.origin_iata = ap1.iata_code
JOIN airport_data ap2
    ON f.destination_iata = ap2.iata_code
GROUP BY ap1.city, ap2.city
HAVING COUNT(DISTINCT a.model) > 2
ORDER BY aircraft_models_count DESC;
"""

try:
    df10 = pd.read_sql(q10, conn)

    st.dataframe(df10, use_container_width=True)

    # Chart
    st.subheader("📊 Aircraft Diversity by Route")
    st.line_chart(df10.set_index('origin_city')['aircraft_models_count'])

except Exception as e:
    st.error(f"Error: {e}")

# =========================
# Delay Percentage by Airport
# =========================
st.header("⏱️ Delay % by Destination Airport")

q11 = """
SELECT 
    ap.name AS airport_name,
    ap.city,
    COUNT(*) AS total_arrivals,
    COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) AS delayed_flights,
    ROUND(
        (COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) * 100.0) 
        / COUNT(*), 
        2
    ) AS delay_percentage
FROM flights_data f
JOIN airport_data ap
    ON f.destination_iata = ap.iata_code
GROUP BY ap.name, ap.city
ORDER BY delay_percentage DESC;
"""

try:
    df11 = pd.read_sql(q11, conn)

    st.dataframe(df11, use_container_width=True)

    # Chart
    st.subheader("📊 Delay % by Airport")
    st.bar_chart(df11.set_index('airport_name')['delay_percentage'])

except Exception as e:
    st.error(f"Error: {e}")