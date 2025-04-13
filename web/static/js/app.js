/**
 * REMIND - Web Interface JavaScript
 * Handles interactions with the REMIND system through the web API
 */

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const chatTitle = document.getElementById('chat-title');
const chatTags = document.getElementById('chat-tags');

// Sidebar elements
const toggleHistoryBtn = document.getElementById('toggle-history-btn');
const toggleMemoryBtn = document.getElementById('toggle-memory-btn');
const historySidebar = document.getElementById('history-sidebar');
const memorySidebar = document.getElementById('memory-sidebar');
const closeHistoryBtn = document.getElementById('close-history-btn');
const closeMemoryBtn = document.getElementById('close-memory-btn');
const conversationList = document.getElementById('conversation-list');
const historySearch = document.getElementById('history-search');

// Memory tab elements
const tabBtns = document.querySelectorAll('.tab-btn');
const episodicList = document.getElementById('episodic-list');
const nonEpisodicList = document.getElementById('non-episodic-list');
const tagsCloud = document.getElementById('tags-cloud');
const episodicSearch = document.getElementById('episodic-search');
const nonEpisodicSearch = document.getElementById('non-episodic-search');
const memorySearch = document.getElementById('memory-search');
const memorySearchBtn = document.getElementById('memory-search-btn');
const memorySearchResults = document.getElementById('memory-search-results');

// Stats elements
const conversationCount = document.getElementById('conversation-count');
const episodicCount = document.getElementById('episodic-count');
const nonEpisodicCount = document.getElementById('non-episodic-count');

// Modal elements
const modal = document.getElementById('memory-detail-modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const closeModalBtn = document.getElementById('close-modal-btn');

// State
let currentConversationId = null;
let isWaitingForResponse = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    loadMemoryCounts();
    loadConversations();
    loadEpisodicMemories();
    loadNonEpisodicMemories();
    loadTags();
});

// Set up event listeners
function setupEventListeners() {
    // Chat controls
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    newChatBtn.addEventListener('click', startNewConversation);
    
    // Sidebar toggles
    toggleHistoryBtn.addEventListener('click', () => {
        historySidebar.classList.toggle('active');
        memorySidebar.classList.remove('active');
    });
    
    toggleMemoryBtn.addEventListener('click', () => {
        memorySidebar.classList.toggle('active');
        historySidebar.classList.remove('active');
    });
    
    closeHistoryBtn.addEventListener('click', () => {
        historySidebar.classList.remove('active');
    });
    
    closeMemoryBtn.addEventListener('click', () => {
        memorySidebar.classList.remove('active');
    });
    
    // Tab switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const tabId = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            document.getElementById(`${tabId}-panel`).classList.add('active');
        });
    });
    
    // Search
    historySearch.addEventListener('input', debounce(() => {
        const query = historySearch.value.trim();
        if (query) {
            searchConversations(query);
        } else {
            loadConversations();
        }
    }, 300));
    
    episodicSearch.addEventListener('input', debounce(() => {
        const query = episodicSearch.value.trim();
        if (query) {
            searchMemories('episodic', query);
        } else {
            loadEpisodicMemories();
        }
    }, 300));
    
    nonEpisodicSearch.addEventListener('input', debounce(() => {
        const query = nonEpisodicSearch.value.trim();
        if (query) {
            searchMemories('non_episodic', query);
        } else {
            loadNonEpisodicMemories();
        }
    }, 300));
    
    memorySearchBtn.addEventListener('click', () => {
        const query = memorySearch.value.trim();
        if (query) {
            searchAllMemories(query);
        }
    });
    
    memorySearch.addEventListener('keypress', e => {
        if (e.key === 'Enter') {
            const query = memorySearch.value.trim();
            if (query) {
                searchAllMemories(query);
            }
        }
    });
    
    // Modal close
    closeModalBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });
    
    // Close modal on outside click
    modal.addEventListener('click', e => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isWaitingForResponse) {
        return;
    }
    
    // Clear input
    messageInput.value = '';
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Add typing indicator
    const typingIndicator = addTypingIndicator();
    
    isWaitingForResponse = true;
    
    try {
        // Prepare request data
        const data = {
            message: message
        };
        
        if (currentConversationId) {
            data.conversation_id = currentConversationId;
        }
        
        // Send message to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        
        const responseData = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingIndicator);
        
        // Add assistant message to chat
        addMessageToChat('assistant', responseData.response);
        
        // Update conversation info if this is a new conversation
        if (!currentConversationId || responseData.new_conversation) {
            currentConversationId = responseData.conversation_id;
            updateConversationInfo(responseData);
        }
        
        // Reload memory counts and conversations
        loadMemoryCounts();
        loadConversations();
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Remove typing indicator
        removeTypingIndicator(typingIndicator);
        
        // Show error message
        addErrorMessage('Sorry, there was an error processing your message. Please try again.');
    } finally {
        isWaitingForResponse = false;
    }
}

// Start a new conversation
function startNewConversation() {
    // Clear current conversation
    currentConversationId = null;
    
    // Clear chat
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h2>New Conversation</h2>
            <p>I'm an AI assistant with memory capabilities. How can I help you today?</p>
        </div>
    `;
    
    // Update conversation info
    chatTitle.textContent = 'New Conversation';
    chatTags.innerHTML = '';
    
    // Focus on input
    messageInput.focus();
}

// Load conversation by ID
async function loadConversation(conversationId) {
    try {
        const response = await fetch(`/api/conversations/${conversationId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load conversation');
        }
        
        const conversation = await response.json();
        
        // Update current conversation
        currentConversationId = conversation.id;
        
        // Clear chat
        chatMessages.innerHTML = '';
        
        // Add messages to chat
        conversation.messages.forEach(msg => {
            addMessageToChat(msg.role, msg.content, new Date(msg.timestamp));
        });
        
        // Update conversation info
        updateConversationInfo({
            title: conversation.title,
            summary: conversation.summary,
            tags: conversation.tags
        });
        
        // Close history sidebar
        historySidebar.classList.remove('active');
        
    } catch (error) {
        console.error('Error loading conversation:', error);
        addErrorMessage('Sorry, there was an error loading the conversation.');
    }
}

// Delete conversation
async function deleteConversation(conversationId, event) {
    // Prevent event propagation
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this conversation?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/conversations/${conversationId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete conversation');
        }
        
        // If deleted current conversation, start a new one
        if (conversationId === currentConversationId) {
            startNewConversation();
        }
        
        // Reload conversations
        loadConversations();
        
        // Reload memory counts
        loadMemoryCounts();
        
    } catch (error) {
        console.error('Error deleting conversation:', error);
        alert('Sorry, there was an error deleting the conversation.');
    }
}

// Add message to chat
function addMessageToChat(role, content, timestamp = new Date()) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}`;
    
    const formattedTime = formatTime(timestamp);
    
    messageElement.innerHTML = `
        <div class="message-bubble">${formatMessageContent(content)}</div>
        <div class="message-time">${formattedTime}</div>
    `;
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add typing indicator
function addTypingIndicator() {
    const typingElement = document.createElement('div');
    typingElement.className = 'message assistant';
    typingElement.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    chatMessages.appendChild(typingElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return typingElement;
}

// Remove typing indicator
function removeTypingIndicator(element) {
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}

// Add error message
function addErrorMessage(message) {
    const errorElement = document.createElement('div');
    errorElement.className = 'message system';
    errorElement.innerHTML = `
        <div class="message-bubble" style="background-color: #ffebee; color: #d32f2f;">
            ${message}
        </div>
    `;
    
    chatMessages.appendChild(errorElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update conversation info
function updateConversationInfo(data) {
    chatTitle.textContent = data.title || 'Untitled Conversation';
    
    // Update tags
    chatTags.innerHTML = '';
    if (data.tags && data.tags.length > 0) {
        data.tags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'tag';
            tagElement.textContent = tag;
            chatTags.appendChild(tagElement);
        });
    }
}

// Load conversations
async function loadConversations() {
    try {
        conversationList.innerHTML = '<div class="loading">Loading conversations...</div>';
        
        const response = await fetch('/api/conversations');
        
        if (!response.ok) {
            throw new Error('Failed to load conversations');
        }
        
        const conversations = await response.json();
        
        // Clear loading indicator
        conversationList.innerHTML = '';
        
        if (conversations.length === 0) {
            conversationList.innerHTML = '<div class="empty-state">No conversations yet</div>';
            return;
        }
        
        // Add conversations to list
        conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conversation-item';
            item.dataset.id = conv.id;
            
            item.innerHTML = `
                <h3>${conv.title || 'Untitled Conversation'}</h3>
                <p>${conv.summary || 'No summary available'}</p>
                <div class="item-tags">
                    ${conv.tags.slice(0, 3).map(tag => `<span class="item-tag">${tag}</span>`).join('')}
                    ${conv.tags.length > 3 ? `<span class="item-tag">+${conv.tags.length - 3} more</span>` : ''}
                </div>
                <div class="conversation-meta">
                    <span>${formatDate(conv.created_at)}</span>
                    <span>${conv.message_count} messages</span>
                </div>
                <button class="btn icon delete-btn" title="Delete conversation">×</button>
            `;
            
            // Add click event
            item.addEventListener('click', () => {
                loadConversation(conv.id);
            });
            
            // Add delete button event
            const deleteBtn = item.querySelector('.delete-btn');
            deleteBtn.addEventListener('click', e => {
                deleteConversation(conv.id, e);
            });
            
            conversationList.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading conversations:', error);
        conversationList.innerHTML = '<div class="empty-state">Error loading conversations</div>';
    }
}

// Load episodic memories
async function loadEpisodicMemories() {
    try {
        episodicList.innerHTML = '<div class="loading">Loading memories...</div>';
        
        const response = await fetch('/api/memories?type=episodic');
        
        if (!response.ok) {
            throw new Error('Failed to load episodic memories');
        }
        
        const memories = await response.json();
        
        // Clear loading indicator
        episodicList.innerHTML = '';
        
        if (memories.length === 0) {
            episodicList.innerHTML = '<div class="empty-state">No episodic memories yet</div>';
            return;
        }
        
        // Add memories to list
        memories.forEach(memory => {
            const item = document.createElement('div');
            item.className = 'memory-item';
            item.dataset.id = memory.id;
            item.dataset.type = 'episodic';
            
            item.innerHTML = `
                <h3>Episodic Memory</h3>
                <p>${memory.content}</p>
                <div class="item-tags">
                    ${memory.tags.slice(0, 3).map(tag => `<span class="item-tag">${tag}</span>`).join('')}
                    ${memory.tags.length > 3 ? `<span class="item-tag">+${memory.tags.length - 3} more</span>` : ''}
                </div>
                <div class="memory-meta">
                    <span>${formatDate(memory.created_at)}</span>
                </div>
            `;
            
            // Add click event
            item.addEventListener('click', () => {
                showMemoryDetails(memory, 'episodic');
            });
            
            episodicList.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading episodic memories:', error);
        episodicList.innerHTML = '<div class="empty-state">Error loading memories</div>';
    }
}

// Load non-episodic memories
async function loadNonEpisodicMemories() {
    try {
        nonEpisodicList.innerHTML = '<div class="loading">Loading memories...</div>';
        
        const response = await fetch('/api/memories?type=non_episodic');
        
        if (!response.ok) {
            throw new Error('Failed to load non-episodic memories');
        }
        
        const memories = await response.json();
        
        // Clear loading indicator
        nonEpisodicList.innerHTML = '';
        
        if (memories.length === 0) {
            nonEpisodicList.innerHTML = '<div class="empty-state">No factual memories yet</div>';
            return;
        }
        
        // Add memories to list
        memories.forEach(memory => {
            const item = document.createElement('div');
            item.className = 'memory-item';
            item.dataset.id = memory.id;
            item.dataset.type = 'non_episodic';
            
            item.innerHTML = `
                <h3>Factual Memory</h3>
                <p>${memory.content}</p>
                <div class="item-tags">
                    ${memory.tags.slice(0, 3).map(tag => `<span class="item-tag">${tag}</span>`).join('')}
                    ${memory.tags.length > 3 ? `<span class="item-tag">+${memory.tags.length - 3} more</span>` : ''}
                </div>
                <div class="memory-meta">
                    <span>${formatDate(memory.created_at)}</span>
                    <span>Confidence: ${(memory.confidence * 100).toFixed(0)}%</span>
                </div>
            `;
            
            // Add click event
            item.addEventListener('click', () => {
                showMemoryDetails(memory, 'non_episodic');
            });
            
            nonEpisodicList.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading non-episodic memories:', error);
        nonEpisodicList.innerHTML = '<div class="empty-state">Error loading memories</div>';
    }
}

// Load tags
async function loadTags() {
    try {
        tagsCloud.innerHTML = '<div class="loading">Loading tags...</div>';
        
        const response = await fetch('/api/tags');
        
        if (!response.ok) {
            throw new Error('Failed to load tags');
        }
        
        const tags = await response.json();
        
        // Clear loading indicator
        tagsCloud.innerHTML = '';
        
        if (tags.length === 0) {
            tagsCloud.innerHTML = '<div class="empty-state">No tags yet</div>';
            return;
        }
        
        // Add tags to cloud
        tags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'tag-item';
            tagElement.innerHTML = `
                ${tag.tag} <span class="tag-count">${tag.count}</span>
            `;
            
            // Add click event
            tagElement.addEventListener('click', () => {
                searchAllMemories(tag.tag);
                
                // Switch to overview tab
                tabBtns.forEach(btn => btn.classList.remove('active'));
                document.querySelector('[data-tab="overview"]').classList.add('active');
                
                document.querySelectorAll('.tab-panel').forEach(panel => {
                    panel.classList.remove('active');
                });
                document.getElementById('overview-panel').classList.add('active');
                
                // Set search input
                memorySearch.value = tag.tag;
            });
            
            tagsCloud.appendChild(tagElement);
        });
    } catch (error) {
        console.error('Error loading tags:', error);
        tagsCloud.innerHTML = '<div class="empty-state">Error loading tags</div>';
    }
}

// Load memory counts
async function loadMemoryCounts() {
    try {
        const response = await fetch('/api/memories');
        
        if (!response.ok) {
            throw new Error('Failed to load memory counts');
        }
        
        const data = await response.json();
        
        if (data.counts) {
            conversationCount.textContent = data.counts.conversations || 0;
            episodicCount.textContent = data.counts.episodic || 0;
            nonEpisodicCount.textContent = data.counts.non_episodic || 0;
        }
    } catch (error) {
        console.error('Error loading memory counts:', error);
    }
}

// Search conversations
async function searchConversations(query) {
    try {
        conversationList.innerHTML = '<div class="loading">Searching...</div>';
        
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&type=conversations`);
        
        if (!response.ok) {
            throw new Error('Failed to search conversations');
        }
        
        const data = await response.json();
        
        // Clear loading indicator
        conversationList.innerHTML = '';
        
        const conversations = data.conversations || [];
        
        if (conversations.length === 0) {
            conversationList.innerHTML = '<div class="empty-state">No matching conversations found</div>';
            return;
        }
        
        // Add conversations to list
        conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conversation-item';
            item.dataset.id = conv.id;
            
            item.innerHTML = `
                <h3>${conv.title || 'Untitled Conversation'}</h3>
                <p>${conv.summary || 'No summary available'}</p>
                <div class="item-tags">
                    ${conv.tags.slice(0, 3).map(tag => `<span class="item-tag">${tag}</span>`).join('')}
                    ${conv.tags.length > 3 ? `<span class="item-tag">+${conv.tags.length - 3} more</span>` : ''}
                </div>
                <div class="conversation-meta">
                    <span>${formatDate(conv.created_at)}</span>
                    <span>${conv.message_count} messages</span>
                </div>
                <button class="btn icon delete-btn" title="Delete conversation">×</button>
            `;
            
            // Add click event
            item.addEventListener('click', () => {
                loadConversation(conv.id);
            });
            
            // Add delete button event
            const deleteBtn = item.querySelector('.delete-btn');
            deleteBtn.addEventListener('click', e => {
                deleteConversation(conv.id, e);
            });
            
            conversationList.appendChild(item);
        });
    } catch (error) {
        console.error('Error searching conversations:', error);
        conversationList.innerHTML = '<div class="empty-state">Error searching conversations</div>';
    }
}

// Search memories by type
async function searchMemories(type, query) {
    try {
        const container = type === 'episodic' ? episodicList : nonEpisodicList;
        container.innerHTML = '<div class="loading">Searching...</div>';
        
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&type=${type}`);
        
        if (!response.ok) {
            throw new Error(`Failed to search ${type} memories`);
        }
        
        const data = await response.json();
        
        // Clear loading indicator
        container.innerHTML = '';
        
        const memories = data[type] || [];
        
        if (memories.length === 0) {
            container.innerHTML = '<div class="empty-state">No matching memories found</div>';
            return;
        }
        
        // Add memories to list
        memories.forEach(memory => {
            const item = document.createElement('div');
            item.className = 'memory-item';
            item.dataset.id = memory.id;
            item.dataset.type = type;
            
            const title = type === 'episodic' ? 'Episodic Memory' : 'Factual Memory';
            
            item.innerHTML = `
                <h3>${title}</h3>
                <p>${memory.content}</p>
                <div class="item-tags">
                    ${memory.tags.slice(0, 3).map(tag => `<span class="item-tag">${tag}</span>`).join('')}
                    ${memory.tags.length > 3 ? `<span class="item-tag">+${memory.tags.length - 3} more</span>` : ''}
                </div>
                <div class="memory-meta">
                    <span>${formatDate(memory.created_at)}</span>
                    ${type === 'non_episodic' ? `<span>Confidence: ${(memory.confidence * 100).toFixed(0)}%</span>` : ''}
                </div>
            `;
            
            // Add click event
            item.addEventListener('click', () => {
                showMemoryDetails(memory, type);
            });
            
            container.appendChild(item);
        });
    } catch (error) {
        console.error(`Error searching ${type} memories:`, error);
        const container = type === 'episodic' ? episodicList : nonEpisodicList;
        container.innerHTML = '<div class="empty-state">Error searching memories</div>';
    }
}

// Search all memories
async function searchAllMemories(query) {
    try {
        memorySearchResults.innerHTML = '<div class="loading">Searching...</div>';
        
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            throw new Error('Failed to search memories');
        }
        
        const data = await response.json();
        
        // Clear loading indicator
        memorySearchResults.innerHTML = '';
        
        const conversations = data.conversations || [];
        const episodic = data.episodic || [];
        const nonEpisodic = data.non_episodic || [];
        
        // Check if we have any results
        if (conversations.length === 0 && episodic.length === 0 && nonEpisodic.length === 0) {
            memorySearchResults.innerHTML = '<div class="empty-state">No matching memories found</div>';
            return;
        }
        
        // Build results HTML
        let resultsHtml = '';
        
        // Add conversations
        if (conversations.length > 0) {
            resultsHtml += `
                <div class="search-result-category">
                    <h3>Conversations (${conversations.length})</h3>
                    <div class="conversation-list">
                    ${conversations.map(conv => `
                        <div class="conversation-item" data-id="${conv.id}">
                            <h3>${conv.title || 'Untitled Conversation'}</h3>
                            <p>${conv.summary || 'No summary available'}</p>
                            <div class="conversation-meta">
                                <span>${formatDate(conv.created_at)}</span>
                            </div>
                        </div>
                    `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Add episodic memories
        if (episodic.length > 0) {
            resultsHtml += `
                <div class="search-result-category">
                    <h3>Episodic Memories (${episodic.length})</h3>
                    <div class="memory-list">
                    ${episodic.map(memory => `
                        <div class="memory-item" data-id="${memory.id}" data-type="episodic">
                            <p>${memory.content}</p>
                            <div class="memory-meta">
                                <span>${formatDate(memory.created_at)}</span>
                            </div>
                        </div>
                    `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Add non-episodic memories
        if (nonEpisodic.length > 0) {
            resultsHtml += `
                <div class="search-result-category">
                    <h3>Factual Memories (${nonEpisodic.length})</h3>
                    <div class="memory-list">
                    ${nonEpisodic.map(memory => `
                        <div class="memory-item" data-id="${memory.id}" data-type="non_episodic">
                            <p>${memory.content}</p>
                            <div class="memory-meta">
                                <span>${formatDate(memory.created_at)}</span>
                                <span>Confidence: ${(memory.confidence * 100).toFixed(0)}%</span>
                            </div>
                        </div>
                    `).join('')}
                    </div>
                </div>
            `;
        }
        
        memorySearchResults.innerHTML = resultsHtml;
        
        // Add click events to conversations
        memorySearchResults.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                loadConversation(item.dataset.id);
            });
        });
        
        // Add click events to memories
        memorySearchResults.querySelectorAll('.memory-item').forEach(item => {
            item.addEventListener('click', async () => {
                try {
                    const response = await fetch(`/api/memories?type=${item.dataset.type}`);
                    
                    if (!response.ok) {
                        throw new Error(`Failed to load ${item.dataset.type} memories`);
                    }
                    
                    const memories = await response.json();
                    
                    const memory = memories.find(m => m.id === item.dataset.id);
                    
                    if (memory) {
                        showMemoryDetails(memory, item.dataset.type);
                    } else {
                        throw new Error('Memory not found');
                    }
                } catch (error) {
                    console.error('Error loading memory:', error);
                    alert('Sorry, there was an error loading the memory details.');
                }
            });
        });
    } catch (error) {
        console.error('Error searching memories:', error);
        memorySearchResults.innerHTML = '<div class="empty-state">Error searching memories</div>';
    }
}

// Show memory details in modal
function showMemoryDetails(memory, type) {
    // Set modal title
    modalTitle.textContent = type === 'episodic' ? 'Episodic Memory' : 'Factual Memory';
    
    // Set modal content
    modalBody.innerHTML = `
        <div class="memory-detail-content">
            ${memory.content}
        </div>
        <div class="memory-detail-meta">
            Created: ${formatDate(memory.created_at)}
            ${type === 'non_episodic' ? `<br>Confidence: ${(memory.confidence * 100).toFixed(0)}%` : ''}
            ${type === 'episodic' && memory.conversation_id ? `<br>Conversation: ${memory.conversation_id}` : ''}
        </div>
        <div class="memory-detail-tags">
            ${memory.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
        </div>
    `;
    
    // Show modal
    modal.classList.add('active');
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) {
        return '';
    }
    
    try {
        const date = new Date(dateString);
        const now = new Date();
        const yesterday = new Date(now);
        yesterday.setDate(now.getDate() - 1);
        
        // Check if date is today
        if (date.toDateString() === now.toDateString()) {
            return `Today, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
        }
        
        // Check if date is yesterday
        if (date.toDateString() === yesterday.toDateString()) {
            return `Yesterday, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
        }
        
        // Otherwise, format as date and time
        return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) + 
               ', ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        return dateString;
    }
}

// Format time for display
function formatTime(dateString) {
    if (!dateString) {
        return '';
    }
    
    try {
        const date = new Date(dateString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        return '';
    }
}

// Format message content (handle newlines, links, etc.)
function formatMessageContent(content) {
    if (!content) {
        return '';
    }
    
    // Convert newlines to <br>
    content = content.replace(/\n/g, '<br>');
    
    // Convert URLs to links
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    content = content.replace(urlRegex, url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
    
    return content;
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}