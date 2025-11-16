# AURA - Intelligent Research Assistant (Web Frontend)

A modern web-based frontend for AURA, the AI-powered research assistant that helps students create comprehensive academic project synopses.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required environment variables (see `.env` setup below)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory with:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
SUPABASE_URL=your_supabase_url_here  # Optional
SUPABASE_KEY=your_supabase_key_here  # Optional
```

### 3. Start the Backend API Server
```bash
python api_server.py
```
The server will start on `http://localhost:5000`

### 4. Open the Frontend
Simply open `index.html` in your web browser:
- Double-click `index.html` in your file explorer, or
- Right-click `index.html` → Open with → Your preferred browser

## 📁 Project Structure

```
aura-streamlit/
├── index.html          # Main web application
├── style.css           # Styling and animations
├── app.js             # Frontend JavaScript logic
├── api_server.py      # Flask API backend
├── services_v2.py      # Core AI services
├── github_services_v2.py  # GitHub integration
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
└── README.md          # This file
```

## 🎯 Features

### Core Functionality
- **Natural Conversation**: Chat naturally about your project ideas
- **Automatic Research**: AI-powered research when enough information is gathered
- **Progress Tracking**: Visual progress bar showing synopsis completion
- **Quick Actions**: Find similar projects, research papers, professional analysis

### Synopsis Generation
- **PDF Export**: Generate professional academic synopsis documents
- **Comprehensive Content**: Includes introduction, literature review, methodology, requirements, feasibility analysis
- **Academic Standards**: Follows B.Tech project requirements

## 🔧 API Endpoints

The backend provides these endpoints:

- `POST /api/conversation` - Handle natural conversation
- `GET /api/github-search` - Search GitHub repositories
- `GET /api/research-papers` - Search research papers
- `POST /api/professional-analysis` - Run professional analysis
- `POST /api/generate-synopsis` - Generate synopsis PDF
- `POST /api/ai-suggestions` - Get AI suggestions
- `GET /api/download/<filename>` - Download generated files

## 🖥️ Usage Instructions

1. **Start the Backend**: Run `python api_server.py`
2. **Open Frontend**: Open `index.html` in your browser
3. **Begin Conversation**: Tell AURA about your project idea naturally
4. **Fill Information**: Answer questions to build your synopsis
5. **Auto-Research**: Research triggers automatically when ready
6. **Generate Synopsis**: Click "Generate Synopsis" when 3+ sections are complete
7. **Download PDF**: Download your professional synopsis document

## 🛠️ Troubleshooting

### Backend Won't Start
- Check if all dependencies are installed: `pip install -r requirements.txt`
- Verify your `.env` file has the correct API keys
- Ensure no other service is using port 5000

### Frontend Not Loading
- Make sure the backend is running on port 5000
- Check browser console for JavaScript errors
- Try refreshing the page

### PDF Download Issues
- PDFs are generated in the same directory as `api_server.py`
- Check file permissions if downloads fail
- Browser may flag local downloads as unsafe - allow them

### AI Features Not Working
- Verify `OPENROUTER_API_KEY` is set correctly
- Check internet connection for API calls
- Some features may be limited without proper API keys

## 🔐 Environment Variables

### Required
- `OPENROUTER_API_KEY`: Your OpenRouter API key for AI features

### Optional
- `SUPABASE_URL`: Supabase database URL for persistent storage
- `SUPABASE_KEY`: Supabase API key for database access

## 📊 System Requirements

- **Python**: 3.8 or higher
- **Browser**: Modern browser with JavaScript enabled
- **Internet**: Required for AI features and external API calls
- **Storage**: ~100MB free space for generated PDFs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is developed for BRCM College of Engineering & Technology.

## 🆘 Support

For issues or questions:
1. Check this README first
2. Verify your environment setup
3. Check the browser console for errors
4. Ensure all dependencies are installed

---

**Made with ❤️ for Students**
