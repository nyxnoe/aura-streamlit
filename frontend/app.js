// State management using localStorage
class AppState {
    constructor() {
        this.sessionId = this.getSessionId();
        this.messages = this.loadMessages();
        this.conversationHistory = this.loadConversationHistory();
        this.synopsisMemory = this.loadSynopsisMemory();
        this.autoResearchDone = false;
        this.initialGreeting = !this.messages.length;
    }

    getSessionId() {
        let id = localStorage.getItem('aura_session_id');
        if (!id) {
            id = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('aura_session_id', id);
        }
        return id;
    }

    logout() {
        localStorage.removeItem('aura_is_logged_in');
        localStorage.removeItem('aura_username');
        localStorage.removeItem('aura_login_time');
        window.location.href = 'login.html';
    }

    loadMessages() {
        const messages = localStorage.getItem('aura_messages');
        return messages ? JSON.parse(messages) : [];
    }

    saveMessages() {
        localStorage.setItem('aura_messages', JSON.stringify(this.messages));
    }

    loadConversationHistory() {
        const history = localStorage.getItem('aura_conversation_history');
        return history ? JSON.parse(history) : [];
    }

    saveConversationHistory() {
        localStorage.setItem('aura_conversation_history', JSON.stringify(this.conversationHistory));
    }

    loadSynopsisMemory() {
        const memory = localStorage.getItem('aura_synopsis_memory');
        return memory ? JSON.parse(memory) : {};
    }

    saveSynopsisMemory() {
        localStorage.setItem('aura_synopsis_memory', JSON.stringify(this.synopsisMemory));
    }
}

// API service class
class APIService {
    constructor(baseURL = 'https://aura-ai-powered-university-research-v0k3.onrender.com/api') {
        this.baseURL = baseURL;
    }

    async handleNaturalConversation(prompt, conversationHistory, sessionId, synopsisMemory) {
        try {
            const response = await fetch(`${this.baseURL}/conversation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt,
                    conversation_history: conversationHistory,
                    session_id: sessionId,
                    synopsis_memory: synopsisMemory
                })
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return {
                response: "Service unavailable. Please check your backend connection.",
                updated_memory: synopsisMemory,
                updated_fields: [],
                missing_info: [],
                auto_research_triggered: false,
                research_results: {}
            };
        }
    }

    async searchGitHubRepos(query, limit = 5) {
        try {
            const response = await fetch(`${this.baseURL}/github-search?q=${encodeURIComponent(query)}&limit=${limit}`);
            return await response.json();
        } catch (error) {
            console.error('GitHub Search Error:', error);
            return [];
        }
    }

    async searchResearchPapers(query, limit = 5) {
        try {
            const response = await fetch(`${this.baseURL}/research-papers?q=${encodeURIComponent(query)}&limit=${limit}`);
            return await response.json();
        } catch (error) {
            console.error('Research Papers Error:', error);
            return [];
        }
    }

    async runProfessionalAnalysis(title, repos) {
        try {
            const response = await fetch(`${this.baseURL}/professional-analysis`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title, repos })
            });
            const data = await response.json();
            return data.analysis;
        } catch (error) {
            console.error('Professional Analysis Error:', error);
            return "Analysis unavailable.";
        }
    }

    async generateSynopsis(sessionId, idea, researchData) {
        try {
            const response = await fetch(`${this.baseURL}/generate-synopsis`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: sessionId, idea, research_data: researchData })
            });
            return await response.json();
        } catch (error) {
            console.error('Synopsis Generation Error:', error);
            return null;
        }
    }

    async getAISuggestions(memory) {
        try {
            const response = await fetch(`${this.baseURL}/ai-suggestions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ memory })
            });
            const data = await response.json();
            return data.suggestions;
        } catch (error) {
            console.error('AI Suggestions Error:', error);
            return "Suggestions unavailable.";
        }
    }
}

// UI Manager class
class UIManager {
    constructor(appState, apiService) {
        this.appState = appState;
        this.apiService = apiService;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.renderInitialState();
        this.updateProgress();
        this.updateStageIndicator();
    }

    setupEventListeners() {
        // Chat input
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');

        const sendMessage = () => {
            const message = chatInput.value.trim();
            if (message) {
                this.handleUserMessage(message);
                chatInput.value = '';
            }
        };

        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Quick actions
        document.getElementById('find-projects').addEventListener('click', () => this.handleFindProjects());
        document.getElementById('research-papers').addEventListener('click', () => this.handleResearchPapers());
        document.getElementById('professional-analysis').addEventListener('click', () => this.handleProfessionalAnalysis());
        document.getElementById('ai-suggestions').addEventListener('click', () => this.handleAISuggestions());

        // Synopsis generation
        document.addEventListener('click', (e) => {
            if (e.target.id === 'generate-synopsis') {
                this.handleGenerateSynopsis();
            }
            if (e.target.id === 'logout-btn') {
                this.appState.logout();
            }
        });
    }

    renderInitialState() {
        if (this.appState.initialGreeting) {
            const greeting = {
                role: "assistant",
                content: "👋 **Hello! I'm AURA, your intelligent research assistant.**\n\nI'm here to help you develop your project idea from concept to complete documentation. Just start telling me about your project idea naturally, and I'll:\n\n🔍 **Automatically research** similar projects and papers\n📝 **Extract key information** for your synopsis as we chat\n🎯 **Ask intelligent questions** to understand your vision better\n📄 **Generate comprehensive documentation** when ready\n\n**What's your project idea? Tell me about it in your own words!** 💡"
            };
            this.appState.messages.push(greeting);
            this.appState.saveMessages();
        }

        this.renderMessages();
    }

    renderMessages() {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';

        this.appState.messages.forEach(message => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${message.role}`;

            const avatar = document.createElement('div');
            avatar.className = 'chat-avatar';
            avatar.textContent = message.role === 'assistant' ? '🤖' : '👤';

            const content = document.createElement('div');
            content.className = 'chat-content';
            content.innerHTML = this.formatMessage(message.content);

            messageDiv.appendChild(avatar);
            messageDiv.appendChild(content);
            chatMessages.appendChild(messageDiv);
        });

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    formatMessage(content) {
        // Convert markdown-like syntax to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    async handleUserMessage(message) {
        // Add user message
        const userMessage = { role: "user", content: message };
        this.appState.messages.push(userMessage);
        this.appState.conversationHistory.push(userMessage);
        this.appState.saveMessages();
        this.appState.saveConversationHistory();
        this.renderMessages();

        // Show thinking indicator
        this.showThinkingIndicator();

        try {
            // Call API
            const result = await this.apiService.handleNaturalConversation(
                message,
                this.appState.conversationHistory,
                this.appState.sessionId,
                this.appState.synopsisMemory
            );

            // Update state
            this.appState.synopsisMemory = result.updated_memory;
            this.appState.saveSynopsisMemory();

            // Build response
            let responseContent = result.response;

            if (result.auto_research_triggered) {
                this.appState.autoResearchDone = true;
                responseContent += '\n\n<div class="auto-research-alert"><h4>🔬 Auto-Research Complete!</h4><p>Research has been integrated into your synopsis!</p></div>';
            }

            if (result.updated_fields && result.updated_fields.length > 0) {
                responseContent += `\n\n*📝 Updated: ${result.updated_fields.join(', ')}*`;
            }

            // Check if ready for synopsis
            const filledFields = Object.values(result.updated_memory).filter(v => v && String(v).trim().length > 10).length;
            if (filledFields >= 4 && !result.updated_memory.synopsis_offer_shown) {
                responseContent += '\n\n<div class="synopsis-ready"><h4>🎉 Ready for Synopsis Generation!</h4><p>Click "Generate Synopsis" in the sidebar!</p></div>';
                this.appState.synopsisMemory.synopsis_offer_shown = true;
                this.appState.saveSynopsisMemory();
            }

            // Add assistant response
            const assistantMessage = { role: "assistant", content: responseContent };
            this.appState.messages.push(assistantMessage);
            this.appState.conversationHistory.push(assistantMessage);
            this.appState.saveMessages();
            this.appState.saveConversationHistory();

            this.renderMessages();
            this.updateProgress();
            this.updateStageIndicator();

        } catch (error) {
            console.error('Error handling message:', error);
            const errorMessage = { role: "assistant", content: "❌ An error occurred. Please try again." };
            this.appState.messages.push(errorMessage);
            this.appState.saveMessages();
            this.renderMessages();
        }

        this.hideThinkingIndicator();
    }

    showThinkingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const thinkingDiv = document.createElement('div');
        thinkingDiv.id = 'thinking-indicator';
        thinkingDiv.className = 'chat-message assistant';
        thinkingDiv.innerHTML = `
            <div class="chat-avatar">🤖</div>
            <div class="chat-content">🤔 AURA is thinking...</div>
        `;
        chatMessages.appendChild(thinkingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideThinkingIndicator() {
        const thinkingIndicator = document.getElementById('thinking-indicator');
        if (thinkingIndicator) {
            thinkingIndicator.remove();
        }
    }

    updateProgress() {
        const memory = this.appState.synopsisMemory;
        const progressItems = {
            "title": "📝 Project Title",
            "group_details": "👥 Team Details",
            "objective_scope": "🎯 Objectives & Scope",
            "process_description": "⚙️ Methodology",
            "resources_limitations": "📋 Resources",
            "conclusion": "🎉 Expected Outcomes",
            "references": "📚 References"
        };

        const completed = Object.keys(progressItems).filter(key => memory[key]).length;
        const total = Object.keys(progressItems).length;
        const progress = completed / total;

        // Update progress bar
        const progressBar = document.getElementById('progress-bar');
        if (progressBar) {
            progressBar.innerHTML = `<div style="width: ${progress * 100}%"></div>`;
        }

        // Update progress details
        const progressDetails = document.getElementById('progress-details');
        if (progressDetails) {
            progressDetails.innerHTML = Object.entries(progressItems).map(([key, label]) => {
                const value = memory[key];
                if (value) {
                    return `<div class="progress-item progress-complete">✅ ${label}</div>`;
                } else {
                    return `<div class="progress-item">⏳ ${label}</div>`;
                }
            }).join('');
        }

        // Update research status
        const researchStatus = document.getElementById('research-status');
        if (researchStatus) {
            if (this.appState.autoResearchDone) {
                researchStatus.innerHTML = `
                    <div style="color: green;">✅ Auto-research completed!</div>
                    <ul>
                        <li>📄 Introduction generated</li>
                        <li>📚 Literature review completed</li>
                        <li>⚙️ Methodology analyzed</li>
                        <li>💻 Requirements specified</li>
                        <li>📊 Feasibility assessed</li>
                    </ul>
                `;
            } else {
                researchStatus.innerHTML = '<div style="color: orange;">⏳ Auto-research pending...</div>';
            }
        }

        // Update synopsis section
        const synopsisSection = document.getElementById('synopsis-section');
        if (synopsisSection) {
            if (completed >= 3) {
                synopsisSection.innerHTML = `
                    <button id="generate-synopsis">🚀 Generate Synopsis</button>
                    <div id="synopsis-download" style="display: none;">
                        <a id="download-link" href="#" download>📥 Download PDF</a>
                    </div>
                `;
            } else {
                synopsisSection.innerHTML = `<p>Need ${3 - completed} more sections</p>`;
            }
        }

        // Update session info
        const sessionInfo = document.getElementById('session-info');
        if (sessionInfo) {
            sessionInfo.innerHTML = `
                <p><strong>Session ID:</strong> ${this.appState.sessionId.slice(-8)}...</p>
                <p><strong>Messages:</strong> ${this.appState.messages.length}</p>
                <p><strong>Created:</strong> ${new Date().toLocaleString()}</p>
            `;
        }
    }

    updateStageIndicator() {
        const memory = this.appState.synopsisMemory;
        const filledCount = Object.values(memory).filter(v => v && String(v).trim().length > 10).length;

        let stage;
        if (filledCount === 0) stage = "🌱 Getting Started";
        else if (filledCount < 3) stage = "📝 Gathering Information";
        else if (filledCount < 5) stage = "🔬 Research Phase";
        else stage = "📄 Ready for Synopsis";

        const stageIndicator = document.getElementById('stage-indicator');
        if (stageIndicator) {
            stageIndicator.textContent = stage;
        }
    }

    async handleFindProjects() {
        const title = this.appState.synopsisMemory.title;
        if (!title) {
            alert("Please share your project idea first!");
            return;
        }

        const repos = await this.apiService.searchGitHubRepos(title, 5);
        this.showResults("📦 Similar Projects Found", repos.map(repo => `<div>${repo}</div>`).join(''));
    }

    async handleResearchPapers() {
        const title = this.appState.synopsisMemory.title;
        if (!title) {
            alert("Please share your project idea first!");
            return;
        }

        const papers = await this.apiService.searchResearchPapers(title, 5);
        this.showResults("📄 Relevant Papers", papers.map(paper => `<div>${paper}</div>`).join(''));
    }

    async handleProfessionalAnalysis() {
        const title = this.appState.synopsisMemory.title;
        if (!title) {
            alert("Please share your project idea first!");
            return;
        }

        const repos = await this.apiService.searchGitHubRepos(title, 3);
        const analysis = await this.apiService.runProfessionalAnalysis(title, repos);
        this.showResults("🎯 Professional Analysis", `<div>${analysis}</div>`);
    }

    async handleAISuggestions() {
        const title = this.appState.synopsisMemory.title;
        if (!title) {
            alert("Please share your project idea first!");
            return;
        }

        const suggestions = await this.apiService.getAISuggestions(this.appState.synopsisMemory);
        this.showResults("💡 AI Suggestions", `<div>${suggestions}</div>`);
    }

    async handleGenerateSynopsis() {
        const button = document.getElementById('generate-synopsis');
        button.disabled = true;
        button.textContent = 'Generating...';

        try {
            const result = await this.apiService.generateSynopsis(
                this.appState.sessionId,
                this.appState.synopsisMemory.title,
                this.appState.synopsisMemory
            );

            if (result && result.filename) {
                // Create download link
                const downloadLink = document.createElement('a');
                downloadLink.href = `http://localhost:5000/api/download/${result.filename}`;
                downloadLink.download = result.filename;
                downloadLink.textContent = '📥 Download PDF';
                downloadLink.style.cssText = `
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 25px;
                    text-decoration: none;
                    font-weight: 600;
                    margin-top: 1rem;
                    transition: all 0.3s ease;
                `;
                downloadLink.onmouseover = () => downloadLink.style.transform = 'translateY(-2px)';
                downloadLink.onmouseout = () => downloadLink.style.transform = 'translateY(0)';

                const synopsisSection = document.getElementById('synopsis-section');
                synopsisSection.appendChild(downloadLink);

                button.textContent = '✅ Generated!';
                button.style.background = '#4caf50';
            } else {
                button.textContent = '❌ Failed';
                button.style.background = '#f44336';
            }
        } catch (error) {
            console.error('Synopsis generation error:', error);
            button.textContent = '❌ Error';
            button.style.background = '#f44336';
        } finally {
            button.disabled = false;
        }
    }

    showResults(title, content) {
    const quickActions = document.getElementById('quick-actions');
    if (!quickActions) return;

    // 🔁 Remove any existing card with the same title
    const existingCards = quickActions.querySelectorAll('.info-card h4');
    existingCards.forEach(h4 => {
        if (h4.textContent.trim() === title.trim()) {
            h4.parentElement.remove();
        }
    });

    // ➕ Add fresh card
    const resultsDiv = document.createElement('div');
    resultsDiv.className = 'info-card';
    resultsDiv.innerHTML = `<h4>${title}</h4>${content}`;

    quickActions.appendChild(resultsDiv);
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
   }

}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    const appState = new AppState();
    const apiService = new APIService();
    const uiManager = new UIManager(appState, apiService);

    // Header functionality
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const newChatBtn = document.getElementById('new-chat-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const userDisplay = document.getElementById('user-display');
    const headerSearch = document.getElementById('header-search');

    // Update user display
    const username = localStorage.getItem('aura_username') || 'Guest';
    if (userDisplay) {
        userDisplay.textContent = username.charAt(0).toUpperCase();
        userDisplay.setAttribute('data-fullname', username);
    }

    // Navigation functionality
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Search functionality
    if (headerSearch) {
        headerSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = headerSearch.value.trim();
                if (query) {
                    // Send search query to chat
                    const chatInput = document.getElementById('chat-input');
                    if (chatInput) {
                        chatInput.value = `Search for: ${query}`;
                        chatInput.focus();
                        // Trigger send if possible
                        const sendButton = document.getElementById('send-button');
                        if (sendButton) {
                            sendButton.click();
                        }
                    }
                }
            }
        });
    }

    // Sidebar toggle
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('sidebar-hidden');
            const main = document.querySelector('main');
            if (main) {
                main.classList.toggle('sidebar-hidden');
            }
        });
    }

    // New chat functionality
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            if (confirm('Start a new chat? This will clear the current conversation.')) {
                // Clear messages and reset state
                appState.messages = [];
                appState.saveMessages();
                appState.conversationHistory = [];
                appState.saveConversationHistory();
                appState.synopsisMemory = {};
                appState.saveSynopsisMemory();
                appState.autoResearchDone = false;

                // Clear UI
                const chatMessages = document.getElementById('chat-messages');
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                }

                // Reset progress
                uiManager.updateProgress();

                // Show welcome message
                uiManager.addMessage('assistant', 'Hello! I\'m AURA, your AI research assistant. Tell me about your project idea and I\'ll help you create a comprehensive synopsis.');
            }
        });
    }

    // Logout functionality
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to logout?')) {
                // Clear all session data
                localStorage.removeItem('aura_is_logged_in');
                localStorage.removeItem('aura_username');
                localStorage.removeItem('aura_login_time');
                localStorage.removeItem('aura_session_id');
                localStorage.removeItem('aura_messages');
                localStorage.removeItem('aura_conversation_history');
                localStorage.removeItem('aura_synopsis_memory');

                // Redirect to login
                window.location.href = 'login.html';
            }
        });
    }
});
function updateSidebarProgress(memory = {}) {
  const sections = [
    { key: "title", label: "📘 Project Title" },
    { key: "group_details", label: "👥 Team Details" },
    { key: "objective_scope", label: "🎯 Objectives & Scope" },
    { key: "process_description", label: "⚙️ Methodology" },
    { key: "resources_limitations", label: "🧩 Resources" },
    { key: "conclusion", label: "🎓 Expected Outcomes" },
    { key: "references", label: "📚 References" }
  ];

  const list = document.getElementById('progress-list');
  const bar = document.getElementById('progress-fill');
  if (!list || !bar) return;

  let filled = 0;
  list.innerHTML = '';

  sections.forEach(sec => {
    const complete = memory[sec.key] && memory[sec.key].trim().length > 0;
    if (complete) filled++;
    const status = complete ? "✅" : "⏳";
    const li = document.createElement('li');
    li.innerHTML = `<span>${sec.label}</span><span class="status">${status}</span>`;
    list.appendChild(li);
  });

  const percent = Math.round((filled / sections.length) * 100);
  bar.style.width = `${percent}%`;
}
updateSidebarProgress();
function updateStageIndicator(filledCount = 0) {
    const stageIndicator = document.getElementById('stage-indicator');
    if (!stageIndicator) return;
    let stage;
    if (filledCount === 0) stage = "🌱 Getting Started";
    else if (filledCount < 3) stage = "📝 Gathering Information";
    else if (filledCount < 5) stage = "🔬 Research Phase";
    else stage = "📄 Ready for Synopsis"
    stageIndicator.textContent = stage
    };