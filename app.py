import streamlit as st
import pandas as pd
import openai
import json
from pydantic import BaseModel

# retrieve and validate API keys 
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
if not OPENAI_API_KEY:
    st.error("Please add your OpenAI API key to the Streamlit secrets.toml file.")
    st.stop()

openai.api_key = OPENAI_API_KEY
client = openai.OpenAI()

# constants
NUMBER_OF_MESSAGES_TO_DISPLAY = 20

# weeks = [
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

weeks = [
    "0: Introductie",
    "1: Pauzeer voor je reageert",
    "2: Let op verzadiging",
    "3: Duidelijkheid & consistentie",
    "4: Herken automatische gedachten",
    "5: Voel emoties volledig",
    "6: Oefen zelfcompassie",
    "7: Laat los",
    "8: Beweeg bewust"
]


intros = {}
practices = {}
system_prompts = {}

# read in all data
for i in weeks:
    # replace these lines with your real file paths
    with open(f'intros_eng/week_{i[0]}.txt', "r") as file:
        intros[i] = file.read()

    with open(f'practices_eng/week_{i[0]}.txt', "r") as file:
        practices[i] = file.read()

    with open(f'prompts/week_{i[0]}.txt', "r") as file:
        system_prompts[i] = file.read()


def initialize_session_state():
    """Initialize session state variables."""
    if "history" not in st.session_state:
        st.session_state.history = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    # Store the previously selected week so we can detect changes
    if "prev_week" not in st.session_state:
        st.session_state.prev_week = weeks[0]
    if "week" not in st.session_state:
        st.session_state.week = weeks[0]

def setup_side_bar():
    """Show the radio for selecting the current week. 
       If the user changed the selection, reset session state accordingly."""
    st.sidebar.image("imgs/logo_bitewise.png")

    selected_week = st.sidebar.radio("Wekelijkse opdracht", weeks, index=0, disabled=False)

    # If the user has switched to a new week
    if selected_week != st.session_state.prev_week:
        # 1) Reset the chat
        st.session_state.history = []
        st.session_state.conversation_history = []
        # 2) Update the system prompt in the next steps
        # (will happen automatically in the chat initialization function)
        # 3) Update the old week 
        st.session_state.prev_week = selected_week
    
    # Update the current week
    st.session_state.week = selected_week


def setup_main_page():
    # Set up the main page layout
    # 1) Title
    st.markdown(
        f"""
        <span style="font-size:30px; color:#FF6632; font-weight:bold;">
            {st.session_state.week[3:]}
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
    st.markdown(
        """
        <span style="font-size:30px; color:#FF6632; font-weight:bold;">
            AI Chat
        </span>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""<span style="color:#26293A;">{"Chat elke avond"}</span>""",
        unsafe_allow_html=True
    )

# ========= Chat Logic ========= #    

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

    chat_input = st.chat_input("Typ hier je bericht...") 
    #chat_input = st.chat_input("Type your message here...") 
    if chat_input:
        on_chat_submit(chat_input)

    # Display conversation
    for message in st.session_state.history[-20:]:
        role = message["role"]
        with st.chat_message(role):
            st.write(message["content"])

if __name__ == "__main__":
    main()

