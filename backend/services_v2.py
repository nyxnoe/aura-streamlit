print("DEBUG: services_v2.py loaded")
import sys
print("sys.path:", sys.path)
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
_ai_provider = None  # "openai" or "openrouter"
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
# AI Client Setup (OpenAI or OpenRouter)
# ---------------------------------
def get_ai_client():
    """Create OpenRouter AI client."""
    global _openrouter_client, _ai_provider
    if _openrouter_client is not None:
        return _openrouter_client

    if env_loader.OPENROUTER_API_KEY:
        print(f"✅ Using OpenRouter API Key (length: {len(env_loader.OPENROUTER_API_KEY)})")
        from openai import OpenAI
        _openrouter_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=env_loader.OPENROUTER_API_KEY)
        _ai_provider = "openrouter"
        print("✅ OpenRouter client initialized")
        return _openrouter_client

    print("❌ OpenRouter API key not available. AI features will be unavailable.")
    _openrouter_client = None
    _ai_provider = None
    return None

# ---------------------------------
# Enhanced AI Response Function
# ----------------------------------
def get_ai_response(messages: list, model: str = None, temperature: float = 0.7) -> str:
    """Get AI response from OpenRouter only. No OpenAI fallback."""
    if model is None:
        model = env_loader.AI_MODEL_PRIMARY
    
    client = get_ai_client()
    if client is None:
        return "AI service not configured. Please set OPENROUTER_API_KEY environment variable."
    
    import time
    start_time = time.time()
    print(f"🤖 Calling OpenRouter AI model: {model}...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            timeout=15
        )
        
        duration = time.time() - start_time
        print(f"⏱️ AI response received in {duration:.2f}s")
        
        if not response or not hasattr(response, 'choices') or not response.choices:
            print(f"⚠️ Empty response from model {model}")
            return "AI returned an empty response."
            
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error getting AI response: {e}")
        print(f"❌ Error type: {type(e)}")
        # Try fallback model only once
        if model != env_loader.AI_MODEL_FALLBACK:
             print("🔄 Trying fallback model...")
             return get_ai_response(messages, model=env_loader.AI_MODEL_FALLBACK, temperature=temperature)
        return f"I encountered an error while calling AI: {str(e)}"
        return f"I encountered an error while calling AI: {str(e)}"

def get_structured_ai_response(messages: list, format_instruction: str = "", model: str = None) -> dict:
    if model is None:
        model = env_loader.AI_MODEL_PRIMARY
    print(f"DEBUG: get_structured_ai_response using model: {model}")
    """
    Get AI response and safely parse JSON.
    """
    if format_instruction:
        messages.append({"role": "system", "content": format_instruction})

    response = get_ai_response(messages, model=model, temperature=0.1)
    
    # If the response itself is an error message, don't try to parse it as JSON
    if response.startswith("I encountered an error") or response.startswith("AI returned"):
        return {"error": response}

    try:
        # 1. Attempt to find JSON block with regex
        json_pattern = r'(\{[\s\S]*\})'
        match = re.search(json_pattern, response)
        
        if match:
            json_str = match.group(1)
            json_str = re.sub(r'^```(json)?|```$', '', json_str.strip(), flags=re.MULTILINE)
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                json_str = re.sub(r',\s*\}', '}', json_str)
                json_str = re.sub(r',\s*\]', ']', json_str)
                return json.loads(json_str)
        
        return json.loads(response.strip())
    except Exception as e:
        print(f"⚠️ [JSON Parse Error] {e}")
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
    Generate comprehensive, detailed, academic-level content for the following 5 sections.
    Each section should be at least 250-400 words, with specific technical details,
    references to existing technologies, and thorough analysis.

    **Output STRICTLY in valid JSON (no markdown, no comments):**
    {{
        "introduction": "Detailed introduction with background, motivation, and significance (250+ words)",
        "literature_review": "Comprehensive review of existing literature, related work, and gap analysis (300+ words)",
        "methodology": "Detailed technical methodology, algorithms, tools, and implementation approach (300+ words)",
        "system_requirements": {{
            "functional": ["Detailed list of functional requirements"],
            "non_functional": ["Detailed list of non-functional requirements"],
            "hardware": ["Specific hardware requirements with specifications"],
            "software": ["Specific software stack, libraries, frameworks"]
        }},
        "feasibility_analysis": {{
            "technical": "Detailed technical feasibility analysis (200+ words)",
            "economic": "Economic feasibility with cost estimates (200+ words)",
            "operational": "Operational feasibility analysis (200+ words)",
            "schedule": "Project timeline and scheduling analysis (200+ words)",
            "risk": "Risk assessment and mitigation strategies (200+ words)"
        }}
    }}
    """

    messages = [{"role": "user", "content": research_prompt}]
    research_results = get_structured_ai_response(messages)

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
    You are AURA, a research assistant. Help the user build an academic project synopsis.
    
    Current Memory: {json.dumps(current_memory)}
    Last Messages: {json.dumps(conversation_history[-2:])}
    User: {user_input}

    Output valid JSON ONLY (no extra text):
    {{
        "updated_memory": {{
            "title": "Project title (be specific and academic)",
            "group_details": "Team member names and roles (e.g., 'John Doe - Team Lead, Jane Smith - Developer')",
            "objective_scope": "Detailed objectives and scope (at least 150 words, include specific goals, boundaries, and deliverables)",
            "process_description": "Detailed technical process and methodology (at least 150 words, include technologies, algorithms, workflow)",
            "resources_limitations": "Resources needed and limitations (at least 100 words, include hardware, software, time, budget constraints)",
            "conclusion": "Project conclusion and expected outcomes (at least 100 words, include benefits, impact, future work)",
            "references": "Key references and sources (list 3-5 academic or technical references)"
        }},
        "updated_fields": ["key1", "key2"],
        "missing_info": ["info1", "info2"],
        "ai_response": "Natural conversational response + ONE follow-up question."
    }}
    """
    
    messages = [{"role": "user", "content": extraction_and_response_prompt}]
    
    # Use a fast, small model for chat
    result = get_structured_ai_response(messages)
    
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
        model="tngtech/deepseek-r1t2-chimera:free"
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
        print(f"⚠️ Error saving memory: {e}. Retrying...")
        import time
        time.sleep(1)  # Wait 1 second
        try:
            if existing.data and len(existing.data) > 0:
                client.table("user_sessions").update(data_to_save).eq("session_id", session_id).execute()
            else:
                data_to_save["session_id"] = session_id
                data_to_save["created_at"] = datetime.now().isoformat()
                client.table("user_sessions").insert(data_to_save).execute()
            print("✅ Memory saved on retry")
        except Exception as e2:
            print(f"⚠️ Retry failed: {e2}. Saving locally.")
            _local_memory_cache[session_id] = memory


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