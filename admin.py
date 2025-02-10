import streamlit as st
import os
import json
import fitz  # PyMuPDF
from openai import AzureOpenAI

# Setup OpenAI Client
client = AzureOpenAI(
    azure_endpoint=os.getenv("ENDPOINT"),
    api_key=os.getenv("OPENAI_API_KEY"),
    api_version="2024-10-01-preview",
)

# Function to extract details using OpenAI
def extract_details(chunk):
    messages = [
        {
            "role": "system",
            "content": "You are a data extraction specialist proficient in extracting tables and data in them.",
        },
        {
            "role": "user",
            "content": f"""
            Document chunk to extract from: 
            {chunk}

            Output format:
            Array of dictionaries in JSON format with the following key and value format:
                "legal_task": "type = string",
                "product": "type = string",
                "where_feature": "type = string",
                "link": "type = string",
                "benefit_statement": "type = string"
            """,
        },
    ]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "extract_trademark_details",
                "description": "Extracts trademark details from a provided document chunk.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "legal_task": {"type": "string"},
                        "product": {"type": "string"},
                        "where_feature": {"type": "string"},
                        "link": {"type": "string"},
                        "benefit_statement": {"type": "string"},
                    },
                    "required": [
                        "legal_task", 
                        "product",
                        "where_feature",
                        "link",
                        "benefit_statement",
                    ],
                    "additionalProperties": False,
                },
            },
        }
    ]
    
    # Call the OpenAI API using function calling
    response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                temperature=0.0,
            )
    
    # Extract and return the response details
    return response.choices[0].message.tool_calls


# Streamlit UI Setup
st.title("Lexis Navigator Admin")
st.write("Upload a PDF document to update Lexis database.")

# File Upload
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

if pdf_file:
    # Open and read the uploaded PDF
    with fitz.open(pdf_file) as doc:
        jsondoc = []

        # Extract text and process each page
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()

            # Simulate extracting details using OpenAI (pass the chunk of text)
            extraction_results = extract_details(text)

            for result in extraction_results:
                extracted_data = json.loads(result.function.arguments)  # Convert JSON string to dictionary
                jsondoc.append(extracted_data)

        # Show the extracted details in a structured format
        st.write("### Extracted Details:")
        if jsondoc:
            st.json(jsondoc)  # Display extracted data as JSON

        # Provide the option to download the extracted data as a JSON file
        output_file = "output.json"
        with open(output_file, "w") as json_file:
            json.dump(jsondoc, json_file, indent=4)

        # Create download button
        with open(output_file, "r") as json_file:
            st.download_button(
                label="Download Extracted Data as JSON",
                data=json_file,
                file_name=output_file,
                mime="application/json",
            )
else:
    st.write("Please upload a PDF file to start the extraction.")
    st.warning("Database updation may take about 10 minutes to complete.")
