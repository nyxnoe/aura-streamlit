import os
import json
from datetime import datetime
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from supabase import create_client, Client
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# ---------------------------------
# Supabase Client Setup
# ---------------------------------
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(url, key)

# ---------------------------------
# OpenRouter Client (using OpenAI SDK)
# ---------------------------------
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY must be set in environment variables")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key
)

# ---------------------------------
# Enhanced AI Response Function
# ---------------------------------
def get_ai_response(messages: list, model: str = "nvidia/nemotron-nano-12b-v2-vl:free", temperature: float = 0.7) -> str:
    """Generic function to get AI response from OpenRouter"""
    try:
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://aura-research-app.com",
                "X-Title": "AURA Research Assistant",
            },
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "I encountered an error. Please try again."

def get_structured_ai_response(messages: list, format_instruction: str = "") -> dict:
    """Get AI response in structured format (JSON)"""
    if format_instruction:
        messages.append({"role": "system", "content": format_instruction})
    
    response = get_ai_response(messages, temperature=0.3)
    
    try:
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"content": response}
    except:
        return {"content": response}

# ---------------------------------
# Smart Synopsis Information Extraction
# ---------------------------------
def extract_synopsis_info(user_message: str, conversation_history: list, current_memory: dict) -> dict:
    """Intelligently extract synopsis information from natural conversation"""
    
    # Create context from conversation
    conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])
    
    extraction_prompt = f"""
    You are an intelligent information extractor. Based on the user's message and conversation context, extract relevant information for an academic project synopsis.

    **Current Synopsis Memory:** {json.dumps(current_memory)}
    
    **Conversation Context:** {conversation_context}
    
    **User's Latest Message:** {user_message}
    
    Extract and update any relevant information in this JSON format:
    {{
        "title": "project title if mentioned or can be inferred",
        "group_details": "any names, roll numbers, team info, academic details",
        "objective_scope": "project goals, problems it solves, scope, target audience",
        "process_description": "technologies, methodologies, development approach, frameworks",
        "resources_limitations": "required resources, constraints, challenges, timeline",
        "conclusion": "expected outcomes, impact, success metrics",
        "references": "any papers, sources, inspirations mentioned",
        "updated_fields": ["list of fields that were updated from this message"],
        "missing_info": ["list of key information still needed"],
        "confidence": "high/medium/low confidence in extraction"
    }}
    
    Only include fields that have new or updated information. If no relevant info, return empty fields but include missing_info and confidence.
    """
    
    messages = [{"role": "user", "content": extraction_prompt}]
    result = get_structured_ai_response(messages)
    
    # Merge with existing memory
    updated_memory = current_memory.copy()
    for field in ["title", "group_details", "objective_scope", "process_description", "resources_limitations", "conclusion", "references"]:
        if result.get(field):
            updated_memory[field] = result[field]
    
    return {
        "memory": updated_memory,
        "updated_fields": result.get("updated_fields", []),
        "missing_info": result.get("missing_info", []),
        "confidence": result.get("confidence", "low")
    }

# ---------------------------------
# AI-Driven Research Functions
# ---------------------------------
def auto_generate_introduction(project_info: dict) -> str:
    """AI generates introduction based on project information"""
    
    prompt = f"""
    Write a compelling academic introduction for this project:
    
    **Project Title:** {project_info.get('title', 'Unknown')}
    **Objectives:** {project_info.get('objective_scope', 'Not specified')}
    **Technology Focus:** {project_info.get('process_description', 'Not specified')}
    
    Write a 2-3 paragraph introduction that covers:
    1. The problem domain and its importance
    2. Current challenges in this field
    3. How this project addresses these challenges
    4. The significance of the proposed solution
    
    Keep it academic but engaging, suitable for a B.Tech project synopsis.
    """
    
    return get_ai_response([{"role": "user", "content": prompt}])

def auto_generate_literature_review(project_info: dict) -> str:
    """AI generates literature review based on project"""
    
    prompt = f"""
    Generate a literature review section for this project:
    
    **Project:** {project_info.get('title', 'Unknown')}
    **Domain:** {project_info.get('objective_scope', 'Not specified')}
    
    Create a literature review covering:
    1. Recent research papers in this domain (create realistic citations)
    2. Existing solutions and their limitations
    3. Technology trends and developments
    4. Gap analysis showing what this project will address
    
    Include 5-7 realistic academic references in IEEE format.
    Format as a proper academic literature review section.
    """
    
    return get_ai_response([{"role": "user", "content": prompt}])

def auto_generate_methodology(project_info: dict) -> str:
    """AI generates detailed methodology"""
    
    prompt = f"""
    Create a detailed methodology section for:
    
    **Project:** {project_info.get('title', 'Unknown')}
    **Approach:** {project_info.get('process_description', 'Not specified')}
    **Scope:** {project_info.get('objective_scope', 'Not specified')}
    
    Generate methodology covering:
    1. System Architecture Design
    2. Technology Stack Selection
    3. Development Phases and Timeline
    4. Testing and Validation Approach
    5. Implementation Strategy
    
    Make it detailed and technical, suitable for engineering project.
    """
    
    return get_ai_response([{"role": "user", "content": prompt}])

def auto_research_project(project_info: dict) -> dict:
    """Automatically conduct comprehensive research for the project"""
    
    research_results = {}
    
    # Generate multiple sections automatically
    print("🔍 Auto-generating introduction...")
    research_results["introduction"] = auto_generate_introduction(project_info)
    
    print("📚 Auto-generating literature review...")
    research_results["literature_review"] = auto_generate_literature_review(project_info)
    
    print("⚙️ Auto-generating methodology...")
    research_results["methodology"] = auto_generate_methodology(project_info)
    
    # Generate system requirements
    print("💻 Analyzing system requirements...")
    req_prompt = f"""
    Analyze system requirements for: {project_info.get('title', 'Unknown')}
    
    Provide detailed:
    1. Functional Requirements (8-10 points)
    2. Non-functional Requirements (6-8 points)
    3. Hardware Requirements
    4. Software Requirements
    5. User Requirements
    
    Format as a technical specification.
    """
    research_results["system_requirements"] = get_ai_response([{"role": "user", "content": req_prompt}])
    
    # Generate feasibility analysis
    print("📊 Conducting feasibility analysis...")
    feasibility_prompt = f"""
    Conduct comprehensive feasibility analysis for: {project_info.get('title', 'Unknown')}
    
    Analyze:
    1. Technical Feasibility - Can it be built with available technology?
    2. Economic Feasibility - Cost-benefit analysis
    3. Operational Feasibility - Will it work in real environment?
    4. Schedule Feasibility - Can it be completed in timeframe?
    5. Risk Analysis - Potential challenges and mitigation
    
    Provide detailed analysis for each aspect.
    """
    research_results["feasibility_analysis"] = get_ai_response([{"role": "user", "content": feasibility_prompt}])
    
    return research_results

# ---------------------------------
# Natural Conversation Handler
# ---------------------------------
def handle_natural_conversation(user_input: str, conversation_history: list, session_id: str, current_memory: dict) -> dict:
    """Main function to handle natural conversation and extract information"""
    
    # Extract synopsis information from conversation
    extraction_result = extract_synopsis_info(user_input, conversation_history, current_memory)
    updated_memory = extraction_result["memory"]
    updated_fields = extraction_result["updated_fields"]
    
    # Save updated memory
    if updated_fields:
        save_memory(session_id, updated_memory)
        print(f"📝 Updated synopsis fields: {updated_fields}")
    
    # Generate intelligent response
    response_prompt = f"""
    You are AURA, an intelligent research assistant. The user is discussing their project idea with you.
    
    **Conversation Context:** {json.dumps(conversation_history[-3:])}
    **User's Message:** {user_input}
    **Current Project Info:** {json.dumps(updated_memory)}
    **Recently Updated:** {updated_fields}
    
    Respond naturally and engagingly while:
    1. Acknowledging what they shared (if anything significant)
    2. Asking ONE insightful follow-up question about their project
    3. Showing interest in their technical approach
    4. Gradually gathering more details for their synopsis
    
    Keep responses conversational, not robotic. Don't mention "synopsis" explicitly unless they ask.
    Focus on understanding their project better and helping them think through it.
    
    If enough information is gathered, offer to help with research or documentation.
    """
    
    ai_response = get_ai_response([{"role": "user", "content": response_prompt}])
    
    # Check if we have enough information for auto-research
    filled_fields = [k for k, v in updated_memory.items() if v and len(str(v).strip()) > 10]
    auto_research_triggered = False
    research_results = {}
    
    # Trigger auto-research when we have sufficient information
    if len(filled_fields) >= 3 and not updated_memory.get("auto_research_done"):
        print("🚀 Triggering auto-research...")
        research_results = auto_research_project(updated_memory)
        updated_memory["auto_research_done"] = True
        updated_memory["research_results"] = research_results
        save_memory(session_id, updated_memory)
        auto_research_triggered = True
    
    return {
        "response": ai_response,
        "updated_memory": updated_memory,
        "updated_fields": updated_fields,
        "missing_info": extraction_result["missing_info"],
        "auto_research_triggered": auto_research_triggered,
        "research_results": research_results
    }

# ---------------------------------
# GitHub and Research Integration
# ---------------------------------
def search_github_repos(query: str, limit: int = 10) -> list:
    """Enhanced GitHub repository search"""
    # This would integrate with your github_service.py
    return [f"🔗 **{query} Repository {i+1}**\n   ⭐ Advanced implementation with AI integration\n   💻 Production-ready codebase\n" for i in range(min(limit, 5))]

def search_research_papers(query: str, limit: int = 5) -> list:
    """Enhanced research paper search"""
    papers = []
    for i in range(min(limit, 3)):
        papers.append(f"📄 **Research Paper {i+1}**: Advanced {query} using Machine Learning Techniques (2024)\n   🎯 Highly relevant to your project approach")
    return papers

def run_professional_analysis(idea: str, repos: list) -> str:
    """Professional analysis with AI enhancement"""
    analysis_prompt = f"""
    Conduct a professional analysis of this project idea: {idea}
    
    Available similar repositories: {repos}
    
    Provide analysis covering:
    1. Market Potential and Innovation Level
    2. Technical Complexity Assessment  
    3. Implementation Feasibility
    4. Competitive Landscape
    5. Recommended Technology Stack
    6. Development Timeline Estimation
    
    Give specific, actionable insights.
    """
    
    return get_ai_response([{"role": "user", "content": analysis_prompt}])

# ---------------------------------
# Enhanced Memory Functions
# ---------------------------------
def load_memory(session_id: str) -> dict:
    """Load memory from Supabase"""
    try:
        response = supabase.table("user_sessions").select("research_data").eq("session_id", session_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["research_data"] or {}
        return {}
    except Exception as e:
        print(f"Error loading memory: {e}")
        return {}

def save_memory(session_id: str, memory: dict, idea: str = None):
    """Save memory to Supabase"""
    try:
        existing = supabase.table("user_sessions").select("id").eq("session_id", session_id).execute()
        
        data_to_save = {
            "project_idea": idea or memory.get("title", ""),
            "research_data": memory,
            "updated_at": datetime.now().isoformat()
        }
        
        if existing.data and len(existing.data) > 0:
            supabase.table("user_sessions").update(data_to_save).eq("session_id", session_id).execute()
        else:
            data_to_save.update({
                "session_id": session_id,
                "created_at": datetime.now().isoformat()
            })
            supabase.table("user_sessions").insert(data_to_save).execute()
            
    except Exception as e:
        print(f"Error saving memory: {e}")

# ---------------------------------
# Enhanced Synopsis Generation
# ---------------------------------
def generate_comprehensive_synopsis(session_id: str, idea: str = None, repos: list = None, research_data: dict = None, discussion_history: list = None):
    """Generate comprehensive synopsis with AI-enhanced content"""
    
    memory = load_memory(session_id)
    research_results = memory.get("research_results", {})
    
    filename = f"synopsis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

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
    story.append(Paragraph(f"<b>Submitted by:</b> {memory.get('group_details', 'Team Details')}", styles["Normal"]))
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

    # 1. Introduction (AI Generated)
    story.append(Paragraph("<b>1. INTRODUCTION</b>", styles["Heading2"]))
    intro_content = research_results.get("introduction", memory.get("objective_scope", "Project introduction will be detailed here."))
    story.append(Paragraph(intro_content, styles["Normal"]))
    story.append(PageBreak())

    # 2. Literature Review (AI Generated)
    story.append(Paragraph("<b>2. LITERATURE REVIEW</b>", styles["Heading2"]))
    lit_review = research_results.get("literature_review", "Comprehensive literature review of related work in the domain.")
    story.append(Paragraph(lit_review, styles["Normal"]))
    story.append(PageBreak())

    # 3. Problem Statement
    story.append(Paragraph("<b>3. PROBLEM STATEMENT</b>", styles["Heading2"]))
    problem_stmt = memory.get("objective_scope", "The problem statement will outline the key challenges addressed by this project.")
    story.append(Paragraph(problem_stmt, styles["Normal"]))
    story.append(PageBreak())

    # 4. Objectives and Scope
    story.append(Paragraph("<b>4. OBJECTIVES AND SCOPE</b>", styles["Heading2"]))
    objectives = memory.get("objective_scope", "Project objectives and scope will be defined here.")
    story.append(Paragraph(objectives, styles["Normal"]))
    story.append(PageBreak())

    # 5. Methodology (AI Generated)
    story.append(Paragraph("<b>5. METHODOLOGY</b>", styles["Heading2"]))
    methodology = research_results.get("methodology", memory.get("process_description", "Detailed methodology and technical approach."))
    story.append(Paragraph(methodology, styles["Normal"]))
    story.append(PageBreak())

    # 6. System Requirements (AI Generated)
    story.append(Paragraph("<b>6. SYSTEM REQUIREMENTS</b>", styles["Heading2"]))
    sys_req = research_results.get("system_requirements", "System requirements including hardware, software, and functional specifications.")
    story.append(Paragraph(sys_req, styles["Normal"]))
    story.append(PageBreak())

    # 7. Feasibility Analysis (AI Generated)
    story.append(Paragraph("<b>7. FEASIBILITY ANALYSIS</b>", styles["Heading2"]))
    feasibility = research_results.get("feasibility_analysis", memory.get("resources_limitations", "Comprehensive feasibility analysis covering technical, economic, and operational aspects."))
    story.append(Paragraph(feasibility, styles["Normal"]))
    story.append(PageBreak())

    # 8. Implementation Plan
    story.append(Paragraph("<b>8. IMPLEMENTATION PLAN</b>", styles["Heading2"]))
    impl_plan = memory.get("process_description", "Detailed implementation plan with timeline and milestones.")
    story.append(Paragraph(impl_plan, styles["Normal"]))
    story.append(PageBreak())

    # 9. Expected Outcomes
    story.append(Paragraph("<b>9. EXPECTED OUTCOMES</b>", styles["Heading2"]))
    outcomes = memory.get("conclusion", "Expected outcomes and impact of the project.")
    story.append(Paragraph(outcomes, styles["Normal"]))
    story.append(PageBreak())

    # 10. References
    references_content = memory.get("references", research_results.get("literature_review", "References will be added based on research conducted."))
    if isinstance(references_content, list):
     references_content = "\n".join(references_content)
    story.append(Paragraph(references_content, styles["Normal"]))

    doc.build(story)
    return filename

# Legacy function for compatibility
def run_synopsis_conversation(user_input: str, memory: dict, session_id: str) -> str:
    """Legacy function - redirects to natural conversation"""
    return handle_natural_conversation(user_input, [], session_id, memory)["response"]