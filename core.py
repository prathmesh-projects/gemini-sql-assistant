# Importing the needed libraries
import pyodbc
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# Base class for common SQL generation logic
class SQLGenerator:
    def __init__(self):
        # Loading API key from .env
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")

        # Configuring Gemini with key and Gemini 2.5 Flash Model
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    # This function configures the LLM with a prompt to solve user queries
    def generate_sql_query(self, schema, question):
        prompt = f"""
        You are an expert SQL assistant. Generate a valid SQL query for Microsoft SQL Server only.
        Analyze the user request step by step carefuly while generating the query.
        Use SELECT TOP n instead of LIMIT n. LIMIT is invalid in SQL Server.

        SCHEMA:
        {schema}

        QUESTION:
        {question}

        SQL QUERY:
        """

        # The response from the model will be saved in the Response variable
        response = self.model.generate_content(prompt)

        # Cleaning the output to remove markdown-style code blocks
        cleaned = response.text.strip()
        cleaned = re.sub(r"```(?:sql)?\s*([\s\S]*?)\s*```", r"\1", cleaned, flags=re.IGNORECASE).strip()

        # Since LIMIT is an invalid command in MS SQL, TOP is to be used.
        # if LIMIT is found in the response, it will be replaced by TOP
        limit_match = re.search(r"LIMIT\s+(\d+)", cleaned, re.IGNORECASE)

        if limit_match:
            # Extracting the number next to LIMIT
            top_n = limit_match.group(1)
            # Remove LIMIT
            cleaned = re.sub(r"LIMIT\s+\d+\s*;?", "", cleaned, flags=re.IGNORECASE)
            # Substitute TOP n (top_n) after SELECT, after removing LIMIT
            cleaned = re.sub(
                r"(?i)SELECT\s+",
                f"SELECT TOP {top_n} ",
                cleaned,
                count=1
            )
        return cleaned

# SQLAssistant class for interacting with a live MS SQL Server database
class SQLAssistant(SQLGenerator):
    def __init__(self, connection_string):
        super().__init__()
        self.connection_string = connection_string
        # Connecting to SQL Server and creating a cursor to be used
        self.conn = pyodbc.connect(self.connection_string)
        self.cursor = self.conn.cursor()

    # This function fetches and formats
    # the database schema as a string (will have following info)
    # to be used by the LLM to answer accordingly
    def get_db_schema(self):
        schema = ""
        self.cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """)

        # Rows will be used to fetch all the records from the table.
        rows = self.cursor.fetchall()

        # The following for loop will be used to get the table names, column name and data type
        # of all the tables present in the DB. They will be stored in tables dict.
        tables = {}
        for table, column, dtype in rows:
            # if the table is not present, the schema will be created, else will be added to it
            if table not in tables:
                tables[table] = []
            tables[table].append(f"{column} ({dtype})")

        # As stated earlier, the schema will be passed as a string object, hence
        # the column and dtype will be concatenated here
        for table, columns in tables.items():
            schema += f"Table {table}:\n  " + ", ".join(columns) + "\n"
        return schema

    # This function will run the generated code using cursor
    def execute_sql(self, sql_query):
        try:
            # Run the query with cursor
            self.cursor.execute(sql_query)
            # Save the output cols from self.cursor.description
            columns = [column[0] for column in self.cursor.description]
            # Fetch all the rows that matched
            rows = self.cursor.fetchall()
            # Make a dict from it
            results = [dict(zip(columns, row)) for row in rows]
            # Return results
            return results
        except Exception as e:
            return {"error": str(e)}

    # This acts like the main function which will output the result.
    def run(self, question):
        try:
            # Firstly, all the above functions will be called
            schema = self.get_db_schema()
            sql_query = self.generate_sql_query(schema, question)
            results = self.execute_sql(sql_query)
            # The output, as mentioned earlier, for all the functions will be stored in a dict
            # The dict will have the generated query(for code) and results(for dataframe)
            return {
                "generated_sql": sql_query,
                "results": results
            }
        except Exception as e:
            return {"error": str(e)}

# JSONSQLAssistant class for generating SQL based on a provided JSON schema
class JSONSQLAssistant(SQLGenerator):
    def __init__(self, json_schema):
        super().__init__()
        self.json_schema = json_schema
    # This function will convert the schema into a string representation
    # which can be read by the LLM as input
    def format_schema(self):
        schema_str = ""
        for table, columns in self.json_schema.items():
            formatted_cols = [f"{col} ({dtype})" for col, dtype in columns.items()]
            schema_str += f"Table {table}:\n  " + ", ".join(formatted_cols) + "\n"
        return schema_str

    # Main function to return generated SQL query
    def run(self, question):
        try:
            schema_str = self.format_schema()
            sql_query = self.generate_sql_query(schema_str, question)
            return {
                "generated_sql": sql_query
            }
        except Exception as e:
            return {"error": str(e)}