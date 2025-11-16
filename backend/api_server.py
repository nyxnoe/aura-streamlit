from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime

# ✅ Load environment variables first (before other imports)
import env_loader

from services_v2 import (
    handle_natural_conversation,
    search_github_repos,
    run_professional_analysis,
    search_research_papers,
    generate_comprehensive_synopsis,
    load_memory,
    save_memory,
    get_ai_response
)

app = Flask(__name__)

# ✅ Configure CORS properly
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],  # Update with your frontend domain in production
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
})

@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "service": "AURA Backend API",
        "version": "2.0",
        "endpoints": [
            "POST /api/conversation",
            "GET /api/github-search",
            "GET /api/research-papers",
            "POST /api/professional-analysis",
            "POST /api/generate-synopsis",
            "GET /api/download/<filename>",
            "POST /api/ai-suggestions"
        ]
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check for monitoring"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/conversation', methods=['POST'])
def conversation():
    try:
        data = request.json
        result = handle_natural_conversation(
            data['prompt'],
            data['conversation_history'],
            data['session_id'],
            data['synopsis_memory']
        )
        return jsonify(result)
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        print(f"Error in conversation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/github-search', methods=['GET'])
def github_search():
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        limit = int(request.args.get('limit', 5))
        repos = search_github_repos(query, limit)
        return jsonify(repos)
    except ValueError:
        return jsonify({'error': 'Invalid limit parameter'}), 400
    except Exception as e:
        print(f"Error in github search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research-papers', methods=['GET'])
def research_papers():
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        limit = int(request.args.get('limit', 5))
        papers = search_research_papers(query, limit)
        return jsonify(papers)
    except ValueError:
        return jsonify({'error': 'Invalid limit parameter'}), 400
    except Exception as e:
        print(f"Error in research papers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/professional-analysis', methods=['POST'])
def professional_analysis():
    try:
        data = request.json
        if not data or 'title' not in data:
            return jsonify({'error': 'Missing required field: title'}), 400
        
        analysis = run_professional_analysis(
            data['title'], 
            data.get('repos', [])
        )
        return jsonify({'analysis': analysis})
    except Exception as e:
        print(f"Error in professional analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-synopsis', methods=['POST'])
def generate_synopsis():
    try:
        data = request.get_json()
        session_id = data.get("session_id", "default_session")
        idea = data.get("idea", "")
        research_data = data.get("research_data", {})

        print(f"📝 Generating synopsis for session: {session_id}")
        
        # ✅ Call with proper parameters
        filename = generate_comprehensive_synopsis(
            session_id=session_id,
            idea=idea,
            research_data=research_data
        )

        print(f"✅ Synopsis generated: {filename}")
        
        return jsonify({
            "message": "Synopsis generated successfully.",
            "filename": filename,
            "download_url": f"/api/download/{filename}"
        })

    except Exception as e:
        print(f"❌ Error generating synopsis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # ✅ Security: Only allow safe filenames
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        # ✅ Point to backend/outputs/ directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        outputs_dir = os.path.join(backend_dir, "outputs")
        file_path = os.path.join(outputs_dir, filename)

        # ✅ Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return jsonify({'error': f"File not found: {filename}"}), 404

        print(f"📤 Sending file: {file_path}")
        return send_file(
            file_path, 
            as_attachment=True, 
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"❌ Error in download: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-suggestions', methods=['POST'])
def ai_suggestions():
    try:
        data = request.json
        if not data or 'memory' not in data:
            return jsonify({'error': 'Missing required field: memory'}), 400
        
        memory = data['memory']
        suggestion_prompt = f"""
        Based on this project: {json.dumps(memory)}

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

        return jsonify({'suggestions': suggestions})
    except Exception as e:
        print(f"Error in AI suggestions: {e}")
        return jsonify({'error': str(e)}), 500

# ✅ Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # ✅ Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 50)
    print(f"🚀 Starting AURA API Server")
    print("=" * 50)
    print(f"📡 Port: {port}")
    print(f"🌐 Host: 0.0.0.0")
    print(f"🔧 Debug: False (Production Mode)")
    print("\n📍 Available Endpoints:")
    print("  - GET  /")
    print("  - GET  /api/health")
    print("  - POST /api/conversation")
    print("  - GET  /api/github-search")
    print("  - GET  /api/research-papers")
    print("  - POST /api/professional-analysis")
    print("  - POST /api/generate-synopsis")
    print("  - GET  /api/download/<filename>")
    print("  - POST /api/ai-suggestions")
    print("=" * 50)
    print(f"\n✅ Server ready at http://0.0.0.0:{port}")
    print("Press CTRL+C to stop\n")
    
    # ✅ Run server
    app.run(debug=False, host='0.0.0.0', port=port)