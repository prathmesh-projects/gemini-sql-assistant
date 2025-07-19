# Importing the needed libraries
import streamlit as st
from core import SQLAssistant, JSONSQLAssistant 
import json

# Defining the available datasets
# they will be a part of the drop-down menu

#Add the database names to the dict below to use them on your system
DATABASE_OPTIONS = {

    #Name for dropdown : #Name of the database in your system

    #Examples:-
    "Retail DB": "CS_Retail",
    "MSO": "MSO",
    "Mobiles": "Mobile_Mf",
}

# Configuration for MS SQL

#Add your system name here
SERVER_NAME = "ADD_YOUR_SYSTEM_NAME_HERE"
DRIVER_NAME = "SQL Server"

# Page titles and headers
st.title("👨‍💻 Gemini SQL Assistant for MS SQL Server")
st.markdown("Choose your mode and ask your question!")

# App info expander
with st.expander("ℹ️ About this app"):
    st.markdown("""
    This is a SQL assistant powered by **Gemini-2.5 Flash**.
    
    - Ask natural language questions.
    - Supports Microsoft SQL Server databases.
    - Works with either **Local Databases** or **JSON-formatted schema**.
    - Uses Gemini to generate SQL queries intelligently.
    """)

# Radio button for choosing between local DB or JSON schema
mode = st.radio("Available modes:", ["Local DBs", "JSON Schema"], horizontal=True)

# if the user selects to access the data from Local DB
if mode == "Local DBs":
    db_choice = st.selectbox("📁 Choose a database", list(DATABASE_OPTIONS.keys()))
    DATABASE_NAME = DATABASE_OPTIONS[db_choice]

    # Connection string
    CONNECTION_STRING = (
        f"Driver={{{DRIVER_NAME}}};"
        f"Server={SERVER_NAME};"
        f"Database={DATABASE_NAME};"
        "Trusted_Connection=yes;"
    )

    # Initialize assistant using cache
    @st.cache_resource
    def get_sql_assistant(conn_str):
        return SQLAssistant(conn_str)

    assistant = get_sql_assistant(CONNECTION_STRING)

    # Input query from the user
    user_query = st.text_input(" Ask your question")

    # Running the query if button is pressed with a non empty input
    if st.button("Run Query") and user_query.strip():
        with st.spinner("🔍 SQL-ing with Gemini "):
            #Getting the result from the LLM
            result = assistant.run(user_query)
            # Displaying the generated SQL Query
            st.subheader("🧾 Generated SQL Query")
            st.code(result.get("generated_sql", "No SQL generated"), language="sql")

            # Displaying results
            st.subheader("📊 Query Results")
            results = result.get("results", [])

            if isinstance(results, dict) and "error" in results:
                st.error(f"❌ Error: {results['error']}")
            elif not results:
                st.info("ℹ️ No results returned.")
            else:
                st.dataframe(results, use_container_width=True)

# if the user selects to give their DB Schema as JSON
elif mode == "JSON Schema":
    st.markdown("Paste your schema in JSON format below:")

    # Default schema for user's convenience
    default_schema = '''
    {
        "Customers": {
            "CustomerID": "INT",
            "Name": "VARCHAR",
            "Region": "VARCHAR"
        },
        "Orders": {
            "OrderID": "INT",
            "CustomerID": "INT",
            "Amount": "DECIMAL",
            "OrderDate": "DATE"
        }
    }
    '''

    # Input box for JSON schema
    json_input = st.text_area("🧾 JSON Schema", height=250, value=default_schema)

    # Input for user query
    user_query = st.text_input(" Ask your question based on the schema")

    # Running the query if button is pressed with a non empty input
    if st.button("Run Query") and json_input.strip() and user_query.strip():
        try:
            # Parse the JSON schema
            schema = json.loads(json_input)

            # Creating the assistant
            json_assistant = JSONSQLAssistant(schema)

            with st.spinner("🧠 Generating SQL from JSON Schema..."):
                #getting the result from the bot
                result = json_assistant.run(user_query)
                # Displaying the result
                st.subheader("🧾 Generated SQL Query")
                st.code(result.get("generated_sql", "No SQL generated"), language="sql")

        except json.JSONDecodeError as e:
            st.error(f"⚠️ Invalid JSON format: {e}")
        except Exception as e:
            st.error(f"❌ Error: {e}")
