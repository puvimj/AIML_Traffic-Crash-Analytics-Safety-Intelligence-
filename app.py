import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

import base64
import altair as alt

# -------------------------------------------------------------------------
# 1. PAGE AND CONFIGURATION SETUP
# -------------------------------------------------------------------------
def get_base64_image(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Convert your saved clean local image
mainlayout_bg = get_base64_image("traffic_bg1.jpg")
sidebar_bg = get_base64_image("traffic_bg.jpg")

# Global UI layout styles - Fixed with doubled curly brackets
st.markdown(f"""
    <style>
        /* Force background layout injection */
        .stApp, [data-testid="stAppViewContainer"], .stAppDeployWithLayout {{
            background-image: linear-gradient(rgba(0, 255,255, 0.88), rgba(14, 17, 23, 0.92)), 
                              url("data:image/jpeg;base64,{mainlayout_bg}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
            
        }}
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <style>
        [data-testid="stSidebar"] {{
            background-image: linear-gradient(rgba(41, 86, 176, 0.90), rgba(14, 17, 23, 0.94)), 
                              url("data:image/jpeg;base64,{sidebar_bg}") !important;
            background-size: cover !important;
            background-position: center !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{ background: transparent !important; }}
    </style>
""", unsafe_allow_html=True)


def load_css(file_name: str):
    """Reads an external CSS file and injects its contents into the app."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>", unsafe_allow_html=True
            )
    except FileNotFoundError:
        st.error(
            f"❌ Style Load Error: Could not find the file '{file_name}'."
        )
load_css("style.css")

st.set_page_config(
    page_title="Traffic Crash Analytics and Safety Intelligence",
    page_icon="🚨",
    layout="wide",
)


# PostgreSQL connection details
DB_USER = "postgres"
DB_PASSWORD = "india*123"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "TrafficCrash"

# CSV file
CSV_FILE = r"C:\GUVI Projects\AIML_Traffic Crash Analytics & Safety Intelligence\trafficCrash\Traffic_CrashesData.csv"

# Table name
TABLE_NAME = "CrashTable"

# Create connection
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

if "db_initialized" not in st.session_state:
    print("Reading CSV...")

    df = pd.read_csv(CSV_FILE)

    print(f"Rows found: {len(df)}")

    print("Creating table and inserting data...")

    df.to_sql(
        name=TABLE_NAME,
        con=engine,
        if_exists="replace",   # Drops and recreates table
        index=False,
        chunksize=10000
    )

    print("Data Insertion Successful !")
    st.session_state.db_initialized = True
    
# -------------------------------------------------------------------------
# 2. SIDEBAR NAVIGATION LINKS
# -------------------------------------------------------------------------

def execute_sql(query_string: str) -> pd.DataFrame:
    """Safely runs queries and returns a dataframe."""
    with engine.connect() as conn:
        return pd.read_sql_query(text(query_string), conn)
    
with st.sidebar:
    st.title("Navigation")
    
    # Use a clean selectbox or radio group instead of raw text bullet points
    nav_selection = st.sidebar.radio(
        "Select Interface View:",
        ["📊 Dashboard", "📈 Crash Analytics"],
        label_visibility="collapsed"
    )


# -------------------------------------------------------------------------
# 3. DASHBOARD
# -------------------------------------------------------------------------
st.title('Traffic Crash Analytics and Safety Intelligence')

if nav_selection == "📊 Dashboard":
    
    st.markdown(
        "Real-time transactional insights processed directly from the master incident dataset."
    )
    st.divider()

    # -------------------------------------------------------------------------
    # 3A. METRIC CARDS ROW 
    # -------------------------------------------------------------------------
    try:
        # 1. Total Incidents 
        total_df = execute_sql('SELECT COUNT(*) as total FROM "CrashTable";')
        total_incidents = int(total_df["total"].iloc[0])

        # 2. Total Lives Lost (Summing the numerical column from your schema)
        fatal_sum_df = execute_sql('SELECT SUM("INJURIES_FATAL") as total_deaths FROM "CrashTable";')
        total_fatalities = int(fatal_sum_df["total_deaths"].fillna(0).iloc[0])

        # 3. Total Count of Incidents that involved at least one fatality
        fatal_incidents_df = execute_sql('SELECT COUNT(*) as total FROM "CrashTable" WHERE "INJURIES_FATAL" > 0;')
        fatal_incident_count = int(fatal_incidents_df["total"].iloc[0])

    except Exception as e:
        total_incidents, total_fatalities, fatal_incident_count = 0, 0, 0

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.metric(label="Total Traffic Incidents", value=f"{total_incidents:,}")
    with col_kpi2:
        st.metric(label="Total Fatalities (Lives Lost)", value=f"{total_fatalities:,}", 
                  help="Critical Tracker: Live aggregate count of recorded fatalities across all city road networks.")
    with col_kpi3:
        st.metric(label="Fatal Incidents Count", value=f"{fatal_incident_count:,}")

    st.divider()

    # -------------------------------------------------------------------------
    # 3B. TIME TRENDS AND COMMON CAUSES
    # -------------------------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Chronological Time-Based Trends")

        # Fixed Query: Uses explicit ::timestamp casting to handle TEXT inputs
        query_trends = """
        SELECT 
            EXTRACT(YEAR FROM TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM')) AS "Year",
            EXTRACT(MONTH FROM TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM'))  AS "Month Number",
            TO_CHAR(TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM'), 'Month') AS "Month Name",
            COUNT(*) AS "Crashes Recorded"
        FROM "CrashTable"
        GROUP BY 
            EXTRACT(YEAR FROM TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM')) , 
            EXTRACT(MONTH FROM TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM')) , 
            TO_CHAR(TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM'), 'Month')
        ORDER BY 
            "Year" DESC, 
            "Month Number" ASC;
        """

        try:
            df_trends = execute_sql(query_trends)

            if not df_trends.empty:
                # Format display configurations using st.dataframe to drop .0 floats
                st.dataframe(
                    df_trends,
                    column_config={
                        "Year": st.column_config.NumberColumn(format="%d"),
                        "Month Number": st.column_config.NumberColumn(format="%d"),
                    },
                    width='stretch',
                    hide_index=True,
                )

                # Automated Business Insight block
                top_year = int(df_trends["Year"].iloc[0])
                st.info(
                    f"**Business Insight:** Seasonal crash metrics for **{top_year}** display shifting risk baselines. "
                    "Resource distribution models should adjust dynamically during these peak historical months."
                )
            else:
                st.warning("No data rows returned for time trends analysis.")
        except Exception as e:
            st.error(f"Time Trends Query Failed: {e}")


    with col2:
        st.subheader("🛠️ Primary Root Cause Analysis")

        # Fixed Query: Uses '%%' to prevent python immutabledict token error
        query_causes = """
        SELECT 
            "PRIM_CONTRIBUTORY_CAUSE" AS "Primary Cause",
            COUNT(*) AS "Incident Count",
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM "CrashTable"), 2) AS "Percentage of Total (%%)"
        FROM "CrashTable"
        GROUP BY  "PRIM_CONTRIBUTORY_CAUSE"
        ORDER BY "Incident Count" DESC;
        """

        try:
            df_causes = execute_sql(query_causes)

            if not df_causes.empty:
                st.dataframe(
                    df_causes,
                    column_config={
                        "Percentage of Total (%)": st.column_config.NumberColumn(
                            format="%.2f%%"
                        )
                    },
                    width='stretch',
                    hide_index=True,
                )

                top_cause = df_causes["Primary Cause"].iloc[0]
                st.info(
                    f"**Business Insight:** Traffic disruptions are heavily driven by **{top_cause}**. "
                    "Targeted law enforcement updates and public safety campaigns should address this factor immediately."
                )
            else:
                st.warning("No data rows returned for root causes analysis.")
        except Exception as e:
            st.error(f"Root Causes Query Failed: {e}")

    st.divider()

    # -------------------------------------------------------------------------
    # 3C. SPATIAL DISTRIBUTION
    # -------------------------------------------------------------------------
    st.subheader("📊 Spatial Distribution of Incidents Across Streets")

    query_locations = """
        SELECT 
            "WEATHER_CONDITION" AS "Weather",
            COUNT(*) AS "Total Crashes"
        FROM "CrashTable"
        GROUP BY  "WEATHER_CONDITION"
        ORDER BY "Total Crashes" DESC;
    """

    try:
        df_locations = execute_sql(query_locations)

        if not df_locations.empty:
            # Layout columns to show table and simple horizontal bar chart side by side
            sub_col1, sub_col2 = st.columns([2, 3])

            with sub_col1:
                st.dataframe(df_locations, width='stretch', hide_index=True)

            # with sub_col2:
            #     st.bar_chart(
            #         data=df_locations,
            #         x="Weather",
            #         y="Total Crashes",
            #         width="stretch"
            #     )


            with sub_col2:
                # 1. Build the tracking line base layer
                base = alt.Chart(df_locations).encode(
                    y=alt.Y("Weather:N", sort="-x", title=None),
                    x=alt.X("Total Crashes:Q", scale=alt.Scale(type="log"), title="Total Crashes (Log Scale)")
                )
                
                # 2. Add technical connector lines
                lines = base.mark_rule(color="rgba(255, 255, 255, 0.15)", strokeWidth=1.5)
                
                # 3. Add prominent circular target nodes that register hovers flawlessly
                nodes = base.mark_circle(color="#00B4D8", size=110).encode(
                    tooltip=[
                        alt.Tooltip("Weather:N", title="Condition"),
                        alt.Tooltip("Total Crashes:Q", title="Crashes", format=",")
                    ]
                )
                
                # 4. Combine layers and adjust fonts to match your custom stylesheet
                lollipop_chart = (lines + nodes).properties(
                    height=400
                ).configure_axisY(
                    labelFontSize=11,
                    labelLimit=160
                ).configure_view(
                    strokeOpacity=0
                )
                
                st.altair_chart(lollipop_chart, width="stretch")


            top_weather = df_locations["Weather"].iloc[0]

            st.info(
                f"**Business Insight:** Analysis of crash distribution by weather condition reveals the environmental factors "
                f" contributing to road accidents. While most crashes occur during **{top_weather}** "
                f" weather due to higher traffic exposure, adverse weather conditions such as rain"
                f" and fog increase crash risk per trip, highlighting the need for weather-responsive traffic management strategies."
            )
        else:
            st.warning("No geographical location data rows were returned.")
    except Exception as e:
        st.error(f"Spatial Distribution Query Failed: {e}")

# 4. CRASH ANALYTICS
else:
    st.markdown("Select an analytical safety question from the dropdown selection box below to run its corresponding database query.")
    st.divider()

    analytics_options = [
        "Select ...",
        "Q1: Top 5 most dangerous combinations of weather and crash type",
        "Q2: Top 10 streets with the highest number of injury crashes",
        "Q3: Percentage of crashes that resulted in injuries for each crash type",
        "Q4: Peak crash hour for each month",        
        "Q5: Top 5 primary causes of crashes at night (Hour ≥ 18)",

        "Q6: Average injuries : Daylight vs. Darkness",
        "Q7: Traffic control device type having highest average injuries per crash",
        "Q8: Top 5 locations  (latitude/longitude) with the highest crash frequency",
        "Q9: Top 5 streets with highest injury rates (>100 crashes)",
        "Q10: Most common crash per calendar year",

        "Q11: Day of the week with the highest average crashes per hour",
        "Q12: High-risk time slot shifts (Morning, Afternoon, Evening, Night)",
        "Q13: Top 3 contributing causes for each crash type",
        "Q14: Year-over-Year growth rate of crashes",
        "Q15: Top 10 regional hotspot zones (Rounded latitude & longitude)",

    ]

    chosen_question = st.selectbox(
        label="🔍 Select Safety Query :",
        options=analytics_options,
        index=0
    )
    st.divider()

    output_container = st.container()

    with output_container:
        if chosen_question == "Select ...":
            st.info("💡 Please choose an analytical reporting question from the selection box above to pull down live metrics.")

        # --- QUERY 1 ---
        elif chosen_question.startswith("Q1:"):
            st.subheader("📊 Top 5 Most Dangerous Weather and Crash Type Combinations")
            sql = """
                SELECT "WEATHER_CONDITION" AS "Weather Condition", "FIRST_CRASH_TYPE" AS "Crash Type", COUNT(*) AS "Total Crashes"
                FROM "CrashTable"
                GROUP BY "WEATHER_CONDITION", "FIRST_CRASH_TYPE"
                ORDER BY "Total Crashes" DESC LIMIT 5;
            """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1, width="stretch", hide_index=True)
                st.info(f"**Business Insight:** The worst risk cluster forms during **{df1['Weather Condition'].iloc[0]}** weather involving **{df1['Crash Type'].iloc[0]}** incidents.")
            except Exception as e:
                st.error(f"Execution Error: {e}")
        
        # --- QUERY 2 ---
        elif chosen_question.startswith("Q2:"):
            st.subheader("📍 Top 10 Streets with the Highest Number of Injury Crashes")
            sql = """
                SELECT "STREET_NAME" AS "Street Name", 
                    COUNT(*) AS "Injury Crashes Count", 
                    SUM("INJURIES_TOTAL"::int) AS "Total Injuries Inflicted"
                FROM "CrashTable"
                WHERE "INJURIES_TOTAL" IS NOT NULL AND "INJURIES_TOTAL"::int > 0
                GROUP BY "STREET_NAME"
                ORDER BY "Injury Crashes Count" DESC LIMIT 10;
            """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1, width="stretch", hide_index=True)
                st.info(f"**Business Insight:** **{df1['Street Name'].iloc[0]}** flags as the most dangerous local transit line for injuries.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 3 ---
        elif chosen_question.startswith("Q3:"):
            st.subheader("📈 Percentage of Crashes Resulting in Injuries by Type")
            sql = """
                SELECT "FIRST_CRASH_TYPE" AS "Crash Type", COUNT(*) AS "Total Incidents",
                       ROUND(100.0 * COUNT(CASE WHEN "INJURIES_TOTAL"::int > 0 THEN 1 END) / COUNT(*), 2) AS "Injury Probability (%%)"
                FROM "CrashTable"
                GROUP BY "FIRST_CRASH_TYPE"
                ORDER BY "Injury Probability (%%)" DESC;
            """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1, width="stretch", hide_index=True)
                st.info(f"**Business Insight:** **{df1['Crash Type'].iloc[0]}** carries the highest proportional likelihood of physical harm to motorists.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 4 ---
        elif chosen_question.startswith("Q4:"):
            st.subheader("📅 Calculated Chronological Peak Crash Hour per Calendar Month")
            sql = """
                WITH HourlyMonthlyAggregates AS (
                    SELECT "CRASH_MONTH" AS "Month Number", "CRASH_HOUR"::int AS "Crash Hour", COUNT(*) AS "Incident Count",
                           ROW_NUMBER() OVER(PARTITION BY "CRASH_MONTH" ORDER BY COUNT(*) DESC) AS rank
                    FROM "CrashTable"
                    GROUP BY "CRASH_MONTH", "CRASH_HOUR"
                )
                SELECT "Month Number", "Crash Hour" AS "Peak Crash Hour", "Incident Count" AS "Crashes Recorded"
                FROM HourlyMonthlyAggregates WHERE rank = 1 ORDER BY "Month Number"::int ASC;
            """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1, column_config={"Month Number": st.column_config.NumberColumn(format="%d"), "Peak Crash Hour": st.column_config.NumberColumn(format="%d")}, width="stretch", hide_index=True)
                st.info(f"**Business Insight:** Peak crash clusters typically stabilize around the hour of **{df1['Peak Crash Hour'].max()}** across high-volume traffic intervals.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 5 ---
        elif chosen_question.startswith("Q5:"):
            st.subheader("🌙 Top 5 primary causes of crashes at night (Hour ≥ 18)")
            sql = """
                SELECT 
                    "PRIM_CONTRIBUTORY_CAUSE" AS "Primary Cause", 
                    COUNT(*) AS "Total Crashes"
                FROM "CrashTable" WHERE "CRASH_HOUR"::int >= 18 
                GROUP BY "PRIM_CONTRIBUTORY_CAUSE" 
                ORDER BY "Total Crashes" DESC LIMIT 5;
            """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1, width="stretch", hide_index=True)
                st.info(
                    f"**Business Insight:** Nighttime crashes are heavily driven by **{df1['Primary Cause'].iloc[0]}**. Targeted police visibility after 18:00 should address this behavior."
                )
            except Exception as e:
                st.error(f"Execution Error: {e}")

        
        # --- QUERY 6 ---
        elif chosen_question.startswith("Q6:"):
            st.subheader("☀️ Average injuries : Daylight vs. Darkness")
            sql = """
                SELECT 
                    CASE WHEN "LIGHTING_CONDITION" ILIKE '%%DAYLIGHT%%' THEN 
                        'Daylight' 
                    ELSE 'Darkness' 
                    END AS "Light Condition",
                    ROUND(AVG("INJURIES_TOTAL"::int), 4) AS "Average Injuries"
                FROM "CrashTable" 
                WHERE "LIGHTING_CONDITION" IS NOT NULL
                GROUP BY 
                    CASE WHEN "LIGHTING_CONDITION" ILIKE '%%DAYLIGHT%%' THEN 
                        'Daylight' 
                    ELSE 'Darkness' 
                    END
                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1, width="stretch", hide_index=True)

                higher_cond = (df1.sort_values("Average Injuries", ascending=False).iloc[0]["Light Condition"])
                st.info(
                    f"**Business Insight:** The average physical injury rate trends higher under **{higher_cond}**. This proves visibility conditions heavily impact crash severity levels."
                )
            except Exception as e:
                st.error(f"Execution Error: {e}")


        # --- QUERY 7 ---
        elif chosen_question.startswith("Q7:"):
            st.subheader("🛑 Traffic control device type having highest average injuries per crash")
            sql = """
                SELECT 
                    "TRAFFIC_CONTROL_DEVICE" AS "Control Device", 
                    COUNT(*) AS "Total Crashes",
                    ROUND(AVG("INJURIES_TOTAL"::int), 4) AS "Average Injuries"
                FROM "CrashTable" 
                GROUP BY "TRAFFIC_CONTROL_DEVICE" HAVING COUNT(*) > 100 
                ORDER BY "Average Injuries" DESC;
                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1, width="stretch", hide_index=True)
                top_device = df1["Control Device"].iloc[0]
                top_avg = df1["Average Injuries"].iloc[0]

                st.info(
                    f"**Business Insight:** Collisions occurring near **{top_device}** zones produce the highest physical severity multiplier, "
                    f"averaging **{top_avg:.4f}** injuries per individual crash. "
                    f"Civic safety engineering teams should prioritize evaluating signal visibility and timing sequences at these specific locations."
                    )
            except Exception as e:
                st.error(f"Execution Error: {e}")


        # --- QUERY 8 ---
        elif chosen_question.startswith("Q8:"):
            st.subheader("🌐 Top 5 locations  (latitude/longitude) with the highest crash frequency")
            sql = """
                SELECT 
                    TRUNC("LATITUDE"::numeric, 4) AS "Latitude", 
                    TRUNC("LONGITUDE"::numeric, 4) AS "Longitude", 
                    COUNT(*) AS "Total Crashes"
                FROM "CrashTable" 
                WHERE "LATITUDE" IS NOT NULL 
                    AND "LONGITUDE" IS NOT NULL
                GROUP BY "LATITUDE", "LONGITUDE" 
                ORDER BY "Total Crashes" DESC LIMIT 5
                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1, width="stretch", hide_index=True)
                st.info(f"**Business Insight:** The exact coordinates at Latitude **{df1['Latitude'].iloc[0]}**, Longitude **{df1['Longitude'].iloc[0]}** flag as the most dangerous square layout hotspot in the city.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 9 ---
        elif chosen_question.startswith("Q9:"):
            st.subheader("🛣️ Top 5 streets with highest injury rates (>100 crashes)")
            sql = """
                SELECT 
                    "STREET_NAME" AS "Street Name", 
                    ROUND(100.0 * COUNT(
                        CASE WHEN "INJURIES_TOTAL"::int > 0 THEN 1 END) / COUNT(*), 2) 
                        AS "Injury Rate (%%)"
                FROM "CrashTable" 
                GROUP BY "STREET_NAME" HAVING COUNT(*) > 100 
                ORDER BY "Injury Rate (%%)" DESC LIMIT 5;

                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1,column_config={"Injury Rate (%)": st.column_config.NumberColumn(format="%.2f%%")},width="stretch",hide_index=True,)
                st.info(f"**Business Insight:** Out of all **{df1['Street Name'].iloc[0]}** has the highest proportional injury conversion rate (**{df1['Injury Rate (%%)'].iloc[0]}%**).")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 10 ---
        elif chosen_question.startswith("Q10:"):
            st.subheader("📅  Most common crash per calendar year")
            sql = """
                WITH YearTable AS 
                    (SELECT 
                        "year"::int AS "Year", 
                        "FIRST_CRASH_TYPE" AS "Crash Type", 
                        COUNT(*) AS "Count",
                        ROW_NUMBER() OVER(PARTITION BY "year" ORDER BY COUNT(*) DESC) AS rank
                    FROM "CrashTable" 
                    WHERE "year" IS NOT NULL 
                    GROUP BY "year", "FIRST_CRASH_TYPE")
                    SELECT "Year", "Crash Type", "Count" AS "Incident Count" 
                    FROM YearTable WHERE rank = 1 ORDER BY "Year" DESC;

                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1,column_config={"Year": st.column_config.NumberColumn(format="%d")},width="stretch",hide_index=True,)
                st.info(f"**Business Insight:** Across multiple reporting cycles, **{df1['Crash Type'].iloc[0]}** remains the most dominant crash dynamic year after year.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 11 ---
        elif chosen_question.startswith("Q11:"):
            st.subheader("📅 Day of the week with the highest average crashes per hour")
            sql = """
                SELECT 
                    CASE "CRASH_DAY_OF_WEEK"::int
                        WHEN 1 THEN 'Sunday' 
                        WHEN 2 THEN 'Monday' WHEN 3 THEN 'Tuesday' 
                        WHEN 4 THEN 'Wednesday'
                        WHEN 5 THEN 'Thursday' 
                        WHEN 6 THEN 'Friday' 
                        WHEN 7 THEN 'Saturday' 
                    END AS "Day of Week",
                    ROUND(COUNT(*)::numeric / 24.0, 2) AS "Average Crashes Per Hour"
                FROM "CrashTable" 
                WHERE "CRASH_DAY_OF_WEEK" IS NOT NULL 
                GROUP BY "CRASH_DAY_OF_WEEK" 
                ORDER BY "Average Crashes Per Hour" DESC LIMIT 1;

                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1,column_config={"Year": st.column_config.NumberColumn(format="%d")},width="stretch",hide_index=True,)
                st.info(f"**Business Insight:** **{df1['Day of Week'].iloc[0]}** exhibits the highest continuous density of incidents, averaging **{df1['Average Crashes Per Hour'].iloc[0]}** crashes every hour.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 12 ---
        elif chosen_question.startswith("Q12:"):
            st.subheader("🕒 High-risk time slot shifts (Morning, Afternoon, Evening, Night)")
            sql = """
                SELECT 
                    CASE WHEN "CRASH_HOUR"::int BETWEEN 5 AND 11 THEN 'Morning (05-11)'
                        WHEN "CRASH_HOUR"::int BETWEEN 12 AND 16 THEN 'Afternoon (12-16)'
                        WHEN "CRASH_HOUR"::int BETWEEN 17 AND 21 THEN 'Evening (17-21)' 
                    ELSE 'Night (22-04)' 
                    END AS "Time Slot Bucket",
                    COUNT(CASE WHEN "INJURIES_TOTAL"::int > 0 THEN 1 END) AS "Total Count", 
                    SUM("INJURIES_TOTAL"::int) AS "Total Injuries Logged"
                FROM "CrashTable" 
                WHERE "CRASH_HOUR" IS NOT NULL
                GROUP BY 1 
                ORDER BY "Total Count" DESC;

                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1,column_config={"Year": st.column_config.NumberColumn(format="%d")},width="stretch",hide_index=True,)
                st.info(f"**Business Insight:** The **{df1['Time Slot Bucket'].iloc[0]}** block is the highest-risk shift for injury-related accidents. Emergency crew shifts should align with this window.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 13 ---
        elif chosen_question.startswith("Q13:"):
            st.subheader("🛠️ Top 3 contributing causes for each crash type")
            sql = """
                WITH CauseMetricsRanked AS 
                    (SELECT "FIRST_CRASH_TYPE" AS "Crash Type", 
                    "PRIM_CONTRIBUTORY_CAUSE" AS "Contributing Cause", 
                    COUNT(*) AS "Count",
                    ROW_NUMBER() OVER(PARTITION BY "FIRST_CRASH_TYPE" ORDER BY COUNT(*) DESC) AS rank
                FROM "CrashTable" 
                GROUP BY "FIRST_CRASH_TYPE", "PRIM_CONTRIBUTORY_CAUSE")
                SELECT "Crash Type", "Contributing Cause", "Count" AS "Incident Count"
                FROM CauseMetricsRanked 
                WHERE rank <= 3 
                ORDER BY "Crash Type" ASC, "Incident Count" DESC;

                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1,column_config={"Year": st.column_config.NumberColumn(format="%d")},width="stretch",hide_index=True,)
                st.info(
                    f"**Business Insight:** Root-cause profiles change drastically depending on the type of collision. "
                    f"The data indicates that **{df1['Crash Type'].iloc[0]}** incidents are most frequently caused by **{df1['Contributing Cause'].iloc[0]}**. "
                    f"Notably, the contributing cause flagged as **{df1['Contributing Cause'].iloc[1]}**, highlights a critical "
                    f"data-logging gap. Immediate action is required to upgrade post-crash investigation protocols and ensure "
                    f"better reporting accuracy."
                )
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 14 ---
        elif chosen_question.startswith("Q14:"):
            st.subheader("📈 Year-over-Year growth rate of crashes")
            sql = """
                WITH AnnualTotals AS 
                (SELECT 
                    "year"::int AS "Year", 
                    COUNT(*) AS "Current Year Crashes"
                FROM "CrashTable" 
                WHERE "year" IS NOT NULL 
                GROUP BY "year"),HistoricalTrends AS 
                (SELECT 
                    "Year", 
                    "Current Year Crashes", 
                    LAG("Current Year Crashes", 1) OVER (ORDER BY "Year" ASC) 
                        AS "Previous Year Crashes"
                FROM AnnualTotals)
                SELECT 
                    "Year", 
                    "Current Year Crashes", 
                    "Previous Year Crashes",
                    ROUND(100.0 * ("Current Year Crashes" - "Previous Year Crashes") / "Previous Year Crashes", 2) AS "YoY Growth Rate (%)"
                FROM HistoricalTrends ORDER BY "Year" DESC;
                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1,column_config={"Year": st.column_config.NumberColumn(format="%d"),
                                                "YoY Growth Rate (%)": st.column_config.NumberColumn(format="%.2f%%"),},
                                                width="stretch",hide_index=True,)
                st.info(f"**Business Insight:** The structural macro trend shows an active annual growth rate fluctuation of"
                        f" **{df1['YoY Growth Rate (%)'].iloc[0]}%** in overall incident registration records.")
            except Exception as e:
                st.error(f"Execution Error: {e}")

        # --- QUERY 15 ---
        elif chosen_question.startswith("Q15:"):
            st.subheader("🗺️ Top 10 regional hotspot zones (Rounded latitude & longitude)")
            sql = """
                SELECT 
                    ROUND("LATITUDE"::numeric, 2) AS "Zone Latitude", 
                    ROUND("LONGITUDE"::numeric, 2) AS "Zone Longitude",
                    COUNT(*) AS "Total Crashes in Zone"
                FROM "CrashTable" 
                WHERE "LATITUDE" IS NOT NULL AND 
                    "LONGITUDE" IS NOT NULL
                GROUP BY "Zone Latitude","Zone Longitude"
                ORDER BY "Total Crashes in Zone" DESC LIMIT 10;
                """
            try:
                df1 = execute_sql(sql)
                st.dataframe(df1,width="stretch",hide_index=True,)
                st.info(
                    f"**Business Insight:** The macro grid area at **{df1['Zone Latitude'].iloc[0]} / {df1['Zone Longitude'].iloc[0]}** "
                    F" contains the highest density of incidents city-wide. This indicates a high-priority zone for safety audits."
                )
            except Exception as e:
                st.error(f"Execution Error: {e}")