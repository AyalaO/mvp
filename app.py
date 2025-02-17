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

weeks = [
    "0: Preperations",
    "1: Pause Before Reacting",
    "2: Notice Your Fullness",
    "3: Create Clarity and Consistency",
    "4: Identify Automatic Thoughts",
    "5: Feel Your Emotions Fully",
    "6: Practice Self-Compassion",
    "7: Letting Go",
    "8: Move Mindfully"
]

practices = {}
practices_display = {}
system_prompts = {}

# read in all data
for i in weeks:
    # replace these lines with your real file paths
    with open(f'practices/week_{i[0]}.txt', "r") as file:
        practices[i] = file.read()

    with open(f'practices_display/week_{i[0]}.txt', "r") as file:
        practices_display[i] = file.read()

    with open(f'prompts/week_{i[0]}.txt', "r") as file:
        system_prompts[i] = file.read()

# Pydantic model for the JSON response
class WeekIntro(BaseModel):
     intro_to_the_week: str
     why_does_this_matter_for_me: str
     encouragement_to_chat: str

def initialize_session_state():
    """Initialize session state variables."""
    if "history" not in st.session_state:
        st.session_state.history = []
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    # Ensure we have a default week
    if "week" not in st.session_state:
        st.session_state.week = weeks[0]

def setup_side_bar():
    st.sidebar.image("imgs/logo_bitewise.png")
    # Example: make the week read-only in the sidebar:
    st.session_state.week = st.sidebar.radio('Which week are you in?', weeks, disabled=True)

def get_week_intro_prompt():
    """Return the system prompt for the current week."""
    return f"""
    You are a CBT and mindfulness coach helping users to lose weight. 
    You are introducing the focus of week {st.session_state.week[0]}, which is {st.session_state.week}. 

    The practice for the week is {practices[st.session_state.week]}.

    Your task:
    1. Provide a short, welcoming introduction to this week.
    2. Concisely explain how the upcoming week's activities will help the user progress toward their goals. 
    4. Offer encouragement to reach out during challenges or for insights.

    Tone:
    - Encouraging, honest and a bit edgy, like a supportive friend
    - Concise
    - Include a few emojis

    Output format:
    Return exactly one valid JSON object with the following 3 keys:
    - "intro_to_the_week"
    - "why_does_this_matter_for_me"
    - "encouragement_to_chat"

    No other text or keys outside of this JSON object. Return exactly one valid JSON object and nothing else—no markdown, no extra text.
    """

def get_week_intro():
    """
    Make the OpenAI API call *once* and cache it in session_state.
    If it's already there, do not call again.
    """
    if "week_intro_dict" not in st.session_state:
        try:
            model_engine = "gpt-4o"
            response = client.beta.chat.completions.parse(
                model=model_engine,
                messages=[ 
                    {"role": "system", "content": get_week_intro_prompt()},
                ],
                response_format=WeekIntro
            )
            # The response content should already be valid JSON from pydantic parsing
            week_intro_obj = response.choices[0].message.content
            # Convert to dictionary if it comes as a string
            if isinstance(week_intro_obj, str):
                week_intro_obj = json.loads(week_intro_obj)
            st.session_state.week_intro_dict = week_intro_obj
        except openai.OpenAIError as e:
            st.error(f"OpenAI Error: {str(e)}")
            st.session_state.week_intro_dict = {
                "intro_to_the_week": "",
                "why_does_this_matter_for_me": "",
                "encouragement_to_chat": "",
            }
    return st.session_state.week_intro_dict

def setup_main_page():
    # Set up the main page layout
    st.markdown(
        f"""
        <span style="font-size:30px; color:#FF6632; font-weight:bold;">
            {st.session_state.week[3:]}
        </span>
        """,
        unsafe_allow_html=True
    )    
    
    # Get (and possibly generate) the week intro *once*
    week_intro_dict = get_week_intro()

    st.markdown(
        f"""<span style="color:#26293A;">{week_intro_dict['intro_to_the_week']}</span>""",
        unsafe_allow_html=True
    )
    st.write("")
    st.markdown(
        f"""<span style="color:#26293A; font-weight:bold;">How will this help me?</span>""",
        unsafe_allow_html=True
    )
    st.markdown(
        f"""<span style="color:#26293A;">{week_intro_dict['why_does_this_matter_for_me']}</span>""",
        unsafe_allow_html=True
    )

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

    with st.expander("**Show practice of the week**", expanded=False, icon="🧡"):
        st.markdown(
            f"""<span style="color:#26293A;">{practices_display[st.session_state.week]}</span>""",
            unsafe_allow_html=True
        )
    
    st.markdown(
        """
        <span style="font-size:30px; color:#FF6632; font-weight:bold;">
            AI Chat
        </span>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""<span style="color:#26293A;">{week_intro_dict['encouragement_to_chat']}</span>""",
        unsafe_allow_html=True
    )

def initialize_conversation(system_prompt):
    """Initialize the conversation history with system and assistant messages."""
    assistant_message = "Ask me anything.." 
    conversation_history = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": assistant_message}
    ]
    return conversation_history

@st.cache_data(show_spinner=False)
def on_chat_submit(chat_input):
    """
    Handle chat input submissions and interact with the OpenAI API.
    """
    user_input = chat_input.strip().lower()

    if 'conversation_history' not in st.session_state:
        # The system prompt for the chat can be different from the intro prompt.
        st.session_state.conversation_history = initialize_conversation(
            system_prompts[st.session_state.week]
        )
    
    # Add user input
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "user", "content": user_input})

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

# main app flow
initialize_session_state()
setup_side_bar()
setup_main_page()

# If no previous conversation, add initial message
if not st.session_state.history:
    initial_bot_message = "Ask me anything..."
    st.session_state.history.append({"role": "assistant", "content": initial_bot_message})
    # use the system prompt for the chat
    st.session_state.conversation_history = initialize_conversation(
        system_prompts[st.session_state.week]
    )

chat_input = st.chat_input("...")
if chat_input:
    on_chat_submit(chat_input)

# Display conversation
for message in st.session_state.history[-NUMBER_OF_MESSAGES_TO_DISPLAY:]:
    role = message["role"]
    avatar_image = (
        "imgs/avatar_bitewise.png" if role == "assistant" else 
        "imgs/profile-user.png" if role == "user" else 
        None
    )
    with st.chat_message(role, avatar=avatar_image):
        st.write(message["content"])
