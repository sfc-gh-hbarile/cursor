import streamlit as st
import pandas as pd
import snowflake.connector
import tomli
from snowflake.snowpark.context import get_active_session

# Set page config
st.set_page_config(
    page_title="Nation Viewer Table",
    page_icon="🌎",
    layout="wide"
)

# Function to get Snowflake connection - cached to prevent multiple MFA requests
@st.cache_resource(show_spinner="Connecting to Snowflake...")
def get_snowflake_connection():
    # First try to get active session (for Streamlit in Snowflake)
    try:
        session = get_active_session()
        if session:
            return session
    except Exception:
        # If get_active_session fails, continue to local connection
        pass
            
    # Try local connection
    try:
        with open('/Users/sweingartner/.snowflake/config.toml', 'rb') as f:
            config = tomli.load(f)
        
        # Get the default connection name
        default_conn = config.get('default_connection_name')
        if not default_conn:
            st.error("No default connection specified in config.toml")
            return None
            
        # Get the connection configuration for the default connection
        conn_params = config.get('connections', {}).get(default_conn)
        if not conn_params:
            st.error(f"Connection '{default_conn}' not found in config.toml")
            return None
        
        # Create a connection
        conn = snowflake.connector.connect(**conn_params)
        return conn
        
    except Exception as e:
        st.error(f"Failed to connect to Snowflake using local config: {str(e)}")
        return None

# Cache the query results to prevent unnecessary database hits
@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_nation_data(_conn):  # Added underscore to prevent hashing
    try:
        # Handle both session and connection types
        if hasattr(_conn, 'sql'):  # Snowpark session
            df = _conn.sql("""
                SELECT N_NATIONKEY, N_NAME, N_REGIONKEY, N_COMMENT
                FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION
            """).to_pandas()
        else:  # Regular connection
            cursor = _conn.cursor()
            cursor.execute("""
                SELECT N_NATIONKEY, N_NAME, N_REGIONKEY, N_COMMENT
                FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION
            """)
            df = pd.DataFrame(cursor.fetchall(), columns=['Nation Key', 'Nation Name', 'Region Key', 'Comment'])
        return df
    except Exception as e:
        st.error(f"Error querying data: {str(e)}")
        return None

# Get Snowflake connection
conn = get_snowflake_connection()
if not conn:
    st.error("Failed to connect to Snowflake. Please check your connection parameters.")
    st.stop()

# Title
st.title("🌎 Nation Data Viewer")
st.markdown("View data from the TPCH_SF1.NATION table")

# Fetch and display the data
df = fetch_nation_data(conn)
if df is not None:
    st.dataframe(df, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Data sourced from Snowflake Sample Data") 