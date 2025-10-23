// Solverde Chatbot Frontend Application
// Handles SSE streaming and UI updates

class SolverdeChatbot {
    constructor() {
        this.apiBaseUrl = '';
        this.sessionId = this.generateUUID();
        this.isStreaming = false;

        this.chatContainer = document.getElementById('chat-container');
        this.chatForm = document.getElementById('chat-form');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.typingIndicator = document.getElementById('typing-indicator');

        this.init();
    }

    init() {
        // Event listeners
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.newChatBtn.addEventListener('click', () => this.startNewChat());

        // Suggestion buttons
        const suggestionBtns = document.querySelectorAll('.suggestion-btn');
        suggestionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.querySelector('span').textContent;
                this.userInput.value = text;
                this.handleSubmit(new Event('submit'));
            });
        });

        // Focus input
        this.userInput.focus();

        // Check API health
        this.checkHealth();

        // Configure marked options for better rendering
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,
                gfm: true
            });
        }
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            console.log('✓ API Health:', data);

            // Show success message briefly
            if (data.faq_count === 0) {
                console.warn('⚠️  Nenhuma FAQ carregada no backend');
            }
        } catch (error) {
            console.error('❌ API não acessível:', error);
            this.showError('Não foi possível conectar ao servidor. Certifica-te que o backend está a correr em http://localhost:8000');
        }
    }

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    async handleSubmit(e) {
        e.preventDefault();

        const message = this.userInput.value.trim();
        if (!message || this.isStreaming) return;

        // Clear input and disable
        this.userInput.value = '';
        this.setInputState(false);

        // Remove welcome screen if present
        const welcomeScreen = this.chatContainer.querySelector('.welcome-screen');
        if (welcomeScreen) {
            welcomeScreen.remove();
        }

        // Display user message
        this.appendMessage('user', message);

        // Show typing indicator
        this.showTypingIndicator();

        // Stream response
        await this.streamResponse(message);

        // Hide typing indicator
        this.hideTypingIndicator();

        // Re-enable input
        this.setInputState(true);
        this.userInput.focus();
    }

    async streamResponse(message) {
        this.isStreaming = true;

        // Create assistant message container
        const assistantMsgDiv = this.createAssistantMessageContainer();

        try {
            // Use Server-Sent Events for streaming
            const url = `${this.apiBaseUrl}/api/chat/stream`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });

            if (!response.ok) {
                throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // Decode the chunk
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));

                            if (data.type === 'token') {
                                fullResponse += data.content;
                                // Update message with markdown rendering
                                assistantMsgDiv.innerHTML = marked.parse(fullResponse);
                                this.scrollToBottom();
                            } else if (data.type === 'done') {
                                // Stream complete
                                break;
                            } else if (data.type === 'error') {
                                throw new Error(data.content);
                            }
                        } catch (parseError) {
                            console.error('Erro ao fazer parse do chunk:', parseError);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Streaming error:', error);
            assistantMsgDiv.innerHTML = `
                <p class="text-red-600">❌ Erro: ${this.escapeHtml(error.message)}</p>
                <p class="text-sm text-gray-500 mt-2">Por favor, tenta novamente.</p>
            `;
        } finally {
            this.isStreaming = false;
        }
    }

    appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message flex';

        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="user-message">
                    <div class="flex items-start space-x-2">
                        <i class="fas fa-user mt-1"></i>
                        <div>${this.escapeHtml(content)}</div>
                    </div>
                </div>
            `;
        } else {
            const renderedContent = typeof marked !== 'undefined'
                ? marked.parse(content)
                : this.escapeHtml(content);

            messageDiv.innerHTML = `
                <div class="assistant-message">
                    <div class="flex items-start space-x-2">
                        <i class="fas fa-robot text-green-600 mt-1"></i>
                        <div>${renderedContent}</div>
                    </div>
                </div>
            `;
        }

        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    createAssistantMessageContainer() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message flex';
        messageDiv.innerHTML = `
            <div class="assistant-message">
                <div class="flex items-start space-x-2">
                    <i class="fas fa-robot text-green-600 mt-1"></i>
                    <div id="streaming-content"></div>
                </div>
            </div>
        `;

        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv.querySelector('#streaming-content');
    }

    showTypingIndicator() {
        this.typingIndicator.classList.remove('hidden');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.classList.add('hidden');
    }

    setInputState(enabled) {
        this.userInput.disabled = !enabled;
        this.sendBtn.disabled = !enabled;

        if (enabled) {
            this.sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            this.sendBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }, 50);
    }

    async startNewChat() {
        if (this.isStreaming) return;

        // Confirm if there are messages
        const messages = this.chatContainer.querySelectorAll('.message');
        if (messages.length > 0) {
            const confirmed = confirm('Tens a certeza que queres começar uma nova conversa? O histórico atual será perdido.');
            if (!confirmed) return;
        }

        // Generate new session ID
        this.sessionId = this.generateUUID();

        // Clear chat container
        this.chatContainer.innerHTML = `
            <div class="text-center py-12 welcome-screen">
                <i class="fas fa-comments text-6xl text-green-500 mb-4"></i>
                <h2 class="text-2xl font-bold text-gray-800 mb-2">Nova Conversa Iniciada!</h2>
                <p class="text-gray-600">Como posso ajudar?</p>

                <!-- Suggested questions -->
                <div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                    <button class="suggestion-btn bg-green-50 hover:bg-green-100 p-4 rounded-lg text-left transition">
                        <i class="fas fa-clock text-green-600 mr-2"></i>
                        <span class="text-gray-700">Quanto tempo demora um levantamento?</span>
                    </button>
                    <button class="suggestion-btn bg-green-50 hover:bg-green-100 p-4 rounded-lg text-left transition">
                        <i class="fas fa-gift text-green-600 mr-2"></i>
                        <span class="text-gray-700">Como usar free spins?</span>
                    </button>
                    <button class="suggestion-btn bg-green-50 hover:bg-green-100 p-4 rounded-lg text-left transition">
                        <i class="fas fa-file-alt text-green-600 mr-2"></i>
                        <span class="text-gray-700">Como obter comprovativo de IBAN?</span>
                    </button>
                    <button class="suggestion-btn bg-green-50 hover:bg-green-100 p-4 rounded-lg text-left transition">
                        <i class="fas fa-trophy text-green-600 mr-2"></i>
                        <span class="text-gray-700">Como usar o meu bónus?</span>
                    </button>
                </div>
            </div>
        `;

        // Re-attach suggestion button listeners
        const suggestionBtns = this.chatContainer.querySelectorAll('.suggestion-btn');
        suggestionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.querySelector('span').textContent;
                this.userInput.value = text;
                this.handleSubmit(new Event('submit'));
            });
        });

        // Focus input
        this.userInput.focus();

        // Show success notification
        this.showSuccess('Nova conversa iniciada!');
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <strong class="font-bold">Erro!</strong>
            <span class="block sm:inline ml-2">${message}</span>
        `;

        // Insert at top of chat container
        this.chatContainer.insertBefore(errorDiv, this.chatContainer.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => errorDiv.remove(), 5000);
    }

    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = `
            <strong class="font-bold">Sucesso!</strong>
            <span class="block sm:inline ml-2">${message}</span>
        `;

        // Insert at top of chat container
        this.chatContainer.insertBefore(successDiv, this.chatContainer.firstChild);

        // Auto-remove after 3 seconds
        setTimeout(() => successDiv.remove(), 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando Solverde Chatbot...');
    new SolverdeChatbot();
});
