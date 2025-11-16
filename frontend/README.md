# AURA Frontend

This directory contains the frontend components for the AURA (AI-Powered Research Assistant) application.

## Files

- `index.html` - Main application interface
- `login.html` - User authentication page
- `app.js` - Main JavaScript application logic
- `style.css` - CSS styling for the application

## Features

### Authentication
- Login page with form validation
- Session management using localStorage
- Automatic redirect to login if not authenticated

### Main Interface
- Chat interface for natural conversation with AURA
- Project progress tracking sidebar
- Quick action buttons for research and analysis
- Synopsis generation and download

### UI Components
- Responsive design with gradient themes
- Animated progress indicators
- Alert boxes for notifications
- Modal-like result displays

## Setup

1. Ensure the backend API server is running on `http://localhost:5000`
2. Open `login.html` in a web browser to start
3. Login with any username and password (demo mode)
4. Access the main application interface

## Development

The frontend uses vanilla JavaScript with no external dependencies for maximum compatibility. All state is managed through localStorage for persistence across sessions.

## API Integration

The frontend communicates with the backend through REST API calls to:
- `/api/conversation` - Handle natural language conversations
- `/api/github-search` - Search GitHub repositories
- `/api/research-papers` - Find academic papers
- `/api/professional-analysis` - Generate project analysis
- `/api/generate-synopsis` - Create PDF synopses
- `/api/ai-suggestions` - Get AI-powered suggestions
