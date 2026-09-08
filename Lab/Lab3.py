import streamlit as st
from openai import OpenAI
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-4o-mini")
token_based_buffer = 500
system_prompt = {'role': 'system', 'content': "Input a user's question and answer it. Then ask if they want to know more information. IF YES, give more information and AGAIN ask if they want more information. IF NO, ask what else you can help with. ALL OUTPUTS should be understandable by a 10 year old"}

st.title("MY Lab3 question answering chatbot")
st.markdown(f"Token buffer: {token_based_buffer}")

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

    #buffer_messages = st.session_state.messages[-4:]
    #^ used for message count conversation buffer

    buffer_messages = []
    total_tokens = 0

    for msg in reversed(st.session_state.messages):
        token_count = len(encoding.encode(msg['content']))
        if total_tokens + token_count < token_based_buffer:
            buffer_messages.append(msg)
            total_tokens = total_tokens + token_count
        else:
            break


    buffer_messages.reverse()
    passed_messages = []
    passed_messages.append(system_prompt)
    passed_messages.extend(buffer_messages)


    client = st.session_state.client
    stream = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=passed_messages,
        stream=True)

    with st.chat_message('assistant'):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})

