import streamlit as st
from openai import OpenAI
import tiktoken
import sys
import chromadb
from pathlib import Path
from pypdf import PdfReader

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

if 'open_ai_client' not in st.session_state:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.open_ai_client = OpenAI(api_key=api_key)

def add_to_collection(collection, text, file_name):
    client = st.session_state.open_ai_client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small'
    )

    embedding = response.data[0].embedding

    collection.add(
        documents=[text],
        ids=[file_name],
        embeddings=[embedding]
    )

def extract_text_from_pdf(pdf_path):
    pdf_reader = PdfReader(pdf_path)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def load_pdfs_to_collection(folder_path, collection):
    pdf_folder = Path(folder_path)
    for pdf_file in pdf_folder.glob("*.pdf"):
        text = extract_text_from_pdf(pdf_file)
        add_to_collection(collection, text, pdf_file.name)

@st.cache_resource #this debug was from claude and the following function
def get_chroma_collection():
    db_path = str(Path(__file__).parent / 'ChromaDB_for_Lab')
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(name='Lab4Collection')
    if collection.count() == 0:
        load_pdfs_to_collection('./Lab-04-Data/', collection)
    return collection

collection = get_chroma_collection()

encoding = tiktoken.encoding_for_model("gpt-4o-mini")
token_based_buffer = 500
system_prompt = {'role': 'system', 'content': "Input a user's question and answer it. Then ask if they want to know more information. IF YES, give more information and AGAIN ask if they want more information. IF NO, ask what else you can help with. ALL OUTPUTS should be understandable by a 10 year old. You MUST end every single response with a new line reading exactly: 'Source(s): ' followed by a comma-separated list of the exact document filenames you used from the provided context. If you did not use any retrieved documents to answer, write 'Source(s): none'."}
st.title("Lab4: Chatbot using RAG")
st.markdown(f"Token buffer: {token_based_buffer}")

#topic = st.sidebar.text_input('Topic', placeholder='Type your topic (e.g., GenAI)...')

#if topic:
    #client = st.session_state.open_ai_client
    #response = client.embeddings.create(
     #   input=topic,
      #  model='text-embedding-3-small'
    #)

    #query_embedding = response.data[0].embedding

    #results = collection.query(
     #   query_embeddings = [query_embedding],
      #  n_results = 3
    #)

    #st.subheader(f'Results for: {topic}')

    #for i in range(len(results['documents'][0])):
     #   doc = results['documents'][0][i]
      #  doc_id = results['ids'][0][i]

       # st.write(f'**{i+1}. {doc_id}**')
#else:
 #   st.info('Enter a topic in the sidebar to seach the collection')

if 'messages' not in st.session_state:
    st.session_state.messages = [{'role': 'assistant', 'content': 'How can I help you?'}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("What is up?"):
    with st.chat_message('user'):
            st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    client = st.session_state.open_ai_client
    response = client.embeddings.create(
       input=prompt,
       model='text-embedding-3-small'
    )

    query_embedding = response.data[0].embedding

    results = collection.query(
        query_embeddings = [query_embedding],
        n_results = 3
    )


    relevant_doc = ''
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        doc_id = results['ids'][0][i]
        relevant_doc += f"{doc_id}: {doc} \n"

    dynamic_system_prompt = {'role': 'system', 'content': system_prompt['content'] + "\n The following text is your RAG context, make sure to cite it clearly if you use it: At the end of every response, add a line formatted exactly as: Source(s): <filename1>, <filename2> listing only the documents you actually used. \n" + relevant_doc}


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
    passed_messages.append(dynamic_system_prompt)
    passed_messages.extend(buffer_messages)

    stream = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=passed_messages,
        stream=True)

    with st.chat_message('assistant'):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})

