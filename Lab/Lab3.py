import streamlit as st
from openai import OpenAI

st.title("MY Lab3 question answering chatbot")

if 'client' not in st.session_state:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.client = OpenAI(api_key=api_key)

if 'messages' not in st.session_state:
    st.session_state.messages = [{'role': 'assistant', 'content': 'How can I help you?'}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message('user'):
        st.markdown(prompt)

    buffer_messages = st.session_state.messages[-4:]
    client = st.session_state.client
    stream = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=buffer_messages,
        stream=True)

    with st.chat_message('assistant'):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})

