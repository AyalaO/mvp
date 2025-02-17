# my first app 
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

# assign OpenAI API Key
openai.api_key = OPENAI_API_KEY
client = openai.OpenAI()

# Constants
NUMBER_OF_MESSAGES_TO_DISPLAY = 20

# weeks, TODO place in seperate file
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

st.session_state.week = weeks[0]

# read in practices per week, full version 
practices = {}
for i in weeks:
    with open(f'practices/week_{i[0]}.txt', "r") as file:
        practices[i] = file.read()

# read in practices per week, display version
practices_display = {}
for i in weeks:
    with open(f'practices_display/week_{i[0]}.txt', "r") as file:
        practices_display[i] = file.read()
 
# read in prompt per week 
system_prompts = {}
for i in weeks:
    with open(f'prompts/week_{i[0]}.txt', "r") as file:
        system_prompts[i] = file.read()


week_intro_prompt = f"""
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

class WeekIntro(BaseModel):
     intro_to_the_week: str
     why_does_this_matter_for_me: str
     encouragement_to_chat: str

################## chat content
def initialize_conversation(system_prompt_week):
    """
    Initialize the conversation history with system and assistant messages.

    Returns:
    - list: Initialized conversation history.
    """
    assistant_message = "Hi, how is it going?" 
    system_prompt = system_prompt_week
    
    conversation_history = [
        {"role": "system", "content": system_prompt
        },
        {"role": "assistant", "content": assistant_message
         }
    ]
    return conversation_history

@st.cache_data(show_spinner=False)
def on_chat_submit(chat_input):
    """
    Handle chat input submissions and interact with the OpenAI API.

    Parameters:
    - chat_input (str): The chat input from the user.

    Returns:
    - None: Updates the chat history in Streamlit's session state.
    """
    user_input = chat_input.strip().lower()

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = initialize_conversation()
    
    # add user input to conversation history
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "user", "content": user_input})

    try:
        model_engine = "gpt-4o"
        assistant_reply = ""

        response = client.chat.completions.create(
            model=model_engine,
            messages=st.session_state.conversation_history
        )
        assistant_reply = response.choices[0].message.content
        
        # add assistant reply to conversation history
        st.session_state.conversation_history.append({"role": "assistant", "content": assistant_reply})
        st.session_state.history.append({"role": "assistant", "content": assistant_reply})

    except OpenAIError as e:
        logging.error(f"Error occurred: {e}")
        st.error(f"OpenAI Error: {str(e)}")

def initialize_session_state():
    """Initialize session state variables."""
    if "history" not in st.session_state:
        st.session_state.history = []
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = [] 


################## chat content

def setup_side_bar():
    # set-up side bar
    st.sidebar.image("imgs/logo_bitewise.png")
    # st.sidebar.text_input("Your goal", key="goal")
    # st.sidebar.text_input("Your real why", key="why")
    # add some spacing
    st.sidebar.write('')
    # show radio button per week
    st.session_state.week = st.sidebar.radio('Which week are you in?', weeks, disabled=False)

def setup_main_page():
    # set-up main page layout
    st.markdown(
        f"""
        <span style="font-size:30px; color:#59C4D6; font-weight:bold;">
            {st.session_state.week[3:]}
        </span>
        """,
        unsafe_allow_html=True
    )    

    try:
        model_engine = "gpt-4o"
        response = client.beta.chat.completions.parse(
            model=model_engine,
            messages=[
                {"role": "system", "content": week_intro_prompt},
                # {"role": "user", "content": f'My goal is to {st.session_state.goal}. Because I want to {st.session_state.why}'}
            ],
            response_format = WeekIntro
        )
        week_intro = response.choices[0].message.content
        week_intro_dict = json.loads(week_intro)

    except openai.OpenAIError as e:
        logging.error(f"Error occurred: {e}")
        st.error(f"OpenAI Error: {str(e)}")

    # show intro
    st.markdown(f"""<span style="color:#26293A;">
                {week_intro_dict['intro_to_the_week']}</span>""", unsafe_allow_html=True)
    st.write("")
    st.markdown(f"""<span style="color:#26293A; font-weight:bold;">
                How will this help me?</span>""", unsafe_allow_html=True)
    st.markdown(f"""<span style="color:#26293A;">
                {week_intro_dict['why_does_this_matter_for_me']}</span>""", unsafe_allow_html=True)

    # Inject CSS to modify the expander’s background color
    st.markdown(
        """
        <style>
        /* Target the entire container of the expander */
        [data-testid="stExpander"] {
            background-color: #59C4D6 !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.expander("**Show practice of the week**", expanded=False, icon="🧡"):
        st.markdown(f"""<span style="color:#26293A;">
                {practices_display[st.session_state.week]}</span>""", unsafe_allow_html=True)

    st.markdown(f"""<span style="color:#26293A;">
                {week_intro_dict['encouragement_to_chat']}</span>""", unsafe_allow_html=True)

def main():
    """
    Handle the chat interface.
    """
    # Insert custom CSS for glowing effect
    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #7ed957,
                0 0 10px #7ed957,
                0 0 15px #7ed957,
                0 0 20px #7ed957,
                0 0 25px #7ed957,
                0 0 30px #7ed957,
                0 0 35px #7ed957;
            position: relative;
            z-index: -1;
            border-radius: 45px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    initialize_session_state()
    setup_side_bar()
    setup_main_page()

    if not st.session_state.history:
        initial_bot_message = "Ask me anything..."
        st.session_state.history.append({"role": "assistant", "content": initial_bot_message})
        st.session_state.conversation_history = initialize_conversation(st.session_state.week)
    
    chat_input = st.chat_input("...")
    if chat_input:
        on_chat_submit(chat_input)


    with st.expander("**Chat**", expanded=False, icon="🧡"):
        for message in st.session_state.history[-NUMBER_OF_MESSAGES_TO_DISPLAY:]:
            role = message["role"]
            avatar_image = "imgs/avatar_bitewise.png" if role == "assistant" else "imgs/profile-user.png" if role == "user" else None
            with st.chat_message(role, avatar=avatar_image):
                st.write(message["content"])
        else:
            print("Error in chat printing")
        
    

if __name__ == "__main__":
    main()