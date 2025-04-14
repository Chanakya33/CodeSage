import streamlit as st
import google.generativeai as genai
import os
import json
import uuid
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import requests

# Set page configuration
st.set_page_config(
    page_title="CodeSage | AI Code Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to load Lottie animation
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Define custom CSS for Navy Blue theme
st.markdown("""
<style>
    :root {
        --navy-dark: #0A192F;
        --navy: #112240;
        --navy-light: #233554;
        --accent: #64FFDA;
        --text-primary: #CCD6F6;
        --text-secondary: #8892B0;
    }
    
    .stApp {
        background-color: var(--navy-dark);
        color: var(--text-primary);
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    
    .stButton button {
        background-color: transparent;
        color: var(--accent);
        border: 1px solid var(--accent);
        border-radius: 4px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: rgba(100, 255, 218, 0.1);
        box-shadow: 0 0 10px rgba(100, 255, 218, 0.3);
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    
    .user-message {
        background-color: var(--navy-light);
        border-left: 4px solid var(--accent);
    }
    
    .assistant-message {
        background-color: var(--navy);
        border-left: 4px solid #6c74dc;
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        color: var(--text-secondary);
        font-size: 0.8rem;
    }
    
    .message-content {
        color: var(--text-primary);
    }
    
    code {
        border-radius: 4px !important;
    }
    
    .css-1kyxreq {
        justify-content: center;
    }
    
    .sidebar-content {
        background-color: var(--navy);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-163ttbj, .css-1fcdlhc {
        background-color: var(--navy);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--navy-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--navy-light);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }
    
    /* Code block styling */
    pre {
        background-color: #1E2D3D !important;
        padding: 1rem !important;
        border-radius: 5px !important;
        overflow-x: auto !important;
        margin-bottom: 1rem !important;
    }
    
    /* Dropdown styling */
    .stSelectbox label, .stTextInput label {
        color: var(--text-primary) !important;
    }
    
    .stTextInput input {
        background-color: var(--navy) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--navy-light) !important;
    }
    
    /* New conversation button styling */
    .new-chat-button {
        width: 100%;
        background-color: var(--navy-light);
        color: var(--accent);
        border: 1px solid var(--accent);
        border-radius: 4px;
        padding: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .new-chat-button:hover {
        background-color: rgba(100, 255, 218, 0.1);
    }
    
    /* Chat history buttons */
    .chat-history-button {
        width: 100%;
        background-color: var(--navy-dark);
        color: var(--text-secondary);
        border: none;
        border-radius: 4px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        text-align: left;
        cursor: pointer;
        transition: all 0.3s ease;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .chat-history-button:hover {
        background-color: var(--navy-light);
        color: var(--text-primary);
    }
    
    .chat-history-button.active {
        background-color: var(--navy-light);
        color: var(--accent);
        border-left: 2px solid var(--accent);
    }
    
    /* Loading animation */
    .loading-animation {
        display: flex;
        justify-content: center;
        padding: 2rem;
    }
    
    /* Code copy button */
    .copy-button {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background-color: var(--navy-light);
        color: var(--text-secondary);
        border: none;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        font-size: 0.8rem;
        cursor: pointer;
        z-index: 100;
    }
    
    .copy-button:hover {
        background-color: var(--navy);
        color: var(--accent);
    }
    
    .language-tag {
        display: inline-block;
        background-color: rgba(100, 255, 218, 0.1);
        color: var(--accent);
        border-radius: 4px;
        padding: 0.15rem 0.5rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    
    /* Time tag */
    .time-tag {
        color: var(--text-secondary);
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}

if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())

if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Define supported languages
SUPPORTED_LANGUAGES = ["HTML", "CSS", "JavaScript", "Python", "SQL"]

# Functions for chat management
def create_new_chat():
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.chat_history[st.session_state.current_chat_id] = {
        "title": "New Conversation",
        "messages": [],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def load_chat(chat_id):
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = st.session_state.chat_history[chat_id]["messages"]

def update_chat_title(chat_id, messages):
    if len(messages) >= 2:  # If there's at least one exchange
        user_message = messages[0]["content"] if messages[0]["role"] == "user" else ""
        title = user_message[:30] + "..." if len(user_message) > 30 else user_message
        st.session_state.chat_history[chat_id]["title"] = title

def save_message(chat_id, role, content):
    message = {"role": role, "content": content, "timestamp": datetime.now().strftime("%H:%M")}
    st.session_state.messages.append(message)
    
    # Update in chat history
    if chat_id not in st.session_state.chat_history:
        st.session_state.chat_history[chat_id] = {
            "title": "New Conversation",
            "messages": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    st.session_state.chat_history[chat_id]["messages"] = st.session_state.messages
    update_chat_title(chat_id, st.session_state.messages)

def check_language_support(query):
    unsupported_languages = ["Java", "C++", "C#", "Ruby", "Swift", "Kotlin", "Go", "PHP", "Rust", "TypeScript"]
    for lang in unsupported_languages:
        if f"in {lang}" in query or f"using {lang}" in query or f"write {lang}" in query or f"{lang} code" in query:
            return False, lang
    return True, None

def generate_response(api_key, messages):
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Select the model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Build the conversation
        system_prompt = """You are CodeSage, an expert AI code assistant specialized in generating high-quality code in HTML, CSS, JavaScript, Python, and SQL only.
        
        Guidelines:
        1. Focus ONLY on HTML, CSS, JavaScript, Python, and SQL code generation.
        2. Refuse any requests for other programming languages politely.
        3. Do not perform general web searches or create content unrelated to code generation.
        4. When generating code, include helpful comments and explanations.
        5. Follow best practices and modern conventions for each language.
        6. Always wrap code in proper markdown code blocks with language specification.
        7. Optimize code for readability and efficiency.
        8. Provide brief explanations of how the code works after generating it.
        
        When users ask questions about code or programming concepts, respond with clear, accurate explanations and examples.
        """
        
        # Create the conversation format that Gemini expects
        chat = model.start_chat(history=[])
        
        # Add system prompt as first message
        prompt_parts = [system_prompt]
        
        # Add conversation history
        for msg in messages:
            if msg["role"] == "user":
                prompt_parts.append(f"User: {msg['content']}")
            else:
                prompt_parts.append(f"Assistant: {msg['content']}")
        
        # Generate response
        response = chat.send_message(prompt_parts)
        
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Sidebar
with st.sidebar:
    st.title("🧠 CodeSage")
    st.markdown("*Your expert AI coding companion*")
    
    # Lottie Animation
    lottie_coding = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_qp1q7mct.json")
    if lottie_coding:
        st_lottie(lottie_coding, speed=1, height=180, key="coding")
    
    # API Key input
    with st.expander("🔑 API Settings", expanded=False):
        api_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.gemini_api_key,
            type="password",
            help="Enter your Gemini API key to use the service"
        )
        if api_key:
            st.session_state.gemini_api_key = api_key
    
    # New chat button
    st.markdown("""
    <div class="new-chat-button" id="new-chat-button">
        + New Conversation
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("+ New Conversation", key="new_chat"):
        create_new_chat()
    
    # Chat history
    st.markdown("### 📝 Chat History")
    
    if not st.session_state.chat_history:
        st.info("No conversation history yet.")
    else:
        # Sort chats by timestamp (newest first)
        sorted_chats = sorted(
            st.session_state.chat_history.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True
        )
        
        for chat_id, chat_data in sorted_chats:
            # Format the button with conditional styling for active chat
            active_class = "active" if chat_id == st.session_state.current_chat_id else ""
            if st.button(f"{chat_data['title']}", key=f"history_{chat_id}", 
                        help=f"Created: {chat_data['timestamp']}"):
                load_chat(chat_id)
    
    # Supported languages
    st.markdown("### 💻 Supported Languages")
    for lang in SUPPORTED_LANGUAGES:
        st.markdown(f"""<span class="language-tag">{lang}</span>""", unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("© 2025 CodeSage AI")

# Main chat interface
st.title("🧠 CodeSage")
st.markdown("*Your expert AI coding companion for HTML, CSS, JavaScript, Python, and SQL*")

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-header">
                <span>You</span>
                <span class="time-tag">{message["timestamp"]}</span>
            </div>
            <div class="message-content">
                {message["content"]}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <div class="message-header">
                <span>🧠 CodeSage</span>
                <span class="time-tag">{message["timestamp"]}</span>
            </div>
            <div class="message-content">
                {message["content"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Input for new message
with st.form(key="message_form", clear_on_submit=True):
    user_input = st.text_area("Ask about code or request a code example:", key="user_input", height=100)
    col1, col2 = st.columns([1, 5])
    
    with col1:
        submit_button = st.form_submit_button("Send")
    
    with col2:
        if not st.session_state.gemini_api_key:
            st.warning("Please enter your Gemini API key in the sidebar.", icon="⚠️")

if submit_button and user_input:
    # Check if message is asking for unsupported language
    is_supported, unsupported_lang = check_language_support(user_input)
    
    # Display user message
    save_message(st.session_state.current_chat_id, "user", user_input)
    
    if not st.session_state.gemini_api_key:
        save_message(st.session_state.current_chat_id, "assistant", 
                   "⚠️ Please add your Gemini API key in the sidebar settings to continue.")
    elif not is_supported:
        save_message(st.session_state.current_chat_id, "assistant", 
                   f"I'm sorry, but I currently only support code generation for HTML, CSS, JavaScript, Python, and SQL. " 
                   f"I detected that you might be asking for {unsupported_lang} code, which I'm not configured to provide. " 
                   f"Please try asking for code in one of the supported languages instead.")
    else:
        # Display a placeholder for the assistant's response
        with st.spinner("CodeSage is thinking..."):
            # Check if message is about general search
            if any(term in user_input.lower() for term in ["search", "look up", "find me", "browse", "google"]):
                if not any(code_term in user_input.lower() for code_term in ["code", "function", "program", "script", "html", "css", "javascript", "python", "sql"]):
                    response = "I'm designed specifically for code generation and programming help in HTML, CSS, JavaScript, Python, and SQL. I can't perform general web searches or browse the internet. Please ask me about code-related topics instead!"
                    save_message(st.session_state.current_chat_id, "assistant", response)
            else:
                # Generate response with Gemini
                response = generate_response(st.session_state.gemini_api_key, st.session_state.messages)
                
                # Save the assistant's response
                save_message(st.session_state.current_chat_id, "assistant", response)
    
    # Rerun to update the UI with new messages
    st.rerun()

# Bottom space
st.markdown("<br><br>", unsafe_allow_html=True)

# Initialize first chat if needed
if not st.session_state.chat_history:
    create_new_chat()