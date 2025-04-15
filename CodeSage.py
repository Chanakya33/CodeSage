import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import re
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GEMINI")
if not api_key:
    st.error("GEMINI_API_KEY is not set in the .env file!")
    st.stop()

# Configure the generative AI model
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# App title and styling
st.set_page_config(
    page_title="AI Code Assistant",
    page_icon="💻",
    layout="wide",
)

# Custom CSS for dark blue theme
st.markdown("""
<style>
    .main {
        background-color: #0d1b2a;
        color: #e0e1dd;
    }
    .stTextInput, .stTextArea {
        background-color: #1b263b;
        color: #e0e1dd;
        border-radius: 10px;
    }
    .stButton>button {
        background-color: #415a77;
        color: #e0e1dd;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background-color: #778da9;
    }
    .chat-container {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .user-message {
        background-color: #1b263b;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .assistant-message {
        background-color: #415a77;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .code-block {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        margin-bottom: 10px;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
    }
    .delete-btn {
        color: #e0e1dd;
        background-color: transparent;
        border: none;
        cursor: pointer;
        float: right;
    }
    .delete-btn:hover {
        color: #ff6b6b;
    }
    .timestamp {
        font-size: 0.8em;
        color: #adb5bd;
        margin-top: 5px;
    }
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'messages' not in st.session_state:
    st.session_state.messages = []

# App title
st.markdown("<h1 style='text-align: center; color: #e0e1dd;'>AI Code Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #778da9;'>Ask me to generate code in any programming language</p>", unsafe_allow_html=True)

# Function to detect code in a response
def extract_code_blocks(text):
    # Regular expression to match markdown code blocks
    pattern = r"```([\w\+\#]*)?\n([\s\S]*?)\n```"
    
    # Find all code blocks
    matches = re.findall(pattern, text)
    
    if not matches:
        return [("", text)]  # No code blocks found
    
    result = []
    last_end = 0
    
    for match in re.finditer(pattern, text):
        # Add text before code block
        if match.start() > last_end:
            result.append(("", text[last_end:match.start()]))
        
        # Add code block with language
        language = match.group(1).strip() if match.group(1) else ""
        code = match.group(2)
        result.append((language, code))
        
        last_end = match.end()
    
    # Add any remaining text after the last code block
    if last_end < len(text):
        result.append(("", text[last_end:]))
    
    return result

# Function to delete a chat message
def delete_message(message_id):
    st.session_state.chat_history = [msg for msg in st.session_state.chat_history if msg['id'] != message_id]
    st.experimental_rerun()

# Function to generate code
def generate_code(prompt):
    try:
        # Enhance the prompt to encourage code generation
        enhanced_prompt = f"""
        You are an expert programmer. Generate clean, optimized, and working code for the following request:
        
        {prompt}
        
        Think step by step, then provide the complete and correct implementation.
        Put all code in proper markdown code blocks with appropriate language tags.
        Include helpful comments to explain complex parts.
        """
        
        response = model.generate_content(enhanced_prompt)
        return response.text
    except Exception as e:
        return f"Error generating code: {str(e)}"

# Display chat history
for message in st.session_state.chat_history:
    with st.container():
        if message['role'] == 'user':
            st.markdown(f"""
            <div class='chat-container'>
                <div class='header'>
                    <strong>You</strong>
                    <button class='delete-btn' onclick="delete_message('{message['id']}')">⋮</button>
                </div>
                <div class='user-message'>
                    {message['content']}
                    <div class='timestamp'>{message['timestamp']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='chat-container'>
                <div class='header'>
                    <strong>AI Assistant</strong>
                    <button class='delete-btn' onclick="delete_message('{message['id']}')">⋮</button>
                </div>
                <div class='assistant-message'>
            """, unsafe_allow_html=True)
            
            # Process and display content with code blocks
            content_blocks = extract_code_blocks(message['content'])
            for language, block in content_blocks:
                if language:  # This is a code block
                    st.code(block, language=language)
                else:  # This is regular text
                    st.markdown(block)
            
            st.markdown(f"""
                    <div class='timestamp'>{message['timestamp']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# User input
col1, col2 = st.columns([6, 1])
with col1:
    user_input = st.text_area("Ask me to generate code...", height=100, key="user_input")

with col2:
    st.write("")
    st.write("")
    if st.button("Send", key="send_button"):
        if user_input.strip():
            # Add user message to chat history
            message_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%I:%M %p · %d %b %Y")
            
            st.session_state.chat_history.append({
                'id': message_id,
                'role': 'user',
                'content': user_input,
                'timestamp': timestamp
            })
            
            # Generate AI response
            with st.spinner("Generating code..."):
                ai_response = generate_code(user_input)
            
            # Add AI response to chat history
            ai_message_id = str(uuid.uuid4())
            st.session_state.chat_history.append({
                'id': ai_message_id,
                'role': 'assistant',
                'content': ai_response,
                'timestamp': timestamp
            })
            
            # Clear the input area
            st.session_state.user_input = ""
            
            # Refresh the page to show new messages
            st.experimental_rerun()

# Add a clear button to delete all chat history
if st.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.experimental_rerun()

# Instructions for the .env file
st.sidebar.title("Setup Instructions")
st.sidebar.info(
    "To use this application, you need a Gemini API key.\n\n"
    "1. Create a `.env` file in the project root directory\n"
    "2. Add your API key as: `GEMINI_API_KEY=your_api_key_here`\n"
    "3. Create a `.gitignore` file and add `.env` to it to keep your key secure"
)

# Show example prompts
st.sidebar.title("Example Prompts")
st.sidebar.markdown("""
- "Create a Python function to find prime numbers"
- "Write HTML and CSS for a responsive navigation bar"
- "Generate a JavaScript function that calculates Fibonacci sequence"
- "Build a Flask API with a POST endpoint to accept JSON data"
- "Create a React component for a form with validation"
""")