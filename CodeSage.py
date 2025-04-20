import warnings
warnings.filterwarnings("ignore")

import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import re
import uuid
from datetime import datetime
import sys
import json

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
    .session-item {
        background-color: #1b263b;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
        cursor: pointer;
    }
    .session-item:hover {
        background-color: #415a77;
    }
    .session-title {
        font-weight: bold;
    }
    .session-date {
        font-size: 0.8em;
        color: #adb5bd;
    }
    .active-session {
        border-left: 4px solid #4caf50;
    }
    .session-actions {
        display: flex;
        gap: 5px;
        margin-top: 5px;
    }
    .session-action-btn {
        background-color: #415a77;
        color: #e0e1dd;
        border: none;
        padding: 2px 5px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 0.8em;
    }
    .session-action-btn:hover {
        background-color: #778da9;
    }
    .notification {
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 10px;
        background-color: #4caf50;
        color: white;
        border-radius: 5px;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

# Define the data storage path
SESSION_DATA_FILE = "codecraft_sessions.json"

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'input_key' not in st.session_state:
    st.session_state.input_key = str(uuid.uuid4())

if 'sessions' not in st.session_state:
    st.session_state.sessions = {}

if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None

if 'notification' not in st.session_state:
    st.session_state.notification = None

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
    
    # Update the current session with the modified chat history
    if st.session_state.current_session_id:
        save_current_session()
        
    st.rerun()

# Function to check if prompt is requesting code
def is_code_request(prompt):
    # List of code-related keywords
    code_keywords = [
        'code', 'function', 'program', 'script', 'algorithm', 'class', 'method',
        'implement', 'develop', 'build', 'create a', 'write a', 'generate a',
        'python', 'javascript', 'html', 'css', 'java', 'c++', 'c#', 'ruby', 'php',
        'typescript', 'swift', 'kotlin', 'rust', 'go', 'dart', 'react', 'angular',
        'vue', 'node', 'django', 'flask', 'express', 'api', 'database', 'sql',
        'mongodb', 'json', 'xml', 'app', 'application', 'git', 'docker', 'aws',
        'azure', 'tensorflow', 'pytorch', 'numpy', 'pandas', 'scikit', 'matplotlib',
        'selenium', 'beautiful soup', 'regex', 'rest', 'graphql', 'web scraping'
    ]
    
    # Non-code patterns (questions about theory, explanations, etc.)
    non_code_patterns = [
        r'explain about', r'what is', r'tell me about', r'how does', r'describe',
        r'history of', r'difference between', r'compare', r'advantages of',
        r'disadvantages', r'pros and cons', r'benefits of', r'drawbacks of',
        r'when to use', r'why use', r'definition of', r'meaning of', r'features of',
        r'characteristics', r'theory', r'concept', r'principles', r'explain'
    ]
    
    # Check if the prompt contains any code-related keywords
    has_code_keywords = any(keyword.lower() in prompt.lower() for keyword in code_keywords)
    
    # Check if the prompt matches any non-code patterns
    is_non_code_request = any(re.search(pattern, prompt.lower()) for pattern in non_code_patterns)
    
    # Return True if it has code keywords and doesn't match non-code patterns
    return has_code_keywords and not is_non_code_request

# Function to generate auto session title
def generate_session_title(first_message):
    try:
        prompt = f"""
        Create a short, concise title (3-5 words) that summarizes the following message content. 
        The title should be specific enough to identify the general topic but brief enough to serve as a chat session name.
        
        Message: {first_message}
        
        Return ONLY the title with no quotes, explanation, or additional text.
        """
        
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 32,
            "max_output_tokens": 20,
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        title = response.text.strip()
        
        # Limit length and clean up title
        if len(title) > 50:
            title = title[:47] + "..."
            
        return title
    except Exception as e:
        # Fallback title with timestamp
        return f"CodeCraft Session {datetime.now().strftime('%b %d, %H:%M')}"

# Function to load sessions from file
def load_sessions():
    try:
        if os.path.exists(SESSION_DATA_FILE):
            with open(SESSION_DATA_FILE, 'r') as f:
                sessions_data = json.load(f)
                return sessions_data
        return {}
    except Exception as e:
        st.error(f"Error loading sessions: {str(e)}")
        return {}

# Function to save sessions to file
def save_sessions():
    try:
        with open(SESSION_DATA_FILE, 'w') as f:
            json.dump(st.session_state.sessions, f)
    except Exception as e:
        st.error(f"Error saving sessions: {str(e)}")

# Function to save the current session
def save_current_session():
    if st.session_state.current_session_id:
        session_id = st.session_state.current_session_id
        
        # Update the session data
        st.session_state.sessions[session_id]['messages'] = st.session_state.chat_history
        st.session_state.sessions[session_id]['last_updated'] = datetime.now().isoformat()
        
        # Save to file
        save_sessions()

# Function to create a new session
def create_new_session(title=None):
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Create a new session entry
    st.session_state.sessions[session_id] = {
        'id': session_id,
        'title': title if title else f"New Session {datetime.now().strftime('%b %d, %H:%M')}",
        'created_at': timestamp,
        'last_updated': timestamp,
        'messages': []
    }
    
    # Update current session ID
    st.session_state.current_session_id = session_id
    
    # Clear chat history for the new session
    st.session_state.chat_history = []
    
    # Save sessions
    save_sessions()
    
    # Show notification
    set_notification(f"New session '{st.session_state.sessions[session_id]['title']}' created")
    
    return session_id

# Function to load a session
def load_session(session_id):
    if session_id in st.session_state.sessions:
        # Set current session ID
        st.session_state.current_session_id = session_id
        
        # Load chat history from the session
        st.session_state.chat_history = st.session_state.sessions[session_id]['messages']
        
        # Update the last accessed timestamp
        st.session_state.sessions[session_id]['last_updated'] = datetime.now().isoformat()
        save_sessions()
        
        # Show notification
        set_notification(f"Loaded session: {st.session_state.sessions[session_id]['title']}")
        
        return True
    
    return False

# Function to delete a session
def delete_session(session_id):
    if session_id in st.session_state.sessions:
        session_title = st.session_state.sessions[session_id]['title']
        
        # Remove the session
        del st.session_state.sessions[session_id]
        
        # Save sessions
        save_sessions()
        
        # If the current session was deleted, create a new session
        if st.session_state.current_session_id == session_id:
            create_new_session()
        
        # Show notification
        set_notification(f"Session '{session_title}' deleted successfully")
        
        return True
    
    return False

# Function to rename a session
def rename_session(session_id, new_title):
    if session_id in st.session_state.sessions:
        old_title = st.session_state.sessions[session_id]['title']
        
        # Update the title
        st.session_state.sessions[session_id]['title'] = new_title
        
        # Save sessions
        save_sessions()
        
        # Show notification
        set_notification(f"Session renamed from '{old_title}' to '{new_title}'")
        
        return True
    
    return False

# Function to set a notification
def set_notification(message):
    st.session_state.notification = {
        'message': message,
        'timestamp': datetime.now()
    }

# Function to handle message submission
def handle_submit(user_input):
    if user_input.strip():
        # Check if the input is a session management command
        if handle_session_command(user_input):
            # Reset the input field
            reset_input()
            return
        
        # If no current session, create one
        if not st.session_state.current_session_id:
            session_id = create_new_session()
        
        # Add user message to chat history
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%I:%M %p · %d %b %Y")
        
        st.session_state.chat_history.append({
            'id': message_id,
            'role': 'user',
            'content': user_input,
            'timestamp': timestamp
        })
        
        # Auto-generate title for new sessions with no messages
        if (st.session_state.current_session_id and 
            len(st.session_state.sessions[st.session_state.current_session_id]['messages']) == 0 and
            st.session_state.sessions[st.session_state.current_session_id]['title'].startswith("New Session")):
            new_title = generate_session_title(user_input)
            rename_session(st.session_state.current_session_id, new_title)
        
        # Check if the prompt is requesting code or not
        if is_code_request(user_input):
            # Generate AI response for code
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
        else:
            # Handle non-code requests with a helpful message
            non_code_response = """
I'm CodeCraft AI, designed specifically to help you generate code. I can't provide explanations about concepts, theories, or general information.

Please rephrase your request to ask for specific code implementation, such as:
- "Create a Python function to..."
- "Write JavaScript code that..."
- "Build an HTML form with..."

For general information, you might want to use a different AI assistant or search engine.
"""
            # Add non-code response to chat history
            non_code_message_id = str(uuid.uuid4())
            st.session_state.chat_history.append({
                'id': non_code_message_id,
                'role': 'assistant',
                'content': non_code_response,
                'timestamp': timestamp
            })
        
        # Save current session
        save_current_session()
        
        # Reset the input field by using a new key
        reset_input()
        
        # Updated to use st.rerun()
        st.rerun()

# Function to handle session management commands
def handle_session_command(user_input):
    input_lower = user_input.lower().strip()
    
    # Command to show sessions
    if re.match(r'^(show|list) (my )?(previous |all )?(sessions|chats)$', input_lower):
        # Will display in the sidebar, no action needed here
        set_notification("Your sessions are displayed in the sidebar")
        return True
    
    # Command to create a new session
    if re.match(r'^(create|start) (a )?(new )?session( called| named| titled)? (.+)$', input_lower):
        title_match = re.match(r'^(create|start) (a )?(new )?session( called| named| titled)? (.+)$', input_lower)
        if title_match:
            title = title_match.group(5).strip().strip('"\'')
            create_new_session(title)
            return True
    
    # Command to create a new session (simple version)
    if re.match(r'^(create|start) (a )?(new )?session$', input_lower):
        create_new_session()
        return True
    
    # Command to rename current session
    if re.match(r'^rename (this|current) (session|chat)( to| as)? (.+)$', input_lower):
        if st.session_state.current_session_id:
            title_match = re.match(r'^rename (this|current) (session|chat)( to| as)? (.+)$', input_lower)
            if title_match:
                new_title = title_match.group(4).strip().strip('"\'')
                rename_session(st.session_state.current_session_id, new_title)
                return True
        else:
            set_notification("No active session to rename. Create a new session first.")
            return True
    
    # Command to delete current session
    if re.match(r'^delete (this|current) (session|chat)$', input_lower):
        if st.session_state.current_session_id:
            delete_session(st.session_state.current_session_id)
            return True
        else:
            set_notification("No active session to delete.")
            return True
    
    # Command to clear chat history in current session
    if re.match(r'^clear (this|current|the) (session|chat|history)$', input_lower):
        if st.session_state.current_session_id:
            st.session_state.chat_history = []
            save_current_session()
            set_notification("Chat history cleared for the current session")
            return True
        else:
            set_notification("No active session to clear.")
            return True
    
    return False

# Function to generate code
def generate_code(prompt):
    try:
        # Enhance the prompt to ensure only code is generated
        enhanced_prompt = f"""
        You are CodeCraft AI, an elite-level programmer that ONLY generates code, never explanations or theory.
        
        Generate clean, optimized, and working code for the following request:
        
        {prompt}

       Act like an elite-level software engineer and prompt engineering expert. You have been writing optimized, scalable, and clean code in multiple languages for over 20 years. You are deeply familiar with performance tuning, code modularity, algorithm efficiency, and best practices in documentation. You also specialize in using AI systems like GPT-4 to generate accurate and production-level code.

        Your task is to generate high-quality, working code in response to a user’s request. To ensure maximum quality, follow these steps:

        Step 1: Break down the problem into logical components. Explain what the user is asking for in your own words and what the output should accomplish.
        Step 2: Propose an architectural or algorithmic approach. Highlight any important trade-offs, edge cases, or assumptions.
        Step 3: Write clean, optimized, and well-documented code to implement the solution.

        Use detailed comments to explain what each part does

        Take a deep breath and work on this problem step-by-step.
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

def show_sessions_sidebar():
    st.sidebar.title("Your Sessions")
    
    # Add a button to create a new session
    if st.sidebar.button("➕ New Session"):
        create_new_session()
        st.rerun()
    
    # Get sessions sorted by last updated
    sessions_list = list(st.session_state.sessions.values())
    sessions_list.sort(key=lambda x: x['last_updated'], reverse=True)
    
    # Display sessions
    if sessions_list:
        for session in sessions_list:
            # Format last updated date
            last_updated = datetime.fromisoformat(session['last_updated'])
            date_str = last_updated.strftime("%b %d, %Y")
            
            # Create a container for the session item
            session_container = st.sidebar.container()
            
            # Check if this is the active session
            is_active = session['id'] == st.session_state.current_session_id
            
            # Display session with title and date
            with session_container:
                col1, col2 = st.columns([7, 1])
                
                with col1:
                    # Use markdown for custom styling
                    if is_active:
                        st.markdown(f"""
                        <div class='session-item active-session' id='{session['id']}'>
                            <div class='session-title'>{session['title']}</div>
                            <div class='session-date'>{date_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Use a button that looks like a div for better UX
                        if st.button(f"{session['title']}", key=f"session_btn_{session['id']}"):
                            load_session(session['id'])
                            st.rerun()
                            
                        st.markdown(f"<div class='session-date'>{date_str}</div>", unsafe_allow_html=True)
                
                with col2:
                    # Session actions (delete)
                    if st.button("🗑️", key=f"delete_{session['id']}", help="Delete session"):
                        delete_session(session['id'])
                        st.rerun()
    else:
        st.sidebar.info("No sessions yet. Start chatting to create your first session!")

def main():
    # Load sessions from file when the app starts
    if not st.session_state.sessions:
        st.session_state.sessions = load_sessions()
        
        # If there are sessions but no current session, set the most recent one
        if st.session_state.sessions and not st.session_state.current_session_id:
            sessions_list = list(st.session_state.sessions.values())
            sessions_list.sort(key=lambda x: x['last_updated'], reverse=True)
            st.session_state.current_session_id = sessions_list[0]['id']
            st.session_state.chat_history = st.session_state.sessions[st.session_state.current_session_id]['messages']
    
    # If no sessions exist, create a default one
    if not st.session_state.sessions:
        create_new_session("Welcome Session")
    
    # App title
    st.markdown("<h1 style='text-align: center; color: #e0e1dd;'>CodeCraft AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #778da9;'>Ask me to generate code in any programming language</p>", unsafe_allow_html=True)
    
    # Display current session title if available
    if st.session_state.current_session_id:
        current_session = st.session_state.sessions.get(st.session_state.current_session_id)
        if current_session:
            st.markdown(f"<h3 style='text-align: center; color: #778da9;'>Session: {current_session['title']}</h3>", unsafe_allow_html=True)

    # Display notification if exists
    if st.session_state.notification:
        notification = st.session_state.notification
        notification_time = notification.get('timestamp')
        
        # Only show notifications that are less than 5 seconds old
        if notification_time and (datetime.now() - notification_time).total_seconds() < 5:
            st.markdown(f"""
            <div class="notification">
                {notification['message']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.session_state.notification = None

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
            user_input = st.text_area("Ask me to generate code or manage sessions...", height=100, key=st.session_state.input_key)
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

    # Add a clear button to delete all chat history for current session
    if st.button("Clear Current Chat History"):
        if st.session_state.current_session_id:
            st.session_state.chat_history = []
            save_current_session()
            st.rerun()

    # Display sessions in sidebar
    show_sessions_sidebar()

    # Show example prompts in the sidebar
    st.sidebar.title("Example Prompts")
    st.sidebar.markdown("""
    - "Create a Python function to find prime numbers"
    - "Write HTML and CSS for a responsive navigation bar"
    - "Generate a JavaScript function that calculates Fibonacci sequence"
    - "Build a Flask API with a POST endpoint to accept JSON data"
    - "Create a React component for a form with validation"
    """)
    
    # Show session management commands
    st.sidebar.title("Session Commands")
    # Show session management commands
    st.sidebar.title("Session Commands")
    st.sidebar.markdown("""
    - "Create a new session called [name]"
    - "Rename this session to [name]"
    - "Delete this session"
    - "Clear this chat"
    - "Show my sessions"
    """)
    
    # Add a clear note about the purpose of the agent
    st.sidebar.title("About CodeCraft AI")
    st.sidebar.info("""
    CodeCraft AI is designed specifically to generate code. It cannot provide explanations about concepts, theories, or general information. 
    
    Please phrase your requests as specific code implementation tasks.
    """)

# Add this condition to ensure proper script execution
if __name__ == "__main__":
    main()