import streamlit as st
import google.generativeai as genai
import os
import json
import uuid
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
gemini_key = os.getenv('GEMINI')

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
    
    /* Chat history container */
    .chat-history-container {
        display: flex;
        flex-direction: column;
        margin-bottom: 0.5rem;
    }
    
    /* Chat history item */
    .chat-history-item {
        display: flex;
        background-color: var(--navy-dark);
        color: var(--text-secondary);
        border-radius: 4px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        align-items: center;
        cursor: pointer;
        transition: all 0.3s ease;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .chat-history-item:hover {
        background-color: var(--navy-light);
        color: var(--text-primary);
    }
    
    .chat-history-item.active {
        background-color: var(--navy-light);
        color: var(--accent);
        border-left: 2px solid var(--accent);
    }
    
    /* Chat history item title */
    .chat-title {
        flex-grow: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    /* Chat history action buttons */
    .chat-actions {
        display: flex;
        gap: 0.5rem;
        margin-left: 0.5rem;
    }
    
    .action-button {
        background-color: transparent;
        color: var(--text-secondary);
        border: none;
        border-radius: 4px;
        padding: 0.1rem 0.3rem;
        font-size: 0.7rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .action-button:hover {
        background-color: rgba(100, 255, 218, 0.1);
        color: var(--accent);
    }
    
    .share-button {
        color: #6c74dc;
    }
    
    .delete-button {
        color: #ff6b6b;
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
    
    /* Share modal */
    .share-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(10, 25, 47, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }
    
    .share-modal-content {
        background-color: var(--navy);
        padding: 2rem;
        border-radius: 0.5rem;
        width: 80%;
        max-width: 600px;
    }
    
    .share-modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .share-modal-title {
        color: var(--text-primary);
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    .close-button {
        background-color: transparent;
        color: var(--text-secondary);
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .close-button:hover {
        color: var(--accent);
    }
    
    .share-options {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .share-option {
        display: flex;
        flex-direction: column;
        align-items: center;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.3s ease;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    
    .share-option:hover {
        background-color: var(--navy-light);
        color: var(--text-primary);
    }
    
    .share-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .share-label {
        font-size: 0.8rem;
    }
    
    /* Delete confirmation */
    .delete-confirm {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    
    .confirm-button {
        background-color: #ff6b6b;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .confirm-button:hover {
        background-color: #e95555;
    }
    
    .cancel-button {
        background-color: var(--navy-light);
        color: var(--text-primary);
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .cancel-button:hover {
        background-color: var(--navy);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}

if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())

if 'messages' not in st.session_state:
    st.session_state.messages = []

# For share/delete functionality
if 'show_share_modal' not in st.session_state:
    st.session_state.show_share_modal = False

if 'share_chat_id' not in st.session_state:
    st.session_state.share_chat_id = None

if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False

if 'delete_chat_id' not in st.session_state:
    st.session_state.delete_chat_id = None

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

def share_chat(chat_id):
    st.session_state.show_share_modal = True
    st.session_state.share_chat_id = chat_id

def delete_chat(chat_id):
    st.session_state.confirm_delete = True
    st.session_state.delete_chat_id = chat_id

def confirm_delete_chat():
    if st.session_state.delete_chat_id in st.session_state.chat_history:
        # If we're deleting the current chat, create a new one
        if st.session_state.delete_chat_id == st.session_state.current_chat_id:
            create_new_chat()
        # Delete the chat
        del st.session_state.chat_history[st.session_state.delete_chat_id]
        # Reset states
        st.session_state.confirm_delete = False
        st.session_state.delete_chat_id = None

def cancel_delete():
    st.session_state.confirm_delete = False
    st.session_state.delete_chat_id = None

def close_share_modal():
    st.session_state.show_share_modal = False
    st.session_state.share_chat_id = None

def export_chat_as_text(chat_id):
    if chat_id in st.session_state.chat_history:
        chat_text = f"CodeSage Chat - {st.session_state.chat_history[chat_id]['title']}\n"
        chat_text += f"Date: {st.session_state.chat_history[chat_id]['timestamp']}\n\n"
        
        for msg in st.session_state.chat_history[chat_id]["messages"]:
            sender = "You" if msg["role"] == "user" else "CodeSage"
            chat_text += f"{sender} ({msg['timestamp']}):\n{msg['content']}\n\n"
        
        return chat_text
    return ""

def generate_response(messages):
    try:
        # Use API key from .env file
        genai.configure(api_key=gemini_key)
        
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

# Check if API key is available but don't display status
api_key_available = gemini_key is not None and gemini_key != ""

# Sidebar
with st.sidebar:
    st.title("🧠 CodeSage")
    st.markdown("*Your expert AI coding companion*")
    
    # Lottie Animation
    lottie_coding = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_qp1q7mct.json")
    if lottie_coding:
        st_lottie(lottie_coding, speed=1, height=180, key="coding")
    
    # New chat button
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
            # Create a container for each chat history item with title and action buttons
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                if st.button(f"{chat_data['title']}", key=f"history_{chat_id}"):
                    load_chat(chat_id)
            
            with col2:
                if st.button("🔗", key=f"share_{chat_id}", help="Share conversation"):
                    share_chat(chat_id)
            
            with col3:
                if st.button("🗑️", key=f"delete_{chat_id}", help="Delete conversation"):
                    delete_chat(chat_id)
    
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
        if not api_key_available:
            st.warning("Please add your Gemini API key to the .env file", icon="⚠️")

if submit_button and user_input:
    # Check if message is asking for unsupported language
    is_supported, unsupported_lang = check_language_support(user_input)
    
    # Display user message
    save_message(st.session_state.current_chat_id, "user", user_input)
    
    if not api_key_available:
        save_message(st.session_state.current_chat_id, "assistant", 
                   "⚠️ Please add your Gemini API key to the .env file to continue.")
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
                response = generate_response(st.session_state.messages)
                
                # Save the assistant's response
                save_message(st.session_state.current_chat_id, "assistant", response)
    
    # Rerun to update the UI with new messages
    st.rerun()

# Share modal
if st.session_state.show_share_modal:
    chat_id = st.session_state.share_chat_id
    if chat_id in st.session_state.chat_history:
        chat_title = st.session_state.chat_history[chat_id]["title"]
        chat_text = export_chat_as_text(chat_id)
        
        # Display share modal
        st.markdown(f"""
        <div class="share-modal">
            <div class="share-modal-content">
                <div class="share-modal-header">
                    <div class="share-modal-title">Share Conversation: {chat_title}</div>
                    <button class="close-button" onclick="handleCloseModal()">×</button>
                </div>
                <textarea id="chat-export" style="width:100%; height:200px; background-color:#1E2D3D; color:#CCD6F6; border:none; border-radius:4px; padding:1rem; margin-bottom:1rem;" readonly>{chat_text}</textarea>
                <div style="display:flex; justify-content:space-between;">
                    <button onclick="copyToClipboard()" class="stButton button">Copy to Clipboard</button>
                    <div class="share-options">
                        <div class="share-option" onclick="shareToWhatsApp()">
                            <span class="share-icon">📱</span>
                            <span class="share-label">WhatsApp</span>
                        </div>
                        <div class="share-option" onclick="shareToEmail()">
                            <span class="share-icon">✉️</span>
                            <span class="share-label">Email</span>
                        </div>
                        <div class="share-option" onclick="downloadAsText()">
                            <span class="share-icon">📄</span>
                            <span class="share-label">Download</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function handleCloseModal() {{
             const buttons = parent.document.querySelectorAll('button');
                for (let i = 0; i < buttons.length; i++) {{
                  if (buttons[i].innerText === 'Close Share Modal') {{
                        buttons[i].click();
                        break;
                    }}
                }}
            }}
            
            function copyToClipboard() {{
                const textarea = document.getElementById('chat-export');
                textarea.select();
                document.execCommand('copy');
                alert('Copied to clipboard!');
            }}
            
            function shareToWhatsApp() {{
                const text = encodeURIComponent(document.getElementById('chat-export').value);
                window.open(`https://wa.me/?text=${{text}}`, '_blank');
            }}
            
            function shareToEmail() {{
                const subject = encodeURIComponent('CodeSage Chat History');
                const body = encodeURIComponent(document.getElementById('chat-export').value);
                window.location.href = `mailto:?subject=${{subject}}&body=${{body}}`;
            }}
            
            function downloadAsText() {{
                const text = document.getElementById('chat-export').value;
                const filename = 'codesage-chat-history.txt';
                const element = document.createElement('a');
                element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
                element.setAttribute('download', filename);
                element.style.display = 'none';
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
            }}
        </script>
        """, unsafe_allow_html=True)
        
        # Hidden button to close modal (triggered by JavaScript)
        if st.button("Close Share Modal", key="close_share_modal"):
            close_share_modal()

# Delete confirmation
if st.session_state.confirm_delete:
    chat_id = st.session_state.delete_chat_id
    if chat_id in st.session_state.chat_history:
        chat_title = st.session_state.chat_history[chat_id]["title"]
        
        # Display confirmation dialog
        st.warning(f"Are you sure you want to delete '{chat_title}'?")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Yes, delete", key="confirm_delete"):
                confirm_delete_chat()
                st.rerun()
        
        with col2:
            if st.button("Cancel", key="cancel_delete"):
                cancel_delete()
                st.rerun()

# Bottom space
st.markdown("<br><br>", unsafe_allow_html=True)

# Initialize first chat if needed
if not st.session_state.chat_history:
    create_new_chat()