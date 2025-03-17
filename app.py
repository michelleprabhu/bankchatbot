import streamlit as st
from neo4j import GraphDatabase
import google.generativeai as genai  # For Gemini API integration
import time
import random
import os

# Set your Gemini API key from Streamlit secrets
try:
    genai.configure(api_key=st.secrets["gemini_api_key"])
except Exception as e:
    st.error("Failed to configure Gemini API. Check your API key in Streamlit secrets.")

# Database connection function
def get_db_connection():
    return GraphDatabase.driver(
        st.secrets["neo4j_uri"],
        auth=(st.secrets["neo4j_user"], st.secrets["neo4j_password"])
    )

# Function to fetch relevant bank policies from Neo4j
def fetch_policies(query):
    conn = get_db_connection()
    session = conn.session()
    
    cypher_query = """
    MATCH (p:Policy)
    WHERE p.text CONTAINS $query
    RETURN p.text AS policy_text
    """
    results = session.run(cypher_query, query=query)
    policies = [record["policy_text"] for record in results]
    
    session.close()
    conn.close()
    
    return policies if policies else ["No relevant policies found."]

# Function to get response from Gemini API
def get_gemini_response(query, policies):
    context = "\n".join(policies)
    prompt = f"Based on the following bank policies, answer the question: \n\n{context}\n\nQuestion: {query}\nAnswer: "
    
    try:
        model = genai.GenerativeModel("gemini-1.0-pro-latest")
        response = model.generate_content(prompt)
        return response.text if response else "I'm unable to find an answer."
    except Exception as e:
        return "Error retrieving response from Gemini API. Please check your API key and internet connection."

# Streamlit UI Enhancements
st.set_page_config(page_title="Bank Policy Chatbot", page_icon="💬", layout="wide")

st.markdown(
    """
    <style>
        .stTextInput>div>div>input {
            font-size: 16px;
            padding: 10px;
            border-radius: 10px;
        }
        .stButton>button {
            font-size: 16px;
            padding: 10px 20px;
            border-radius: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .chat-container {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            animation: fadeIn 0.5s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("💬 Bank Policy Chatbot")
st.write("👋 Welcome! Ask me anything about banking policies!")

# Chat-like interface with animation
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User input section
user_query = st.text_input("Type your question below and press Enter:")
submit_button = st.button("Ask")

if submit_button and user_query:
    with st.spinner("Thinking..."):
        policies = fetch_policies(user_query)
        gemini_response = get_gemini_response(user_query, policies)
        time.sleep(random.uniform(0.5, 1.5))  # Simulating response delay with animation
    
    # Append the conversation to chat history
    st.session_state.chat_history.append(("You", user_query))
    st.session_state.chat_history.append(("Bot", gemini_response))

# Display chat history with animations
st.write("### 📝 Chat History")
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for speaker, text in st.session_state.chat_history:
    st.markdown(
        f"<p style='animation: fadeIn 0.5s ease-in-out;'><b>{speaker}:</b> {text}</p>", 
        unsafe_allow_html=True
    )
st.markdown("</div>", unsafe_allow_html=True)
