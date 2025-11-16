from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime
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
CORS(app)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path='config/.env')

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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github-search', methods=['GET'])
def github_search():
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 5))
        repos = search_github_repos(query, limit)
        return jsonify(repos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/research-papers', methods=['GET'])
def research_papers():
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 5))
        papers = search_research_papers(query, limit)
        return jsonify(papers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/professional-analysis', methods=['POST'])
def professional_analysis():
    try:
        data = request.json
        analysis = run_professional_analysis(data['title'], data['repos'])
        return jsonify({'analysis': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-synopsis', methods=['POST'])
def generate_synopsis():
    try:
        data = request.get_json()
        session_id = data.get("session_id", "default_session")

        output_path = generate_comprehensive_synopsis(session_id)

        # ✅ Extract only the filename, not the full path
        filename = os.path.basename(output_path)

        print(f"✅ Synopsis generated: {filename}")
        return jsonify({
            "message": "Synopsis generated successfully.",
            "filename": filename,  # send just the filename
            "download_url": f"/api/download/{filename}"
        })

    except Exception as e:
        print(f"Error generating synopsis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # ✅ Point to the correct folder where PDFs are saved
        outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
        file_path = os.path.join(outputs_dir, filename)

        # ✅ Check if file actually exists
        if not os.path.exists(file_path):
            return jsonify({'error': f"File not found: {file_path}"}), 404

        print(f"📤 Sending file: {file_path}")
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-suggestions', methods=['POST'])
def ai_suggestions():
    try:
        data = request.json
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting AURA API Server...")
    print("Available endpoints:")
    print("- POST /api/conversation")
    print("- GET /api/github-search")
    print("- GET /api/research-papers")
    print("- POST /api/professional-analysis")
    print("- POST /api/generate-synopsis")
    print("- GET /api/download/<filename>")
    print("- POST /api/ai-suggestions")
    print("\nServer running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
