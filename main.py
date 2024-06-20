import streamlit as st
import os
from st_pages import add_page_title, show_pages, Page, Section
from streamlit_oauth import OAuth2Component

add_page_title()

show_pages(
    [
        Page(path="main.py", name="Connect", icon="🤝"),
        Section(name="FHIR Features", icon="🔥️"),
        Page(path="pages/features/search.py", name="Search", icon="🔍"),
        Page(path="pages/features/observations.py", name="Observations", icon="👀"),
        Section(name="Demo Apps", icon="🚨️"),
        Page(path="pages/demos/plaquenil_calculator.py", name="Plaquenil Calculator", icon="🧮"),
        Page(path="pages/demos/creatine_clearance.py", name="Creatine Clearance", icon="📏"),
    ]
)

sign_in_options = [
    {'workspace_id': os.environ.get('SMARTWORKSPACEID'), 'name': 'SmartHealth IT', 'search_requirements': None},
]

AUTHORIZE_URL = 'https://app.meldrx.com/connect/authorize'
TOKEN_URL = 'https://app.meldrx.com/connect/token'
REFRESH_TOKEN_URL = 'https://app.meldrx.com/connect/token'
REVOKE_TOKEN_URL = 'https://app.meldrx.com/connect/revocation'
CLIENT_ID = os.environ.get('CLIENTID')
CLIENT_SECRET = os.environ.get('CLIENTSECRET')
SCOPE = 'openid profile patient/*.read'


oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL, REVOKE_TOKEN_URL)
for option in sign_in_options:
    workspace_id = option['workspace_id']
    result = oauth2.authorize_button(
        name=option['name'],
        redirect_uri=f'{os.environ.get("APPURL")}/component/streamlit_oauth.authorize_button',
        scope=SCOPE,
        extras_params={'aud': f'https://app.meldrx.com/api/fhir/{workspace_id}'},
        pkce='S256'
    )

    if result and 'token' in result:
        # If authorization successful, save token in session state
        st.session_state.token = result.get('token')
        st.session_state.workspace_id = workspace_id
        st.session_state.search_requirements = option['search_requirements']

if 'token' in st.session_state:
    token = st.session_state['token']
    st.text('token_response')
    st.json(token)

import openai
from llama_index.llms.openai import OpenAI
try:
  from llama_index import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader
except ImportError:
  from llama_index.core import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader

st.set_page_config(page_title="Chat with the Searching for Health", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
openai.api_key = os.environ.get("OPENAIKEY")
st.title("Chat with Searching for Health")
         
if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about Searching for Health or its contents!"}
    ]

@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing the Searching for Health book – hang tight! This should take 1-2 minutes."):
        reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
        docs = reader.load_data()
        # llm = OpenAI(model="gpt-3.5-turbo", temperature=0.5, system_prompt="You are an expert o$
        # index = VectorStoreIndex.from_documents(docs)
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-4o", temperature=0.5, system_prompt="You are an expert at helping patients trying to navigate their relationship with their doctor and their health system, to help them get what they need. You help patients understand how to use online research and medically sound resources to improve their health."))
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

index = load_data()

if "chat_engine" not in st.session_state.keys(): # Initialize the chat engine
        st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) # Add response to message history
