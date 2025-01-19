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

# weeks, TODO place in seperate file
weeks = [
    "1: Pause Before Reacting",
    "2: Notice Your Fullness",
    "3: Create Clarity and Consistency",
    "4: Identify Automatic Thoughts",
    "5: Feel Your Emotions Fully",
    "6: Practice Self-Compassion",
    "7: Letting Go",
    "8: Move Mindfully"
]

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

st.sidebar.image("imgs/logo_bitewise.png")
st.sidebar.text_input("Your goal", key="goal")
st.sidebar.text_input("Your real why", key="why")
# add some spacing
st.sidebar.write('')
# show radio button per week
week = st.sidebar.radio('Which week are you in?', weeks)
latest_reply_for_week = 'initiate'


# set-up main page layout
st.markdown(
    f"""
    <span style="font-size:30px; color:#44D07A; font-weight:bold;">
        {week[3:]}
    </span>
    """,
    unsafe_allow_html=True
)

week_intro_prompt = f"""
You are a CBT and mindfulness coach helping users to lose weight. 
You are introducing the focus of week {week[0]}, which is {week}. 

The practice for the week is {practices[week]}.

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

try:
    model_engine = "gpt-4o"
    response = client.beta.chat.completions.parse(
        model=model_engine,
        messages=[
            {"role": "system", "content": week_intro_prompt},
            {"role": "user", "content": f'My goal is to {st.session_state.goal}. Because I want to {st.session_state.why}'}
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
        background-color: #44D07A !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }

    /* Target the header text inside the expander */
    [data-testid="stExpander"] .streamlit-expanderHeader {
        color: #26293A !important;
        font-weight: bold; 
    }

    /* Target the content area inside the expander */
    [data-testid="stExpander"] .streamlit-expanderContent {
        background-color: #fff !important;  /* Example: white content area */
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.expander("**Show practice of the week**", expanded=False, icon="💚"):
    st.markdown(f"""<span style="color:#26293A;">
            {practices_display[week]}</span>""", unsafe_allow_html=True)

st.markdown(f"""<span style="color:#26293A;">
            {week_intro_dict['encouragement_to_chat']}</span>""", unsafe_allow_html=True)

