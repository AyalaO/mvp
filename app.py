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

    selected_week = st.sidebar.radio("Selecteer de week", weeks, index=0, disabled=False)

    # If the user has switched to a new week
    if selected_week != st.session_state.prev_week:
        # 1) Clear the stored intro so it will be re-generated
        if "week_intro_dict" in st.session_state:
            del st.session_state.week_intro_dict
        # 2) Reset the chat
        st.session_state.history = []
        st.session_state.conversation_history = []
        # 3) Update the system prompt in the next steps
        # (will happen automatically in the chat initialization function)
        # 4) Update the old week 
        st.session_state.prev_week = selected_week
    
    # Update the current week
    st.session_state.week = selected_week

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
    Make sure your output is in Dutch
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
                    {"role": "system", "content": get_week_intro_prompt()+'answer in Dutch'},
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
        #f"""<span style="color:#26293A; font-weight:bold;">How will this help me?</span>""",
        f"""<span style="color:#26293A; font-weight:bold;">Waarom helpt dit?</span>""",
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

    #with st.expander("**Show practice of the week**", expanded=False):
    with st.expander("**Toon opdracht van de week**", expanded=False):
        st.markdown(
            f"""<span style="color:#26293A;">{practices_display[st.session_state.week]}</span>""",
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
        f"""<span style="color:#26293A;">{week_intro_dict['encouragement_to_chat']}</span>""",
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

