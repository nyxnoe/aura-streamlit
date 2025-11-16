# AURA - AI-Powered Research Assistant

AURA (AI-Powered Research Assistant) is an intelligent web application that helps students develop B.Tech project ideas from concept to complete documentation through natural conversation and automated research.

## 🏗️ Project Structure

```
aura-streamlit/
├── frontend/           # Frontend web application
│   ├── index.html      # Main application interface
│   ├── login.html      # Authentication page
│   ├── app.js          # JavaScript application logic
│   ├── style.css       # CSS styling
│   └── README.md       # Frontend documentation
├── backend/            # Python Flask API server
│   ├── api_server.py  # Main API server
│   ├── app_v2.py       # Core application logic
│   ├── services_v2.py  # API services
│   ├── github_services_v2.py  # GitHub integration
│   └── test.py         # Test scripts
├── config/             # Configuration and dependencies
│   ├── requirements.txt # Python dependencies
│   ├── .env           # Environment variables
│   ├── setup.md       # Setup instructions
│   ├── README.md      # Project documentation
│   └── check_env.py   # Environment checker
├── outputs/            # Generated synopsis PDFs
├── scripts/            # Utility scripts
│   ├── open_frontend.bat
│   ├── run_aura.bat
│   └── start_server.bat
└── README.md          # This file
```

## ✨ Features

### 🤖 Intelligent Conversation
- Natural language processing for project development
- Context-aware responses and memory management
- Intelligent question asking to gather requirements

### 🔬 Automated Research
- GitHub repository search and analysis
- Academic paper discovery
- Professional project analysis
- AI-powered suggestions

### 📄 Synopsis Generation
- Automated PDF generation following academic standards
- B.Tech project format compliance
- Professional formatting and layout

### 🎯 Progress Tracking
- Real-time project completion status
- Visual progress indicators
- Stage-based development guidance

### 🔐 User Authentication
- Simple login system with session management
- Secure session handling
- User data persistence

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Web browser
- Internet connection for API calls

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd aura-streamlit
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r config/requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `config/.env.example` to `config/.env`
   - Add your API keys (OpenAI, GitHub tokens, etc.)

4. **Run the application:**
   ```bash
   # Option 1: Use the batch script
   scripts\run_aura.bat

   # Option 2: Manual startup
   # Terminal 1: Start backend
   python backend/api_server.py

   # Terminal 2: Open frontend
   start frontend/login.html
   ```

5. **Access the application:**
   - Open `http://localhost:3000` (if using live server)
   - Or open `frontend/login.html` directly in browser

## 📖 Usage

1. **Login:** Use any username and password to access the system
2. **Start Conversation:** Tell AURA about your project idea naturally
3. **Gather Information:** Answer AURA's questions to build your project profile
4. **Auto-Research:** Let AURA automatically research similar projects
5. **Generate Synopsis:** Download your professional PDF synopsis

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the `config/` directory:

```env
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
FLASK_ENV=development
FLASK_DEBUG=True
```

### API Endpoints

The backend provides the following endpoints:
- `POST /api/conversation` - Handle natural conversations
- `GET /api/github-search` - Search GitHub repositories
- `GET /api/research-papers` - Find research papers
- `POST /api/professional-analysis` - Generate analysis
- `POST /api/generate-synopsis` - Create PDF synopses
- `POST /api/ai-suggestions` - Get AI suggestions

## 🛠️ Development

### Frontend Development
- Uses vanilla JavaScript and CSS
- No build process required
- Responsive design for mobile and desktop

### Backend Development
- Flask-based REST API
- Modular service architecture
- Easy to extend with new features

### Adding New Features
1. Add API endpoint in `backend/services_v2.py`
2. Implement frontend logic in `frontend/app.js`
3. Update UI in `frontend/index.html` if needed

## 📊 Project Status

- ✅ Frontend authentication system
- ✅ Chat interface with AURA
- ✅ Progress tracking and visualization
- ✅ GitHub integration
- ✅ Research paper search
- ✅ Professional analysis
- ✅ Synopsis PDF generation
- ✅ Session management
- ✅ Responsive design

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is developed for BRCM College of Engineering & Technology.

## 🙏 Acknowledgments

- Built with Flask, OpenAI GPT, and modern web technologies
- Designed for B.Tech project development workflow
- Inspired by the need for intelligent academic assistance

## 📞 Support

For issues or questions:
1. Check the setup documentation in `config/setup.md`
2. Review the troubleshooting guide
3. Open an issue in the repository

---

**Made with ❤️ for Students at BRCM College of Engineering & Technology**
