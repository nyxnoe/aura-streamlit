// ==========================================
// 1. STATE MANAGEMENT (With Self-Healing)
// ==========================================
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

    // --- Safe Loaders (Prevents "undefined" crashes) ---
    _safeLoad(key, defaultValue) {
        const data = localStorage.getItem(key);
        try {
            if (!data || data === "undefined" || data === "null") {
                return defaultValue;
            }
            return JSON.parse(data);
        } catch (e) {
            console.warn(`⚠️ Corrupted data for ${key}. Resetting.`);
            return defaultValue;
        }
    }

    loadMessages() { return this._safeLoad('aura_messages', []); }
    loadConversationHistory() { return this._safeLoad('aura_conversation_history', []); }
    loadSynopsisMemory() { return this._safeLoad('aura_synopsis_memory', {}); }

    // --- Savers ---
    saveMessages() { localStorage.setItem('aura_messages', JSON.stringify(this.messages)); }
    saveConversationHistory() { localStorage.setItem('aura_conversation_history', JSON.stringify(this.conversationHistory)); }
    saveSynopsisMemory() { localStorage.setItem('aura_synopsis_memory', JSON.stringify(this.synopsisMemory)); }
}

// ==========================================
// 2. API SERVICE (Connected to Relative Path)
// ==========================================
class APIService {
    constructor(baseURL = '/api') { // ✅ Fixes CORS
        this.baseURL = baseURL;
    }

    async handleNaturalConversation(prompt, conversationHistory, sessionId, synopsisMemory) {
        try {
            const response = await fetch(`${this.baseURL}/conversation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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
        } catch (error) { return []; }
    }

    async searchResearchPapers(query, limit = 5) {
        try {
            const response = await fetch(`${this.baseURL}/research-papers?q=${encodeURIComponent(query)}&limit=${limit}`);
            return await response.json();
        } catch (error) { return []; }
    }

    async runProfessionalAnalysis(title, repos) {
        try {
            const response = await fetch(`${this.baseURL}/professional-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, repos })
            });
            const data = await response.json();
            return data.analysis;
        } catch (error) { return "Analysis unavailable."; }
    }

    async generateSynopsis(sessionId, idea, researchData) {
        try {
            const response = await fetch(`${this.baseURL}/generate-synopsis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, idea, research_data: researchData })
            });
            return await response.json();
        } catch (error) { return null; }
    }

    async getAISuggestions(memory) {
        try {
            const response = await fetch(`${this.baseURL}/ai-suggestions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ memory })
            });
            const data = await response.json();
            return data.suggestions;
        } catch (error) { return "Suggestions unavailable."; }
    }
}

// ==========================================
// 3. UI MANAGER (With Dynamic Sidebar)
// ==========================================
class UIManager {
    constructor(appState, apiService) {
        this.appState = appState;
        this.apiService = apiService;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.renderInitialState();
        this.updateProgress(); // Initial sidebar render
    }

    setupEventListeners() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');

        const sendMessage = () => {
            const message = chatInput.value.trim();
            if (message) {
                this.handleUserMessage(message);
                chatInput.value = '';
            }
        };

        if(sendButton) sendButton.addEventListener('click', sendMessage);
        if(chatInput) chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Quick Actions
        const btnFind = document.getElementById('find-projects');
        if(btnFind) btnFind.addEventListener('click', () => this.handleFindProjects());
        
        const btnPapers = document.getElementById('research-papers');
        if(btnPapers) btnPapers.addEventListener('click', () => this.handleResearchPapers());
        
        const btnAnalysis = document.getElementById('professional-analysis');
        if(btnAnalysis) btnAnalysis.addEventListener('click', () => this.handleProfessionalAnalysis());
        
        const btnAI = document.getElementById('ai-suggestions');
        if(btnAI) btnAI.addEventListener('click', () => this.handleAISuggestions());

        // Global clicks
        document.addEventListener('click', (e) => {
            if (e.target.id === 'generate-synopsis') this.handleGenerateSynopsis();
            if (e.target.id === 'logout-btn') this.appState.logout();
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
        if(!chatMessages) return;
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
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    formatMessage(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    async handleUserMessage(message) {
        const userMessage = { role: "user", content: message };
        this.appState.messages.push(userMessage);
        this.appState.conversationHistory.push(userMessage);
        this.appState.saveMessages();
        this.renderMessages();
        this.showThinkingIndicator();

        try {
            const result = await this.apiService.handleNaturalConversation(
                message,
                this.appState.conversationHistory,
                this.appState.sessionId,
                this.appState.synopsisMemory
            );

            this.appState.synopsisMemory = result.updated_memory;
            this.appState.saveSynopsisMemory();

            let responseContent = result.response;

            if (result.auto_research_triggered) {
                this.appState.autoResearchDone = true;
                responseContent += '\n\n<div class="auto-research-alert"><h4>🔬 Auto-Research Complete!</h4><p>Research has been integrated into your synopsis!</p></div>';
            }

            if (result.updated_fields && result.updated_fields.length > 0) {
                responseContent += `\n\n*📝 Updated: ${result.updated_fields.join(', ')}*`;
            }

            const filledFields = Object.values(result.updated_memory).filter(v => v && String(v).trim().length > 10).length;
            if (filledFields >= 4 && !result.updated_memory.synopsis_offer_shown) {
                responseContent += '\n\n<div class="synopsis-ready"><h4>🎉 Ready for Synopsis Generation!</h4><p>Click "Generate Synopsis" in the sidebar!</p></div>';
                this.appState.synopsisMemory.synopsis_offer_shown = true;
                this.appState.saveSynopsisMemory();
            }

            const assistantMessage = { role: "assistant", content: responseContent };
            this.appState.messages.push(assistantMessage);
            this.appState.conversationHistory.push(assistantMessage);
            this.appState.saveMessages();
            this.appState.saveConversationHistory();

            this.renderMessages();
            this.updateProgress(); // Update sidebar dynamically

        } catch (error) {
            const errorMessage = { role: "assistant", content: "❌ An error occurred. Please try again." };
            this.appState.messages.push(errorMessage);
            this.renderMessages();
        }
        this.hideThinkingIndicator();
    }

    showThinkingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const thinkingDiv = document.createElement('div');
        thinkingDiv.id = 'thinking-indicator';
        thinkingDiv.className = 'chat-message assistant';
        thinkingDiv.innerHTML = `<div class="chat-avatar">🤖</div><div class="chat-content">🤔 AURA is thinking...</div>`;
        chatMessages.appendChild(thinkingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideThinkingIndicator() {
        const thinkingIndicator = document.getElementById('thinking-indicator');
        if (thinkingIndicator) thinkingIndicator.remove();
    }

    // ✅ DYNAMIC SIDEBAR UPDATE FUNCTION
    updateProgress() {
        const memory = this.appState.synopsisMemory;
        const progressItems = {
            "title": "Project Title",
            "group_details": "Team Details",
            "objective_scope": "Objectives & Scope",
            "process_description": "Methodology",
            "resources_limitations": "Resources",
            "conclusion": "Expected Outcomes",
            "references": "References"
        };

        const completed = Object.keys(progressItems).filter(key => memory[key]).length;
        const total = Object.keys(progressItems).length;
        const progress = completed / total;

        // 1. Update Progress Bar
        const progressBar = document.getElementById('progress-bar');
        if (progressBar) {
            const percent = Math.round(progress * 100);
            progressBar.innerHTML = `
                <div class="progress-header">
                    <span>${completed}/${total} sections (${percent}%)</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${percent}%"></div>
                </div>
            `;
        }

        // 2. Update List with Expandable Cards
        const progressDetails = document.getElementById('progress-details');
        if (progressDetails) {
            progressDetails.innerHTML = Object.entries(progressItems).map(([key, label]) => {
                const value = memory[key];
                
                if (value && String(value).trim().length > 0) {
                    const previewText = String(value).replace(/<[^>]*>?/gm, ''); 
                    return `
                    <details class="sidebar-card completed">
                        <summary>
                            <span class="icon">✅</span>
                            <strong>${label}</strong>
                            <span class="expand-hint">▼</span>
                        </summary>
                        <div class="card-content">
                            <div class="content-text">${previewText}</div>
                        </div>
                    </details>`;
                } else {
                    return `
                    <div class="sidebar-card pending">
                        <span class="icon">⏳</span>
                        <span>${label}</span>
                    </div>`;
                }
            }).join('');
        }

        // 3. Update Research Status
        const researchStatus = document.getElementById('research-status');
        if (researchStatus) {
            if (this.appState.autoResearchDone) {
                researchStatus.innerHTML = `
                    <div class="sidebar-card research-done">
                        <div>✅ <strong>Auto-Research Complete!</strong></div>
                        <div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">
                            Research integrated.
                        </div>
                    </div>`;
            } else {
                researchStatus.innerHTML = `
                    <div class="sidebar-card research-pending">
                        ⏳ Auto-research pending...
                    </div>`;
            }
        }

        // 4. Update Synopsis Section
        const synopsisSection = document.getElementById('synopsis-section');
        if (synopsisSection) {
            if (completed >= 3) {
                 if (!synopsisSection.innerHTML.includes('Generate Synopsis')) {
                     synopsisSection.innerHTML = `<button id="generate-synopsis" class="sidebar-btn">🚀 Generate Synopsis</button>`;
                }
            } else {
                synopsisSection.innerHTML = `<div class="sidebar-note">Need ${3 - completed} more sections</div>`;
            }
        }
    }

    async handleFindProjects() {
        const title = this.appState.synopsisMemory.title;
        if (!title) { alert("Please share your project idea first!"); return; }
        const repos = await this.apiService.searchGitHubRepos(title, 5);
        this.showResults("📦 Similar Projects Found", repos.map(repo => `<div>${repo}</div>`).join(''));
    }

    async handleResearchPapers() {
        const title = this.appState.synopsisMemory.title;
        if (!title) { alert("Please share your project idea first!"); return; }
        const papers = await this.apiService.searchResearchPapers(title, 5);
        this.showResults("📄 Relevant Papers", papers.map(paper => `<div>${paper}</div>`).join(''));
    }

    async handleProfessionalAnalysis() {
        const title = this.appState.synopsisMemory.title;
        if (!title) { alert("Please share your project idea first!"); return; }
        const repos = await this.apiService.searchGitHubRepos(title, 3);
        const analysis = await this.apiService.runProfessionalAnalysis(title, repos);
        this.showResults("🎯 Professional Analysis", `<div>${analysis}</div>`);
    }

    async handleAISuggestions() {
        const title = this.appState.synopsisMemory.title;
        if (!title) { alert("Please share your project idea first!"); return; }
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
                const downloadLink = document.createElement('a');
                // ✅ Fix: Use dynamic Base URL for download
                downloadLink.href = `${this.apiService.baseURL}/download/${result.filename}`;
                downloadLink.download = result.filename;
                downloadLink.textContent = '📥 Download PDF';
                downloadLink.className = 'download-btn'; // Use CSS class instead of inline styles
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

                const synopsisSection = document.getElementById('synopsis-section');
                synopsisSection.appendChild(downloadLink);
                button.textContent = '✅ Generated!';
                button.style.background = '#4caf50';
            } else {
                button.textContent = '❌ Failed';
                button.style.background = '#f44336';
            }
        } catch (error) {
            console.error('Synopsis error:', error);
            button.textContent = '❌ Error';
        } finally {
            button.disabled = false;
        }
    }

    showResults(title, content) {
        const quickActions = document.getElementById('quick-actions');
        if (!quickActions) return;
        
        const existingCards = quickActions.querySelectorAll('.info-card h4');
        existingCards.forEach(h4 => {
            if (h4.textContent.trim() === title.trim()) h4.parentElement.remove();
        });

        const resultsDiv = document.createElement('div');
        resultsDiv.className = 'info-card';
        resultsDiv.innerHTML = `<h4>${title}</h4>${content}`;
        quickActions.appendChild(resultsDiv);
        resultsDiv.scrollIntoView({ behavior: 'smooth' });
    }
}

// ==========================================
// 4. INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    const appState = new AppState();
    const apiService = new APIService();
    const uiManager = new UIManager(appState, apiService);

    // UI Toggles
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const newChatBtn = document.getElementById('new-chat-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const userDisplay = document.getElementById('user-display');
    
    if (userDisplay) {
        const username = localStorage.getItem('aura_username') || 'Guest';
        userDisplay.textContent = username.charAt(0).toUpperCase();
    }

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('sidebar-hidden');
            const main = document.querySelector('main');
            if (main) main.classList.toggle('sidebar-hidden');
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            if (confirm('Start a new chat?')) {
                appState.messages = [];
                appState.conversationHistory = [];
                appState.synopsisMemory = {};
                appState.autoResearchDone = false;
                appState.saveMessages();
                appState.saveConversationHistory();
                appState.saveSynopsisMemory();
                
                const chatMessages = document.getElementById('chat-messages');
                if (chatMessages) chatMessages.innerHTML = '';
                uiManager.updateProgress();
                uiManager.renderInitialState();
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (confirm('Logout?')) appState.logout();
        });
    }
});