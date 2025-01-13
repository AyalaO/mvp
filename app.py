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

# set-up sidebar layout
st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #D8BFA3;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.image("imgs/logo_apple.png")

# st.sidebar.text_input("Your name", key="name")
st.sidebar.text_input("Your goal", key="goal")
st.sidebar.text_input("Your real why", key="why")

# # show dropdown menu with weeks
# week_drop = st.sidebar.selectbox(
#     'Which week are you in?', 
#     weeks)
# 'You are in week: ', week_drop

# add some spacing
st.sidebar.write('')

# show radio button per week
week = st.sidebar.radio('Which week are you in?', weeks)
latest_reply_for_week = 'initiate'

st.subheader(week[3:])

week_intro_prompt = f"""
You are a CBT and mindfulness coach helping users to lose weight. 
You are introducing the focus of week {week[0]}, which is {week}. 

The practice for the week is {practices[week]}.

Your task:
1. Provide a short, welcoming introduction to this week.
2. Briefly explain how this contributes to the user's goals.
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

Use markdown to layout the text
No other text or keys outside of this JSON object. Return exactly one valid JSON object and nothing else—no markdown, no extra text.
"""

class WeekIntro(BaseModel):
     intro_to_the_week: str
     why_does_this_matter_for_me: str
     encouragement_to_chat: str

if week != latest_reply_for_week:
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
            
            latest_reply_for_week = week 

    except openai.OpenAIError as e:
        logging.error(f"Error occurred: {e}")
        st.error(f"OpenAI Error: {str(e)}")

# show intro
week_intro_dict = json.loads(week_intro)
st.write(week_intro_dict['intro_to_the_week'])
st.write('**How will this help me?**')
st.write(week_intro_dict['why_does_this_matter_for_me'])
with st.expander("**Show practice of the week**", expanded=False, icon="🎯"):
    st.write(practices_display[week])
st.write(week_intro_dict['encouragement_to_chat'])