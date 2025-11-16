import streamlit as st
import time
import uuid
from datetime import datetime
# --- OPTIMIZATION ---
# Import from the new, faster services_v2.py file

try:
    from services_v2 import (
        handle_natural_conversation,
        search_github_repos,
        run_professional_analysis,
        search_research_papers,
        generate_comprehensive_synopsis,
        load_memory,
        save_memory,
        get_ai_response,
        auto_research_project
    )
    _services_ok = True
except Exception as _e:
    print(f"Warning: Could not import services_v2: {_e}")
    _services_ok = False
    # define safe fallbacks so UI can start
    def handle_natural_conversation(*args, **kwargs):
        return {
            "response": "Service unavailable: backend services failed to import. Check logs.",
            "updated_memory": kwargs.get("current_memory", {}) if kwargs else {},
            "updated_fields": [],
            "missing_info": [],
            "auto_research_triggered": False,
            "research_results": {}
        }
    # Provide minimal fallbacks for other functions as needed...
if not _services_ok:
    import streamlit as st
    st.error(
        "⚠️ Some backend services failed to load. "
        "Please check your environment variables and restart the app."
    )
    st.stop()  # Stop the app from proceeding further

import json

# ----------------------------
# Streamlit Page Configuration
# ----------------------------
st.set_page_config(
    page_title="AURA - Intelligent Research Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/aura',
        'Report a bug': "https://github.com/yourusername/aura/issues",
        'About': "# AURA - AI-powered Research Assistant\nVersion 2.0"
    }
)

# ----------------------------
# Custom CSS for Enhanced UI
# ----------------------------
st.markdown("""
<style>
/* Main container styling */
.main {
    padding: 0rem 1rem;
}

/* Header gradient animation */
@keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.main-header {
    font-size: 3.5rem;
    font-weight: 800;
    background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c);
    background-size: 400% 400%;
    animation: gradient 15s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.5rem;
    padding: 1rem 0;
}

.subtitle {
    text-align: center;
    color: #666;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Progress indicators */
.progress-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    color: white;
    margin-bottom: 1rem;
}

.progress-item {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    margin: 0.3rem 0;
    backdrop-filter: blur(10px);
}

.progress-complete {
    background: rgba(76, 175, 80, 0.2);
    border-left: 3px solid #4caf50;
}

/* Stage indicator */
.stage-indicator {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 10px 20px;
    border-radius: 25px;
    font-size: 0.9rem;
    display: inline-block;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Alert boxes */
.auto-research-alert {
    background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
    border-left: 4px solid #4caf50;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 8px;
    color: #1a1a1a;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.synopsis-ready {
    background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
    border: 2px solid #fdcb6e;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    color: #2d3436;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* Chat message styling */
.stChatMessage {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    margin: 0.5rem 0;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.5rem 1.5rem;
    border-radius: 25px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* --- Transparent Sidebar (Glassmorphism Style) --- */
[data-testid="stSidebar"], .stSidebar, section[data-testid="stSidebar"] {
    background: rgba(0, 0, 0, 0.25) !important;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: none !important;
}

/* Sidebar content cards & buttons adjustments */
[data-testid="stSidebar"] .block-container {
    background: transparent !important;
    color: #fff !important;
}

[data-testid="stSidebar"] * {
    color: #f0f0f0 !important;
}



/* Quick action buttons */
.quick-action-btn {
    background: white;
    border: 2px solid #667eea;
    color: #667eea;
    padding: 0.75rem;
    border-radius: 12px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
}

.quick-action-btn:hover {
    background: #667eea;
    color: white;
    transform: translateY(-2px);
}

/* Info cards */
.info-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Session State Initialization
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "synopsis_memory" not in st.session_state:
    st.session_state.synopsis_memory = load_memory(st.session_state.session_id)

if "auto_research_done" not in st.session_state:
    st.session_state.auto_research_done = False

if "initial_greeting" not in st.session_state:
    st.session_state.initial_greeting = True
    greeting = """👋 **Hello! I'm AURA, your intelligent research assistant.**

I'm here to help you develop your project idea from concept to complete documentation. Just start telling me about your project idea naturally, and I'll:

🔍 **Automatically research** similar projects and papers
📝 **Extract key information** for your synopsis as we chat  
🎯 **Ask intelligent questions** to understand your vision better
📄 **Generate comprehensive documentation** when ready

**What's your project idea? Tell me about it in your own words!** 💡"""
    
    st.session_state.messages.append({"role": "assistant", "content": greeting})

# ----------------------------
# Header Section
# ----------------------------
st.markdown('<h1 class="main-header">✨ AURA</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Your AI-Powered Research Assistant for Academic Excellence</p>', unsafe_allow_html=True)

# Current stage indicator
memory = st.session_state.synopsis_memory
filled_count = len([k for k, v in memory.items() if v and len(str(v).strip()) > 10])

if filled_count == 0:
    stage = "🌱 Getting Started"
elif filled_count < 3:
    stage = "📝 Gathering Information"
elif filled_count < 5:
    stage = "🔬 Research Phase"
else:
    stage = "📄 Ready for Synopsis"

st.markdown(f'<div class="stage-indicator">{stage}</div>', unsafe_allow_html=True)

# ----------------------------
# Sidebar with Enhanced Progress Tracking
# ----------------------------
with st.sidebar:
    st.markdown("## 📊 **Project Progress**")
    
    # Progress visualization
    progress_items = {
        "title": ("📝 Project Title", memory.get("title")),
        "group_details": ("👥 Team Details", memory.get("group_details")),
        "objective_scope": ("🎯 Objectives & Scope", memory.get("objective_scope")),
        "process_description": ("⚙️ Methodology", memory.get("process_description")),
        "resources_limitations": ("📋 Resources", memory.get("resources_limitations")),
        "conclusion": ("🎉 Expected Outcomes", memory.get("conclusion")),
        "references": ("📚 References", memory.get("references"))
    }
    
    completed = sum(1 for _, (_, value) in progress_items.items() if value)
    total = len(progress_items)
    
    # Enhanced progress bar
    progress = completed / total
    st.progress(progress)
    
    if progress < 0.3:
        progress_color = "🔴"
    elif progress < 0.7:
        progress_color = "🟡"
    else:
        progress_color = "🟢"
    
    st.markdown(f"### {progress_color} **{completed}/{total} sections** ({progress:.0%})")
    
    # Detailed progress items
    st.markdown("---")
    for key, (label, value) in progress_items.items():
        if value:
            st.success(f"✅ {label}")
            with st.expander("View content", expanded=False):
                st.write(str(value)[:200] + "..." if len(str(value)) > 200 else str(value))
        else:
            st.info(f"⏳ {label}")
    
    # Research status section
    st.markdown("---")
    st.markdown("### 🔬 **Research Status**")
    
    if memory.get("auto_research_done"):
        st.success("✅ **Auto-research completed!**")
        research_items = [
            "📄 Introduction generated",
            "📚 Literature review completed",
            "⚙️ Methodology analyzed",
            "💻 Requirements specified",
            "📊 Feasibility assessed"
        ]
        for item in research_items:
            st.write(item)
    else:
        st.info("⏳ Auto-research pending...")
        st.caption("Will trigger automatically when enough information is gathered")
    
    # Synopsis generation section
    st.markdown("---")
    st.markdown("### 📄 **Synopsis Generation**")
    
    if completed >= 3:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 **Generate Synopsis**", use_container_width=True):
                with st.spinner("Creating your comprehensive synopsis..."):
                    filename = generate_comprehensive_synopsis(
                        st.session_state.session_id,
                        idea=memory.get("title"),
                        research_data=memory
                    )
                    with open(filename, "rb") as f:
                        pdf_bytes = f.read()
                
                    st.success("✅ Synopsis generated successfully!")
        
        with col2:
            if 'pdf_bytes' in locals():
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=f"synopsis_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    else:
        st.info(f"Need {3 - completed} more sections before generating synopsis")
    
    # Session info
    st.markdown("---")
    with st.expander("🔧 Session Info"):
        st.write(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
        st.write(f"**Messages:** {len(st.session_state.messages)}")
        st.write(f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ----------------------------
# Main Chat Interface
# ----------------------------
# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        if msg["role"] == "assistant" and "auto-research-alert" in msg.get("content", ""):
            st.markdown(msg["content"], unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# Chat input handler
if prompt := st.chat_input("💬 Tell me about your project idea or ask any questions..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.conversation_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # Process with AURA
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        
        # --- OPTIMIZATION ---
        # Removed the fake time.sleep() loop.
        # We will wrap the actual, slow function call in a single spinner.
        
        with st.spinner("🤔 AURA is thinking..."):
            try:
                # This is the real "laggy" function call (now optimized in services_v2.py)
                result = handle_natural_conversation(
                    prompt, 
                    st.session_state.conversation_history,
                    st.session_state.session_id,
                    st.session_state.synopsis_memory
                )
                
                # Update session state
                st.session_state.synopsis_memory = result["updated_memory"]
                st.session_state.conversation_history.append({
                    "role": "assistant", 
                    "content": result["response"]
                })
                
                # Build enhanced response
                response_parts = [result["response"]]
                
                # Add auto-research notification if triggered
                if result.get("auto_research_triggered"):
                    st.session_state.auto_research_done = True
                    research_alert = """
                    
<div class="auto-research-alert">
<h4>🔬 Auto-Research Complete!</h4>
<p>I've automatically conducted comprehensive research for your project:</p>
<ul>
<li>✅ Generated detailed introduction</li>
<li>✅ Created literature review with citations</li>
<li>✅ Analyzed technical methodology</li>
<li>✅ Specified system requirements</li>
<li>✅ Conducted feasibility analysis</li>
</ul>
<p><strong>All research has been integrated into your synopsis!</strong></p>
</div>"""
                    response_parts.append(research_alert)
                
                # Add updated fields notification
                if result.get("updated_fields"):
                    fields_str = ", ".join(result["updated_fields"])
                    response_parts.append(f"\n\n*📝 Updated: {fields_str}*")
                
                # Check if ready for synopsis
                filled_fields = len([k for k, v in result["updated_memory"].items() 
                                    if v and len(str(v).strip()) > 10])
                
                if filled_fields >= 4 and not st.session_state.synopsis_memory.get("synopsis_offer_shown"):
                    synopsis_ready = """
                    
<div class="synopsis-ready">
<h4>🎉 Ready for Synopsis Generation!</h4>
<p>Great progress! I have enough information to generate your comprehensive synopsis.</p>
<p><strong>👉 Click "Generate Synopsis" in the sidebar</strong> or ask me to create it!</p>
</div>"""
                    response_parts.append(synopsis_ready)
                    st.session_state.synopsis_memory["synopsis_offer_shown"] = True
                    save_memory(st.session_state.session_id, st.session_state.synopsis_memory)
                
                # Display complete response
                full_response = "\n".join(response_parts)
                message_placeholder.markdown(full_response, unsafe_allow_html=True)
                
                # Add to message history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response
                })
                
            except Exception as e:
                error_msg = f"❌ An error occurred: {str(e)}\n\nPlease try again or rephrase your message."
                message_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# ----------------------------
# Quick Actions Section
# ----------------------------
st.markdown("---")
st.markdown("### 🚀 **Quick Actions**")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔍 **Find Similar Projects**", use_container_width=True):
        if st.session_state.synopsis_memory.get("title"):
            with st.spinner("Searching GitHub..."):
                # This now calls the cached function from services_v2.py
                repos = search_github_repos(
                    st.session_state.synopsis_memory["title"], 
                    limit=5
                )
                with st.expander("📦 Similar Projects Found", expanded=True):
                    for repo in repos:
                        st.markdown(repo)
        else:
            st.warning("💡 Please share your project idea first!")

with col2:
    if st.button("📚 **Research Papers**", use_container_width=True):
        if st.session_state.synopsis_memory.get("title"):
            with st.spinner("Finding research papers..."):
                # This now calls the cached function from services_v2.py
                papers = search_research_papers(
                    st.session_state.synopsis_memory["title"],
                    limit=5
                )
                with st.expander("📄 Relevant Papers", expanded=True):
                    for paper in papers:
                        st.markdown(paper)
        else:
            st.warning("💡 Please share your project idea first!")

with col3:
    if st.button("📊 **Professional Analysis**", use_container_width=True):
        if st.session_state.synopsis_memory.get("title"):
            with st.spinner("Conducting analysis..."):
                repos = search_github_repos(
                    st.session_state.synopsis_memory["title"], 
                    limit=3
                )
                # This now calls the cached function from services_v2.py
                analysis = run_professional_analysis(
                    st.session_state.synopsis_memory["title"],
                    repos
                )
                with st.expander("🎯 Professional Analysis", expanded=True):
                    st.markdown(analysis)
        else:
            st.warning("💡 Please share your project idea first!")

with col4:
    if st.button("💡 **Get AI Suggestions**", use_container_width=True):
        if st.session_state.synopsis_memory.get("title"):
            with st.spinner("Generating suggestions..."):
                suggestion_prompt = f"""
                Based on this project: {json.dumps(st.session_state.synopsis_memory)}
                
                Provide 5 specific, actionable suggestions to improve the project:
                1. Technical enhancements
                2. Implementation strategies
                3. Potential challenges to address
                4. Innovation opportunities
                5. Market differentiation
                
                Be specific and practical.
                """
                
                suggestions = get_ai_response(
                    [{"role": "user", "content": suggestion_prompt}]
                )
                
                with st.expander("💡 AI Suggestions", expanded=True):
                    st.markdown(suggestions)
        else:
            st.warning("💡 Please share your project idea first!")

# ----------------------------
# Help Section
# ----------------------------
with st.expander("❓ **How to Use AURA**"):
    st.markdown("""
    ### 🎯 **Getting Started**
    1. **Start naturally** - Just tell me about your project idea in your own words
    2. **No forms needed** - I'll extract information from our conversation
    3. **Ask anything** - Get help with technical questions, implementation, or ideas
    
    ### 🔬 **Auto-Research Feature**
    - Automatically triggers when enough information is gathered
    - Generates introduction, literature review, and methodology
    - Analyzes requirements and feasibility
    - All research is integrated into your final synopsis
    
    ### 📄 **Synopsis Generation**
    - Available after 3+ sections are filled
    - Creates professional PDF following academic standards
    - Includes all B.Tech project requirements
    - Fully formatted and ready for submission
    
    ### 💡 **Tips for Best Results**
    - Be specific about your project goals
    - Mention technologies you plan to use
    - Share any constraints or requirements
    - Ask for suggestions when stuck
    
    ### 🚀 **Quick Actions**
    - **Find Similar Projects**: Discover related GitHub repositories
    - **Research Papers**: Find academic papers in your domain
    - **Professional Analysis**: Get expert-level project analysis
    - **AI Suggestions**: Receive personalized improvement ideas
    """)

# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>AURA v2.0 | Powered by Advanced AI | Made with ❤️ for Students</p>
    <p style='font-size: 0.9em;'>© 2024 BRCM College of Engineering & Technology</p>
</div>
""", unsafe_allow_html=True)
