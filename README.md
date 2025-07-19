# Gemini SQL Assistant

Gemini SQL Assistant is a Streamlit-based intelligent SQL query generator designed for Microsoft SQL Server. Powered by the Gemini 2.5 Flash model, this tool allows users to ask natural language questions and receive accurate SQL queries in return. It supports both local databases and dynamic schemas provided in JSON format.

## Features

- Ask questions in plain English and get valid SQL Server queries instantly
- Two modes of operation:
  - **Local DBs**: Select from available SQL Server databases on your machine
  - **JSON Schema**: Paste a custom schema in JSON format to generate queries for any dataset
- Smart handling of SQL Server syntax (e.g., converts `LIMIT` to `SELECT TOP`)
- Displays the generated query and the result set
- Streamlit-based interface for easy interaction
- Gemini 2.5 Flash integration for fast and accurate results

## How It Works

1. Select your mode: Local database or JSON schema
2. Provide a question in natural language
3. Gemini analyzes your question and schema to generate a valid SQL query
4. The query is executed, and results are shown (if using a local database).