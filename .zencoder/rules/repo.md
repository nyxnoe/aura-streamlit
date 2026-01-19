---
description: Repository Information Overview
alwaysApply: true
---

# AURA - AI-Powered Research Assistant Information

## Repository Summary
AURA (AI-Powered Research Assistant) is an intelligent web application designed to help B.Tech students develop project ideas into professional documentation. It utilizes natural language processing for project development, automated research (GitHub, research papers), and standard-compliant PDF synopsis generation.

## Repository Structure
The repository is organized into several key components:
- **frontend/**: Vanilla JavaScript, HTML, and CSS web application for the user interface.
- **backend/**: Flask-based REST API server handling the core logic, integrations, and synopsis generation.
- **ai-services/**: A Streamlit-based alternative or standalone interface providing similar AI-driven research capabilities.
- **config/**: Centralized configuration, environment variables, and dependency definitions.
- **scripts/**: Platform-specific (Shell and Batch) scripts for automating application startup.
- **outputs/**: Storage for generated academic synopsis PDFs.

### Main Repository Components
- **Web Frontend**: Entry point at `frontend/login.html`, communicates with the Flask backend.
- **Flask Backend**: Entry point at `backend/api_server.py`, provides REST endpoints for conversation and research.
- **Streamlit App**: Entry point at `ai-services/app_v2.py`, offers an integrated UI for research and analysis.

## Projects

### Backend (Flask API)
**Configuration File**: `backend/requirements.txt`

#### Language & Runtime
**Language**: Python  
**Version**: 3.8+ (3.13.4 in production)  
**Build System**: pip  
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- `flask`: Web framework
- `openai`: AI model integration
- `reportlab`: PDF generation
- `supabase`: Database/Persistence
- `requests`: External API calls

#### Build & Installation
```bash
# Install dependencies from root
pip install -r config/requirements.txt

# Start the backend server
python backend/api_server.py
```

#### Testing
**Framework**: Manual/Script-based
**Test Location**: `backend/test.py`
**Run Command**:
```bash
python backend/test.py
```

### AI-Services (Streamlit App)
**Configuration File**: `ai-services/requirements.txt`

#### Language & Runtime
**Language**: Python  
**Version**: 3.8+  
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- `streamlit`: Dashboard/App framework
- `openai`: AI integration
- `supabase`: Persistence layer
- `reportlab`: PDF generation

#### Build & Installation
```bash
# Install dependencies
pip install -r ai-services/requirements.txt

# Run the Streamlit application
streamlit run ai-services/app_v2.py
```

### Frontend (Web App)
**Type**: Static Web Application

#### Specification & Tools
**Type**: HTML/JS/CSS  
**Required Tools**: Web Browser

#### Key Resources
**Main Files**:
- `frontend/index.html`: Main interface
- `frontend/login.html`: Authentication entry point
- `frontend/app.js`: Application logic and API integration

#### Usage & Operations
**Key Commands**:
```bash
# Open the application
start frontend/login.html
```
**Integration Points**:
Connects to the Backend API at `http://localhost:5000` for all AI and research features.
