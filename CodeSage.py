import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import re
import uuid
from datetime import datetime
import sys

# Load environment variables
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GEMINI")
if not api_key:
    st.error("GEMINI_API_KEY is not set in the .env file!")
    st.stop()

# Configure the generative AI model
try:
    genai.configure(api_key=api_key)
    # Use the correct free model name - gemini-1.5-flash instead of gemini-pro
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error configuring Gemini API: {str(e)}")
    st.error("If you see a model not found error, you may need to check the available models.")
    st.info("For free tier, try using 'gemini-1.5-flash' instead of 'gemini-pro'")
    st.stop()

# App title and styling
st.set_page_config(
    page_title="CodeCraft AI",
    page_icon="🧩",
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

if 'input_key' not in st.session_state:
    st.session_state.input_key = str(uuid.uuid4())

# Function to reset the input field
def reset_input():
    st.session_state.input_key = str(uuid.uuid4())

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
    st.rerun()  # Updated to use st.rerun()

# Function to handle message submission
def handle_submit(user_input):
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
        try:
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
        except Exception as e:
            error_message = str(e)
            st.error(f"Error: {error_message}")
            
            # Add error message to chat history
            error_message_id = str(uuid.uuid4())
            st.session_state.chat_history.append({
                'id': error_message_id,
                'role': 'assistant',
                'content': f"Error generating code: {error_message}",
                'timestamp': timestamp
            })
        
        # Reset the input field by using a new key
        reset_input()
        
        # Updated to use st.rerun()
        st.rerun()

# Function to generate code
def generate_code(prompt):
    try:
        # Enhance the prompt to encourage code generation
        enhanced_prompt = f"""
        You are an elite-level programmer. Generate clean, optimized, and working code for the following request:
        
        {prompt}
        
        Think step by step, then provide the complete and correct implementation.
        Put all code in proper markdown code blocks with appropriate language tags.
        Include helpful comments to explain complex parts.
        """
        
        # Set proper generation parameters
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
        }
        
        # Use the safety settings appropriate for code generation
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        response = model.generate_content(
            enhanced_prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        return response.text
    except Exception as e:
        return f"Error generating code: {str(e)}"

# Function to list available models
def list_available_models():
    try:
        models = genai.list_models()
        model_names = [model.name for model in models]
        return model_names
    except Exception as e:
        return f"Error listing models: {str(e)}"

def main():
    # App title
    st.markdown("<h1 style='text-align: center; color: #e0e1dd;'>CodeCraft AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #778da9;'>Ask me to generate code in any programming language</p>", unsafe_allow_html=True)

    # Display chat history
    for idx, message in enumerate(st.session_state.chat_history):
        with st.container():
            if message['role'] == 'user':
                st.markdown(f"""
                <div class='chat-container'>
                    <div class='header'>
                        <strong>You</strong>
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
                        <strong>CodeCraft AI</strong>
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

    # User input form
    with st.form(key="message_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_area("Ask me to generate code...", height=100, key=st.session_state.input_key)
        with col2:
            st.write("")
            st.write("")
            submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input.strip():
            # Process outside the form to prevent immediate rerun issues
            st.session_state.current_input = user_input

    # Process the submitted input (if any)
    if 'current_input' in st.session_state and st.session_state.current_input:
        user_input = st.session_state.current_input
        st.session_state.current_input = None  # Clear it to prevent reprocessing
        handle_submit(user_input)

    # Add a clear button to delete all chat history
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()  # Updated to use st.rerun() only once

    # Show example prompts in the sidebar
    st.sidebar.title("Example Prompts")
    st.sidebar.markdown("""
    - "Create a Python function to find prime numbers"
    - "Write HTML and CSS for a responsive navigation bar"
    - "Generate a JavaScript function that calculates Fibonacci sequence"
    - "Build a Flask API with a POST endpoint to accept JSON data"
    - "Create a React component for a form with validation"
    """)

# Add this condition to ensure proper script execution
if __name__ == "__main__":
    main()