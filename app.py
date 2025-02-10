import streamlit as st
from openai import AzureOpenAI
import json
import requests
import os

# Load the JSON document content
def load_json_document(file_path):
    with open(file_path, "r") as file:
        document = json.load(file)
    return document

client = AzureOpenAI(
    azure_endpoint=os.getenv("ENDPOINT"),
    api_key=os.getenv("OPENAI_API_KEY"),
    api_version="2024-10-01-preview",
)

def generate_response(query, context):
    """
    Sends the query and the context to the OpenAI API to generate a response.
    """
    prompt = f"Given the following context, answer the question:\n\nContext: {context}\n\nQuestion: {query}\nAnswer:"
    
    response = client.chat.completions.create(
                model="gpt-4o",  # Replace with your model ID
                messages=[{
                    "role": "system",
                    "content": "You are a helpful assistant, who answers users' questions in a friendly manner.",
                },
                {"role": "user", "content": prompt}],
                temperature=0.0,
            )
    
    answer = response.choices[0].message.content.strip()
    return answer

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
    # # Display the assistant's answer in the chat
    # st.session_state.messages.append({"role": "assistant", "content": answer})

    # # Refresh the chat interface
    # st.rerun()
