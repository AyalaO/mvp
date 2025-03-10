import streamlit as st
import pandas as pd
import openai
import json
from pydantic import BaseModel
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import uuid

# retrieve and validate API keys 
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
if not OPENAI_API_KEY:
    st.error("Please add your OpenAI API key to the Streamlit secrets.toml file.")
    st.stop()

openai.api_key = OPENAI_API_KEY
client = openai.OpenAI()

# constants
NUMBER_OF_MESSAGES_TO_DISPLAY = 20

# create a connection object for google sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# week_titles = [
#     "0: Preperations",
#     "1: Pause Before Reacting",
#     "2: Notice Your Fullness",
#     "3: Create Clarity and Consistency",
#     "4: Identify Automatic Thoughts",
#     "5: Feel Your Emotions Fully",
#     "6: Practice Self-Compassion",
#     "7: Letting Go",
#     "8: Move Mindfully"
# ]

week_titles = {
    "Introductie": "Introductie",
    "Week 1": "De kunst van even pauzeren",
    "Week 2": "Let op verzadiging",
    "Week 3": "Duidelijkheid & consistentie",
    "Week 4": "Herken automatische gedachten",
    "Week 5": "Voel emoties volledig",
    "Week 6": "Oefen zelfcompassie",
    "Week 7": "Laat los",
    "Week 8": "Beweeg bewust"
}

weeks = [
    "Introductie", 
    "Week 1", 
    # "Week 2", 
    # "Week 3", 
    # "Week 4", 
    # "Week 5", 
    # "Week 6", 
    # "Week 7", 
    # "Week 8", 
]


intros = {}
practices = {}
system_prompts = {}

# read in all data
for i in weeks:
    # replace these lines with your real file paths
    with open(f'intros_nl/week_{i[-1]}.txt', "r") as file:
        intros[i] = file.read()

    with open(f'practices_nl/week_{i[-1]}.txt', "r") as file:
        practices[i] = file.read()

    with open(f'prompts/week_{i[-1]}.txt', "r") as file:
        system_prompts[i] = file.read()


def initialize_session_state():
    """Initialize session state variables."""
    if "history" not in st.session_state:
        st.session_state.history = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    # store the previously selected week so we can detect changes
    if "prev_week" not in st.session_state:
        st.session_state.prev_week = weeks[0]
    if "week" not in st.session_state:
        st.session_state.week = weeks[0]
    # generate session id for tracking
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

def setup_side_bar():
    """Show the radio for selecting the current week. 
       If the user changed the selection, reset session state accordingly."""
    st.sidebar.image("imgs/logo_bitewise.png")

    selected_week = st.sidebar.radio("Kies een week", weeks, index=0, disabled=False)

    st.sidebar.markdown(
        f"""<span style="color:#FF6632;">{"Week 2 is beschikbaar vanaf 17 maart."}</span>""",
        unsafe_allow_html=True
    )

    # If the user has switched to a new week
    if selected_week != st.session_state.prev_week:
        # 1) Reset the chat
        st.session_state.history = []
        st.session_state.conversation_history = []
        # 2) Update the system prompt in the next steps
        # will happen automatically in the chat initialization function
        # 3) Update the old week 
        st.session_state.prev_week = selected_week
        # 4) Generate a new session_id so you can log new chat independently
        st.session_state.session_id = str(uuid.uuid4())
    
    # Update the current week
    st.session_state.week = selected_week


def setup_main_page():
    # Set up the main page layout
    # 1) Title
    st.markdown(
        f"""
        <span style="font-size:30px; color:#FF6632; font-weight:bold;">
            {week_titles[st.session_state.week]}
        </span>
        """,
        unsafe_allow_html=True
    )    
    st.write("")

    # 2) Hard coded week intro
    st.markdown(
        f"""<span style="color:#26293A;">{intros[st.session_state.week]}</span>""",
        unsafe_allow_html=True
    )
    
    if st.session_state.week != weeks[0]:
        # 2) Weekly exercise
        # CSS to style the expander
        st.markdown(
            """
            <style>
            [data-testid="stExpander"] {
                background-color: #FCEFD9 !important;
                border-radius: 10px !important;
                overflow: hidden !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        with st.expander("**Toon opdracht van de week**", expanded=False):
            st.markdown(
                f"""<span style="color:#26293A;">{practices[st.session_state.week]}</span>""",
                unsafe_allow_html=True
            )
        
        # Chat section

        chat_intro = """ 
                        Elke avond check je hier in bij de AI-chat – een paar minuten is genoeg! 🤖💬 
                        Reflecteer hoe het ging: vond je de opdracht nuttig, uitdagend, irritant of juist verhelderend? 
                        Alles is goed! Dit moment van reflectie helpt je om inzichten op te doen en bewuster met je proces bezig te zijn. 
                        Hoe vaker je dit doet, hoe meer je eruit haalt. Dus neem dat moment voor jezelf! 🚀✨
                         """
        st.markdown(
            """
            <span style="font-size:30px; color:#FF6632; font-weight:bold;">
                AI Chat
            </span>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""<span style="color:#26293A;">{chat_intro}</span>""",
            unsafe_allow_html=True
        )

# ========= Chat Logic ========= #    

@st.cache_data(show_spinner=False)
def log_conversation(latest_chat_state):
    # format logs
    latest_chat_state_clean = "  ".join(
                    interaction['role'] + ' : ' + interaction['content']
                    for interaction in latest_chat_state
                    )
    new_log_entry = [datetime.now().strftime("%Y/%m/%d %H:%M:%S"), 
                    st.session_state.session_id, 
                    st.session_state.week,
                    latest_chat_state_clean]
    print(new_log_entry)
    print(f'length new entry is {len(new_log_entry)}')
    # read in sheet
    df_logs = conn.read(worksheet="chat_logs", usecols=[0,1,2,3], ttl=0)
    index_session = df_logs.index[df_logs['session_id'] == st.session_state.session_id].tolist()
    if not index_session:
        # session not logged before yet, append logs on new row
        df_logs.loc[len(df_logs)] = new_log_entry
    else:
        # session already logged before, replace existing row
        df_logs.loc[index_session] = new_log_entry
    # write to sheet        
    conn.update(worksheet="chat_logs", data=df_logs)


def initialize_conversation(system_prompt):
    """Initialize the conversation history with system and assistant messages."""
    #assistant_message = "Ask me anything.." 
    assistant_message = "Waarmee kan ik je vandaag helpen?" 
    conversation_history = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": assistant_message}
    ]
    return conversation_history

@st.cache_data(show_spinner=False)
def on_chat_submit(chat_input):
    """Handle user chat submissions."""
    user_input = chat_input.strip()
    if not user_input:
        return

    if "conversation_history" not in st.session_state or not st.session_state.conversation_history:
        # System prompt from the new week
        system_prompt = system_prompts[st.session_state.week]
        st.session_state.conversation_history = initialize_conversation(system_prompt)

    # Add user message
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "user", "content": user_input})

    # Check final prompts
    print(st.session_state.conversation_history)

    # Send to OpenAI
    try:
        model_engine = "gpt-4o"
        response = client.chat.completions.create(
            model=model_engine,
            messages=st.session_state.conversation_history
        )
        assistant_reply = response.choices[0].message.content
        
        # Add assistant reply to conversation history
        st.session_state.conversation_history.append({"role": "assistant", "content": assistant_reply})
        st.session_state.history.append({"role": "assistant", "content": assistant_reply})

    except openai.error.OpenAIError as e:
        st.error(f"OpenAI Error: {str(e)}")


# ========= Main App ========= #

def main():
    # retrieve uid
    uid = st.query_params["uid"]
    initialize_session_state()
    setup_side_bar()
    setup_main_page()

    # If no history yet, create an initial bot message
    if not st.session_state.history:
        st.session_state.history.append({
            "role": "assistant", 
            #"content": "Ask me anything..."
            "content": "Waarmee kan ik je vandaag helpen.."
        })

    if st.session_state.week != weeks[0]:
        chat_input = st.chat_input("Typ hier je bericht...") 
        #chat_input = st.chat_input("Type your message here...") 
        if chat_input:
            on_chat_submit(chat_input)
            # log user chat activity
            user_worksheet = uid
            new_log_entry = [datetime.now().strftime("%Y/%m/%d %H:%M:%S"), 
                            st.session_state.session_id, 
                            f'user {uid} used chat']
            df_logs = conn.read(worksheet=user_worksheet, usecols=[0,1,2], ttl=0)
            df_logs.loc[len(df_logs)] = new_log_entry
            conn.update(worksheet=user_worksheet, data=df_logs)

        # Display conversation
        for message in st.session_state.history[-20:]:
            role = message["role"]
            with st.chat_message(role):
                st.write(message["content"])
        # Log conversations
        if len(st.session_state.history) > 1:
            log_conversation(st.session_state.history)
    
    # user activity logging
    user_worksheet = uid
    new_log_entry = [datetime.now().strftime("%Y/%m/%d %H:%M:%S"), 
                    st.session_state.session_id, 
                    f'user {uid} opened {st.session_state.week}']
    df_logs = conn.read(worksheet=user_worksheet, usecols=[0,1,2], ttl=0)
    df_logs.loc[len(df_logs)] = new_log_entry
    conn.update(worksheet=user_worksheet, data=df_logs)




if __name__ == "__main__":
    main()

