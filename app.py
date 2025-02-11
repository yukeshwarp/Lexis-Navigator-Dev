import streamlit as st
from openai import AzureOpenAI
import json
import requests
import os
import hashlib

# Load the JSON document content
def load_json_document(file_path):
    with open(file_path, "r") as file:
        document = json.load(file)
    return document

# Azure OpenAI Client
client = AzureOpenAI(
    azure_endpoint="https://llmtech-eus2.openai.azure.com",
    api_key="fd87c22896654bc09830988577f2d7b5",
    api_version="2024-10-01-preview",
)

# Bing Search API configuration
BING_SEARCH_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"
BING_API_KEY = "afc632c209584311956e12239969f498"

def search_bing(query):
    try:
        """
        Function to search the web using Azure Bing Search API when the user requests it.
        """
        headers = {
            "Ocp-Apim-Subscription-Key": BING_API_KEY
        }

        params = {
            "q": query,
            "textDecorations": True,
            "textFormat": "HTML",
        }

        response = requests.get(BING_SEARCH_ENDPOINT, headers=headers, params=params)
        if response.status_code == 200:
            search_results = response.json()
            # Extract top search result titles and URLs
            if 'webPages' in search_results:
                results = search_results['webPages']['value']
                top_result = results[0]
                return f"Here is a top result I found: {top_result['name']} - {top_result['url']}"
            else:
                return "Sorry, I couldn't find any relevant search results."
        else:
            return f"Error during search: {response.status_code}"
    except Exception as e:
        print(e)
        return f"Error: {str(e)}"

# Set up the Streamlit app
st.title("Lexis Navigator")
st.write("Ask your query to navigate through Lexis tools.")

# Load the standard document content (Assume it is stored in JSON)
document = load_json_document("output.json")  # Update with the path to your JSON document
context = json.dumps(document)  # Convert document to JSON string to pass as context

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").markdown(message["content"])  # Use .text() here instead of .content()
    else:
        st.chat_message("assistant").markdown(message["content"])  # Use .text() here instead of .content()

# Implement streaming input
if prompt := st.chat_input("Ask your question here..."):
    # Display the user's question in the chat
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        inline_prompt = f"Given the following context, answer the question:\n\nContext: {context}\n\nQuestion: {prompt}\nAnswer:"

        try:
            response_stream = client.chat.completions.create(
                        model="gpt-4o",  # Replace with your model ID
                        messages=[{
                            "role": "system",
                            "content": "You are a helpful assistant, who answers users' questions in a friendly manner.",
                        },
                        {"role": "user", "content": inline_prompt}],
                        temperature=0.0,
                        stream=True,
                    )
            
            bot_response = ""
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                for chunk in response_stream:
                    if chunk.choices:
                        bot_response += chunk.choices[0].delta.content or ""
                        response_placeholder.markdown(bot_response)

            st.session_state.messages.append({"role": "assistant", "content": bot_response})

            # Perform Bing Search and ground the response with search results
            search_result = search_bing(prompt)

            # Modify the assistant's response to include search results
            grounded_response = f"{bot_response}\n\nAdditionally, I found the following relevant information from the web:\n{search_result}"

            st.session_state.messages.append({"role": "assistant", "content": grounded_response})

        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})

    # Display messages with an additional search button for the last entered user prompt
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.chat_message("user").markdown(message["content"])  # Use .text() here instead of .content()
        else:
            st.chat_message("assistant").markdown(message["content"])  # Use .text() here instead of .content()

        if message["role"] == "assistant":
            # Use the most recent user input as the key for the "Search more on the web" button
            if prompt:  # Ensure prompt is not empty
                search_button_key = hashlib.md5(prompt.encode()).hexdigest()
                if st.button("Search more on the web", key=search_button_key):  # Use the last user input as the key
                    search_result = search_bing(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": search_result})
                    st.rerun()
