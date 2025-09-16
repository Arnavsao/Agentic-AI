
class GAILChatbot {
    constructor() {
        this.isLoading = false;
        this.conversationHistory = [];
        this.init();
    }

    init() {
        this.loadSuggestions();
        this.loadSystemStatus();
        this.setupEventListeners();
    }

    setupEventListeners() {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');

        messageInput.focus();

        messageInput.addEventListener('input', () => {
            messageInput.style.height = 'auto';
            messageInput.style.height = messageInput.scrollHeight + 'px';
        });
    }

    async loadSuggestions() {
        try {
            const response = await fetch('/api/suggestions');
            const data = await response.json();
            
            const suggestionsContainer = document.getElementById('suggestions');
            suggestionsContainer.innerHTML = '';

            data.suggestions.forEach(suggestion => {
                const suggestionElement = document.createElement('div');
                suggestionElement.className = 'suggestion-item';
                suggestionElement.textContent = suggestion;
                suggestionElement.onclick = () => this.sendSuggestion(suggestion);
                suggestionsContainer.appendChild(suggestionElement);
            });
        } catch (error) {
            console.error('Error loading suggestions:', error);
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            const statusContainer = document.getElementById('system-status');
            
            if (data.status === 'operational') {
                statusContainer.innerHTML = `
                    <div class="status-item">
                        <span>Status:</span>
                        <span class="status-badge status-operational">Operational</span>
                    </div>
                    <div class="status-item">
                        <span>Documents:</span>
                        <span>${data.total_documents.toLocaleString()}</span>
                    </div>
                    <div class="status-item">
                        <span>Last Updated:</span>
                        <span>${new Date(data.last_updated).toLocaleDateString()}</span>
                    </div>
                `;
            } else {
                statusContainer.innerHTML = '<div class="text-danger">System Error</div>';
            }
        } catch (error) {
            console.error('Error loading system status:', error);
            document.getElementById('system-status').innerHTML = '<div class="text-danger">Status Unavailable</div>';
        }
    }

    async sendMessage(message = null) {
        const messageInput = document.getElementById('message-input');
        const messageText = message || messageInput.value.trim();

        if (!messageText || this.isLoading) {
            return;
        }

        if (!message) {
            messageInput.value = '';
            messageInput.style.height = 'auto';
        }

        this.addMessage(messageText, 'user');

        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: messageText,
                    timestamp: new Date().toISOString()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            this.hideTypingIndicator();

            this.addBotMessage(data.answer, data.sources, data.confidence);

            if (data.suggested_questions) {
                this.updateSuggestions(data.suggested_questions);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addBotMessage(
                'I apologize, but I encountered an error while processing your request. Please try again.',
                [],
                0
            );
        }
    }

    sendSuggestion(suggestion) {
        this.sendMessage(suggestion);
    }

    addMessage(text, sender) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = text;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.getCurrentTime();

        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        this.scrollToBottom();

        this.conversationHistory.push({
            sender: sender,
            text: text,
            timestamp: new Date().toISOString()
        });
    }

    addBotMessage(text, sources, confidence) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.innerHTML = `<i class="fas fa-robot"></i> ${this.formatMessage(text)}`;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.getCurrentTime();

        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);

        if (confidence > 0) {
            const confidenceBadge = document.createElement('div');
            confidenceBadge.className = 'confidence-badge';
            confidenceBadge.textContent = `Confidence: ${(confidence * 100).toFixed(0)}%`;
            messageContent.appendChild(confidenceBadge);
        }

        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            
            const sourcesTitle = document.createElement('div');
            sourcesTitle.textContent = 'Sources:';
            sourcesTitle.style.fontWeight = '600';
            sourcesTitle.style.marginBottom = '0.5rem';
            sourcesDiv.appendChild(sourcesTitle);

            sources.forEach((source, index) => {
                const sourceLink = document.createElement('a');
                sourceLink.className = 'source-link';
                sourceLink.href = source.url;
                sourceLink.target = '_blank';
                sourceLink.textContent = `${index + 1}. ${source.title}`;
                sourceLink.title = `Similarity: ${(source.similarity_score * 100).toFixed(1)}%`;
                sourcesDiv.appendChild(sourceLink);
            });

            messageContent.appendChild(sourcesDiv);
        }

        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        this.scrollToBottom();

        this.conversationHistory.push({
            sender: 'bot',
            text: text,
            sources: sources,
            confidence: confidence,
            timestamp: new Date().toISOString()
        });
    }

    formatMessage(text) {
        return text.replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        typingIndicator.style.display = 'none';
    }

    updateSuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('suggestions');
        suggestionsContainer.innerHTML = '';

        suggestions.forEach(suggestion => {
            const suggestionElement = document.createElement('div');
            suggestionElement.className = 'suggestion-item';
            suggestionElement.textContent = suggestion;
            suggestionElement.onclick = () => this.sendSuggestion(suggestion);
            suggestionsContainer.appendChild(suggestionElement);
        });
    }

    async clearHistory() {
        try {
            await fetch('/api/clear-history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const chatMessages = document.getElementById('chat-messages');
            const initialMessage = chatMessages.querySelector('.bot-message');
            chatMessages.innerHTML = '';
            if (initialMessage) {
                chatMessages.appendChild(initialMessage);
            }

            this.conversationHistory = [];

            this.addBotMessage('Conversation history cleared. How can I help you today?', [], 1);

        } catch (error) {
            console.error('Error clearing history:', error);
            this.addBotMessage('Sorry, I couldn\'t clear the history. Please try again.', [], 0);
        }
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

let chatbot;

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function sendMessage() {
    if (chatbot) {
        chatbot.sendMessage();
    }
}

function sendSuggestion(suggestion) {
    if (chatbot) {
        chatbot.sendSuggestion(suggestion);
    }
}

function clearHistory() {
    if (chatbot) {
        chatbot.clearHistory();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    chatbot = new GAILChatbot();
});
