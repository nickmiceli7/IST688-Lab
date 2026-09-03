import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

def read_pdf(file):
    reader = PdfReader(file)
    string = ""
    for page in reader.pages:
        string += page.extract_text()
    return string

# Show title and description.
st.title("MY Document question answering")
st.write(
    "Upload a pdf below and determine how you want it summarized – GPT will answer! "
)

# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.secrets.OPENAI_API_KEY

# Create an OpenAI client.
client = OpenAI(api_key=openai_api_key)

language = st.sidebar.selectbox('Select language:', [
    'English',
    'Spanish',
    'French'
])

choice = st.sidebar.selectbox('Select one:', [
    'Summarize the document in 100 words',
    'Summarize the document in 2 paragraphs',
    'Summarize the document in 5 bullet points'
])

check = st.sidebar.checkbox('Use advanced model')

if check:
    model='gpt-5-mini'
else:
    model='gpt-5-nano'

# Let the user upload a file via `st.file_uploader`.
uploaded_file = st.file_uploader(
    "Upload a document (.pdf)", type=("pdf")
)

if uploaded_file:

    # Process the uploaded file and question.
    document = read_pdf(uploaded_file)
    messages = [
        {
            "role": "system",
            "content": f"{choice}, in {language}"
        },
        {
            "role": "user",
            "content": f"Summarize this document: {document}"
        }
    ]

    # Generate an answer using the OpenAI API.
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    # Stream the response to the app using `st.write_stream`.
    st.write_stream(stream)