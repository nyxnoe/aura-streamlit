import os
import json
from datetime import datetime
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from supabase import create_client, Client
import re

# ✅ Load environment variables FIRST (before other imports that need them)
import env_loader

# ✅ Handle Streamlit import gracefully (it's not needed for backend-only deployment)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    # Create a dummy st.cache_data decorator that does nothing
    print("ℹ️ Streamlit not available (backend mode). Caching disabled.")
    STREAMLIT_AVAILABLE = False
    
    class st:
        """Dummy Streamlit class for backend-only mode"""
        @staticmethod
        def cache_data(ttl=None):
            """No-op decorator when Streamlit is not available"""
            def decorator(func):
                return func
            return decorator

# Import functions from our optimized GitHub services file
from github_services_v2 import search_github_repos as search_github_repos_cached

# Global clients
_supabase_client = None
_openrouter_client = None
_local_memory_cache = {}

# ---------------------------------
# Supabase Client Setup
# ---------------------------------

def get_supabase_client():
    """Lazy-create Supabase client. Return None if credentials missing."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("ℹ️ Supabase not configured. Using local memory fallback.")
        _supabase_client = None
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        print("✅ Supabase client initialized")
        return _supabase_client
    except Exception as e:
        print(f"⚠️ Failed to initialize Supabase: {e}")
        _supabase_client = None
        return None


# ---------------------------------
# OpenRouter Client (using OpenAI SDK)
# ---------------------------------
def get_openrouter_client():
    """Lazy-create OpenRouter/OpenAI client. Return None if API key missing."""
    global _openrouter_client
    if openrouter_api_key:
        print(f"🔑 DEBUG: API Key loaded! Length: {len(openrouter_api_key)}")
        print(f"🔑 DEBUG: Key starts with: {openrouter_api_key[:10]}...")
    else:
        print("❌ DEBUG: OPENROUTER_API_KEY is None or Empty!")
    if _openrouter_client is not None:
        return _openrouter_client

    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not set. AI features will be unavailable.")
        _openrouter_client = None
        return None

    try:
        from openai import OpenAI
        _openrouter_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key)
        print("✅ OpenRouter client initialized")
        return _openrouter_client
    except Exception as e:
        print(f"❌ Failed to initialize OpenRouter: {e}")
        _openrouter_client = None
        return None

# ---------------------------------
# Enhanced AI Response Function
# ----------------------------------
def get_ai_response(messages: list, model: str = "nvidia/nemotron-nano-12b-v2-vl:free", temperature: float = 0.7) -> str:
    """Generic function to get AI response from OpenRouter (safe, non-raising)."""
    client = get_openrouter_client()
    if client is None:
        return "AI service not configured. Please set OPENROUTER_API_KEY environment variable."
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error getting AI response: {e}")
        return f"I encountered an error while calling AI: {str(e)}"

def get_structured_ai_response(messages: list, format_instruction: str = "", model: str = "nvidia/nemotron-nano-12b-v2-vl:free") -> dict:
    """
    Get AI response and safely parse JSON (even if malformed).
    Handles missing commas, markdown fences, and bad line breaks gracefully.
    """
    if format_instruction:
        messages.append({"role": "system", "content": format_instruction})

    response = get_ai_response(messages, model=model, temperature=0.2)

    # --- CLEANUP PHASE ---
    try:
        # Remove markdown code blocks
        cleaned = re.sub(r"^```(json)?|```$", "", response.strip(), flags=re.MULTILINE)
        # Remove comments (// or #)
        cleaned = re.sub(r"(?m)^\s*(//|#).*$", "", cleaned)
        # Fix missing commas between keys
        cleaned = re.sub(r'"}\s*"', '"}, "', cleaned)
        cleaned = cleaned.replace('}"', '},"')
        # Add comma between consecutive keys without one
        cleaned = re.sub(r'"\s*"(?!:)', '", "', cleaned)
        # Remove markdown bullets/asterisks
        cleaned = cleaned.replace("*", "").replace("**", "")
        # Clean blank lines
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)

        # Try parsing directly
        try:
            return json.loads(cleaned)
        except Exception:
            # Fallback: extract inner JSON manually
            json_match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
            if json_match:
                fixed = json_match.group(1)
                return json.loads(fixed)
            raise

    except Exception as e:
        print(f"⚠️ [JSON Parse Error] {e}")
        print("Raw response (truncated):", response[:500])
        return {"error": str(e), "raw_response": response}

# ---------------------------------
# AI-Driven Research Functions
# ---------------------------------

@st.cache_data(ttl=3600)
def auto_research_project(project_info: dict) -> dict:
    """
    Automatically conduct comprehensive research for the project
    using a single, consolidated AI call.
    """
    print("🚀 Triggering consolidated auto-research...")

    research_prompt = f"""
    You are an expert academic researcher.
    A student is working on the following project:
    
    **Project Title:** {project_info.get('title', 'Unknown')}
    **Objectives:** {project_info.get('objective_scope', 'Not specified')}
    **Technology Focus:** {project_info.get('process_description', 'Not specified')}

    **Task:**
    Generate the content for the following 5 sections. Be comprehensive,
    academic, and detailed.

    **Output STRICTLY in valid JSON (no markdown, no comments):**
    {{
        "introduction": "...",
        "literature_review": "...",
        "methodology": "...",
        "system_requirements": {{
            "functional": ["..."],
            "non_functional": ["..."],
            "hardware": ["..."],
            "software": ["..."]
        }},
        "feasibility_analysis": {{
            "technical": "...",
            "economic": "...",
            "operational": "...",
            "schedule": "...",
            "risk": "..."
        }}
    }}
    """

    messages = [{"role": "user", "content": research_prompt}]
    research_results = get_structured_ai_response(messages, model="nvidia/nemotron-nano-12b-v2-vl:free")

    if research_results.get("error"):
        print(f"❌ Error in auto-research: {research_results.get('raw_response', '')[:500]}")
        return {"error": research_results.get('raw_response')}

    # Format results
    formatted_results = {
        "introduction": research_results.get("introduction", ""),
        "literature_review": research_results.get("literature_review", ""),
        "methodology": research_results.get("methodology", ""),
        "system_requirements": json.dumps(research_results.get("system_requirements", {}), indent=2),
        "feasibility_analysis": json.dumps(research_results.get("feasibility_analysis", {}), indent=2)
    }

    print("✅ Auto-research completed successfully.")
    return formatted_results

# ---------------------------------
# Natural Conversation Handler
# ---------------------------------
def handle_natural_conversation(user_input: str, conversation_history: list, session_id: str, current_memory: dict) -> dict:
    """
    Main function to handle natural conversation.
    Consolidates extraction and response into one AI call.
    """
    
    extraction_and_response_prompt = f"""
    You are AURA, an intelligent research assistant.
    Your goal is to talk to a user to help them build an academic project synopsis.
    
    **Current Synopsis Memory:**
    {json.dumps(current_memory, indent=2)}
    
    **Conversation History (last 3 messages):**
    {json.dumps(conversation_history[-3:], indent=2)}
    
    **User's Latest Message:**
    {user_input}

    **Required JSON Output Format (No comments allowed):**
    ```json
    {{
        "updated_memory": {{
            "title": "Update with new info, or keep old",
            "group_details": "Update with new info, or keep old",
            "objective_scope": "Update with new info, or keep old",
            "process_description": "Update with new info, or keep old",
            "resources_limitations": "Update with new info, or keep old",
            "conclusion": "Update with new info, or keep old",
            "references": "Update with new info, or keep old"
        }},
        "updated_fields": ["list", "of", "keys", "you", "updated"],
        "missing_info": ["list", "of", "key", "info", "still_needed"],
        "ai_response": "Your natural, conversational response to the user. Acknowledge what they said and ask ONE good follow-up question."
    }}
    ```
    
    **Rules:**
    -   Fill `updated_memory` by merging new info with the "Current Synopsis Memory".
    -   `updated_fields` should only list keys you *actually changed* or added.
    -   `ai_response` must be conversational, not robotic. Do not mention "synopsis".
    -   **Do not add any comments (like //) inside the JSON response.**
    """
    
    messages = [{"role": "user", "content": extraction_and_response_prompt}]
    
    # Use a fast, small model for chat
    result = get_structured_ai_response(messages, model="nvidia/nemotron-nano-12b-v2-vl:free")
    
    if result.get("error"):
        return {
            "response": f"An error occurred during AI processing. Please try again.",
            "updated_memory": current_memory,
            "updated_fields": [],
            "missing_info": [],
            "auto_research_triggered": False,
            "research_results": {}
        }

    updated_memory = result.get("updated_memory", current_memory)
    updated_fields = result.get("updated_fields", [])
    ai_response = result.get("ai_response", "I'm not sure what to say, can you rephrase?")
    
    # Save updated memory if changes were made
    if updated_fields:
        save_memory(session_id, updated_memory)
        print(f"📝 Updated synopsis fields: {updated_fields}")
    
    # Check if we have enough information for auto-research
    filled_fields = [k for k, v in updated_memory.items() if v and len(str(v).strip()) > 10]
    auto_research_triggered = False
    research_results = {}
    
    # Trigger auto-research when we have sufficient information
    if len(filled_fields) >= 3 and not updated_memory.get("auto_research_done"):
        research_results = auto_research_project(updated_memory)
        if not research_results.get("error"):
            updated_memory["auto_research_done"] = True
            updated_memory["research_results"] = research_results
            save_memory(session_id, updated_memory)
            auto_research_triggered = True
        else:
            ai_response += f"\n\n(Auto-research encountered an issue, but you can continue.)"
    
    return {
        "response": ai_response,
        "updated_memory": updated_memory,
        "updated_fields": updated_fields,
        "missing_info": result.get("missing_info", []),
        "auto_research_triggered": auto_research_triggered,
        "research_results": research_results
    }

# ---------------------------------
# GitHub and Research Integration
# ---------------------------------
def search_github_repos(query: str, limit: int = 10) -> list:
    """
    Pass-through function to our cached GitHub service.
    This exists so app_v2.py only needs to import from services_v2.py
    """
    return search_github_repos_cached(query, limit)

@st.cache_data(ttl=3600)
def search_research_papers(query: str, limit: int = 5) -> list:
    """Enhanced research paper search (Mock)"""
    print(f"📚 Mock searching for papers on: {query}")
    papers = []
    for i in range(min(limit, 3)):
        papers.append(f"📄 **Research Paper {i+1}**: Advanced {query} using Machine Learning Techniques (2024)\n    🎯 Highly relevant to your project approach")
    return papers

@st.cache_data(ttl=3600)
def run_professional_analysis(idea: str, repos: list) -> str:
    """Professional analysis with AI enhancement"""
    analysis_prompt = f"""
    Conduct a professional analysis of this project idea: {idea}
    
    Available similar repositories: {repos[:3]}
    
    Provide analysis covering:
    1. Market Potential and Innovation Level
    2. Technical Complexity Assessment  
    3. Implementation Feasibility
    4. Competitive Landscape
    5. Recommended Technology Stack
    6. Development Timeline Estimation
    
    Give specific, actionable insights.
    """
    
    return get_ai_response(
        [{"role": "user", "content": analysis_prompt}],
        model="nvidia/nemotron-nano-12b-v2-vl:free"
    )

# ---------------------------------
# Enhanced Memory Functions
# ---------------------------------
def load_memory(session_id: str) -> dict:
    client = get_supabase_client()
    if client is None:
        return _local_memory_cache.get(session_id, {})
    try:
        response = client.table("user_sessions").select("research_data").eq("session_id", session_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["research_data"] or {}
        return {}
    except Exception as e:
        print(f"⚠️ Error loading memory from Supabase: {e}")
        return _local_memory_cache.get(session_id, {})

def save_memory(session_id: str, memory: dict, idea: str = None):
    client = get_supabase_client()
    if client is None:
        _local_memory_cache[session_id] = memory
        return
    try:
        data_to_save = {
            "project_idea": idea or memory.get("title", ""),
            "research_data": memory,
            "updated_at": datetime.now().isoformat()
        }
        existing = client.table("user_sessions").select("id").eq("session_id", session_id).execute()
        if existing.data and len(existing.data) > 0:
            client.table("user_sessions").update(data_to_save).eq("session_id", session_id).execute()
        else:
            data_to_save["session_id"] = session_id
            data_to_save["created_at"] = datetime.now().isoformat()
            client.table("user_sessions").insert(data_to_save).execute()
    except Exception as e:
        print(f"⚠️ Error saving memory: {e}")


# ---------------------------------
# Enhanced Synopsis Generation
# ---------------------------------
def generate_comprehensive_synopsis(session_id: str, idea: str = None, repos: list = None, research_data: dict = None, discussion_history: list = None):
    """Generate comprehensive synopsis with AI-enhanced content"""
    
    memory = load_memory(session_id)
    research_results = memory.get("research_results", {})

    # ✅ Create outputs directory in backend folder
    backend_dir = os.path.abspath(os.path.dirname(__file__))
    output_dir = os.path.join(backend_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    # ✅ Generate filename
    filename = f"synopsis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(output_dir, filename)

    print(f"📂 Saving synopsis to: {output_path}")

    # ✅ Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Helper to clean text for ReportLab
    def clean_text(text):
        if not text:
            return ""
        return str(text).replace('\n', '<br/>')

    # Enhanced Title Page
    title = memory.get('title', idea or 'Project Title')
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph("<b>PROJECT SYNOPSIS</b>", styles["Heading1"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Submitted for the partial fulfillment of</b>", styles["Normal"]))
    story.append(Paragraph("<b>BACHELOR OF TECHNOLOGY</b>", styles["Heading2"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph("BRCM COLLEGE OF ENGINEERING & TECHNOLOGY", styles["Heading3"]))
    story.append(Paragraph("BAHAL, BHIWANI - 127028", styles["Normal"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>Submitted by:</b> {clean_text(memory.get('group_details', 'Team Details'))}", styles["Normal"]))
    story.append(PageBreak())

    # Table of Contents
    story.append(Paragraph("<b>TABLE OF CONTENTS</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))
    toc_items = [
        "1. Introduction",
        "2. Literature Review", 
        "3. Problem Statement",
        "4. Objectives and Scope",
        "5. Methodology",
        "6. System Requirements",
        "7. Feasibility Analysis",
        "8. Implementation Plan",
        "9. Expected Outcomes",
        "10. References"
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles["Normal"]))
    story.append(PageBreak())

    # 1. INTRODUCTION
    story.append(Paragraph("<b>1. INTRODUCTION</b>", styles["Heading2"]))
    intro_content = research_results.get("introduction", memory.get("objective_scope", "Project introduction will be detailed here."))
    story.append(Paragraph(clean_text(intro_content), styles["Normal"]))
    story.append(PageBreak())

    # 2. LITERATURE REVIEW
    story.append(Paragraph("<b>2. LITERATURE REVIEW</b>", styles["Heading2"]))
    lit_review = research_results.get("literature_review", "Comprehensive literature review of related work in the domain.")
    story.append(Paragraph(clean_text(lit_review), styles["Normal"]))
    story.append(PageBreak())

    # 3. PROBLEM STATEMENT
    story.append(Paragraph("<b>3. PROBLEM STATEMENT</b>", styles["Heading2"]))
    problem_stmt = memory.get("objective_scope", "The problem statement will outline the key challenges addressed by this project.")
    story.append(Paragraph(clean_text(problem_stmt), styles["Normal"]))
    story.append(PageBreak())

    # 4. OBJECTIVES AND SCOPE
    story.append(Paragraph("<b>4. OBJECTIVES AND SCOPE</b>", styles["Heading2"]))
    objectives = memory.get("objective_scope", "Project objectives and scope will be defined here.")
    story.append(Paragraph(clean_text(objectives), styles["Normal"]))
    story.append(PageBreak())

    # 5. METHODOLOGY
    story.append(Paragraph("<b>5. METHODOLOGY</b>", styles["Heading2"]))
    methodology = research_results.get("methodology", memory.get("process_description", "Detailed methodology and technical approach."))
    story.append(Paragraph(clean_text(methodology), styles["Normal"]))
    story.append(PageBreak())

    # 6. SYSTEM REQUIREMENTS (Formatted)
    story.append(Paragraph("<b>6. SYSTEM REQUIREMENTS</b>", styles["Heading2"]))
    sys_req_raw = research_results.get("system_requirements", {})

    try:
        if isinstance(sys_req_raw, str):
            sys_req_data = json.loads(sys_req_raw)
        else:
            sys_req_data = sys_req_raw

        for category, items in sys_req_data.items():
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<u><b>{category.replace('_', ' ').title()}</b></u>", styles["Heading3"]))
            if isinstance(items, list):
                for item in items:
                    story.append(Paragraph(f"• {clean_text(item)}", styles["Normal"]))
            story.append(Spacer(1, 10))
    except Exception:
        story.append(Paragraph(clean_text(str(sys_req_raw)), styles["Normal"]))
    story.append(PageBreak())

    # 7. FEASIBILITY ANALYSIS (Formatted)
    story.append(Paragraph("<b>7. FEASIBILITY ANALYSIS</b>", styles["Heading2"]))
    feas_raw = research_results.get("feasibility_analysis", {})

    try:
        if isinstance(feas_raw, str):
            feas_data = json.loads(feas_raw)
        else:
            feas_data = feas_raw

        for section, text in feas_data.items():
            story.append(Spacer(1, 8))
            story.append(Paragraph(f"<u><b>{section.title()}</b></u>", styles["Heading3"]))
            story.append(Paragraph(clean_text(text), styles["Normal"]))
            story.append(Spacer(1, 8))
    except Exception:
        story.append(Paragraph(clean_text(str(feas_raw)), styles["Normal"]))
    story.append(PageBreak())

    # 8. IMPLEMENTATION PLAN
    story.append(Paragraph("<b>8. IMPLEMENTATION PLAN</b>", styles["Heading2"]))
    impl_plan = memory.get("process_description", "Detailed implementation plan with timeline and milestones.")
    story.append(Paragraph(clean_text(impl_plan), styles["Normal"]))
    story.append(PageBreak())

    # 9. EXPECTED OUTCOMES
    story.append(Paragraph("<b>9. EXPECTED OUTCOMES</b>", styles["Heading2"]))
    outcomes = memory.get("conclusion", "Expected outcomes and impact of the project.")
    story.append(Paragraph(clean_text(outcomes), styles["Normal"]))
    story.append(PageBreak())

    # 10. REFERENCES
    story.append(Paragraph("<b>10. REFERENCES</b>", styles["Heading2"]))
    references_content = memory.get("references", research_results.get("literature_review", "References will be added based on research conducted."))
    if isinstance(references_content, list):
        references_content = "\n".join(references_content)
    story.append(Paragraph(clean_text(references_content), styles["Normal"]))

    # ✅ Build PDF and return just the filename
    doc.build(story)
    print(f"✅ Synopsis generated: {filename}")
    return filename