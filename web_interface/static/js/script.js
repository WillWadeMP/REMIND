// Global variables
let conversationId = new Date().toISOString().replace(/[-:.TZ]/g, '');
let episodicMemories = [];
let nonEpisodicMemories = [];
let allHooks = [];

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.memory-tab-content');
const episodicMemoriesList = document.getElementById('episodic-memories');
const nonEpisodicMemoriesList = document.getElementById('non-episodic-memories');
const hooksList = document.getElementById('hooks-list');
const episodicSearch = document.getElementById('episodic-search');
const nonEpisodicSearch = document.getElementById('non-episodic-search');
const modal = document.getElementById('memory-detail-modal');
const modalClose = document.querySelector('.close-button');
const modalTitle = document.getElementById('modal-title');
const modalContent = document.getElementById('modal-content');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Load memories
    loadMemories();
    
    // Add event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Activate the selected tab
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show the corresponding content
            const tabId = button.getAttribute('data-tab');
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });
    
    episodicSearch.addEventListener('input', filterEpisodicMemories);
    nonEpisodicSearch.addEventListener('input', filterNonEpisodicMemories);
    
    modalClose.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Send a message to the chat
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    userInput.value = '';
    
    try {
        // Show typing indicator
        const typingIndicator = addMessageToChat('assistant', '...', true);
        
        // Send message to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                conversation_id: conversationId
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        chatMessages.removeChild(typingIndicator);
        
        // Add assistant message to chat
        addMessageToChat('assistant', data.response);
        
        // Update memories
        loadMemories();
        
    } catch (error) {
        console.error('Error:', error);
        // Remove typing indicator if it exists
        const indicator = document.querySelector('.message.assistant.typing');
        if (indicator) {
            chatMessages.removeChild(indicator);
        }
        
        // Add error message
        addMessageToChat('system', 'Sorry, there was an error processing your message. Please try again.');
    }
}

// Add a message to the chat
function addMessageToChat(role, content, isTyping = false) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}`;
    
    if (isTyping) {
        messageElement.classList.add('typing');
    }
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('p');
    messageText.textContent = content;
    
    messageContent.appendChild(messageText);
    
    if (!isTyping) {
        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = moment().format('HH:mm');
        messageContent.appendChild(timestamp);
    }
    
    messageElement.appendChild(messageContent);
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageElement;
}

// Load memories from the API
async function loadMemories() {
    try {
        const response = await fetch('/api/memories');
        if (!response.ok) {
            throw new Error('Failed to load memories');
        }
        
        const data = await response.json();
        
        // Update memory arrays
        episodicMemories = data.episodic_memories;
        nonEpisodicMemories = data.non_episodic_memories;
        
        // Load hooks
        await loadHooks();
        
        // Display memories
        displayEpisodicMemories();
        displayNonEpisodicMemories();
        
    } catch (error) {
        console.error('Error loading memories:', error);
        episodicMemoriesList.innerHTML = '<div class="error">Error loading memories</div>';
        nonEpisodicMemoriesList.innerHTML = '<div class="error">Error loading memories</div>';
    }
}

// Load memory hooks from the API
async function loadHooks() {
    try {
        const response = await fetch('/api/memories/hooks');
        if (!response.ok) {
            throw new Error('Failed to load hooks');
        }
        
        const data = await response.json();
        allHooks = data.hooks;
        
        // Display hooks
        displayHooks();
        
    } catch (error) {
        console.error('Error loading hooks:', error);
        hooksList.innerHTML = '<div class="error">Error loading hooks</div>';
    }
}

// Display episodic memories
function displayEpisodicMemories(filter = '') {
    episodicMemoriesList.innerHTML = '';
    
    const filteredMemories = filter ? 
        episodicMemories.filter(memory => 
            (memory.summary && memory.summary.toLowerCase().includes(filter.toLowerCase())) ||
            (memory.content && memory.content.toLowerCase().includes(filter.toLowerCase())) ||
            (memory.hooks && memory.hooks.some(hook => hook.toLowerCase().includes(filter.toLowerCase())))
        ) : 
        episodicMemories;
    
    if (filteredMemories.length === 0) {
        episodicMemoriesList.innerHTML = '<div class="empty">No episodic memories found</div>';
        return;
    }
    
    filteredMemories.forEach(memory => {
        const memoryItem = document.createElement('div');
        memoryItem.className = 'memory-item';
        memoryItem.onclick = () => showMemoryDetails(memory, 'Episodic Memory');
        
        const title = document.createElement('div');
        title.className = 'title';
        title.textContent = `Memory from ${formatDate(memory.timestamp)}`;
        
        const summary = document.createElement('div');
        summary.className = 'summary';
        summary.textContent = memory.summary || 'No summary available';
        
        const metadata = document.createElement('div');
        metadata.className = 'metadata';
        metadata.textContent = `Conversation ID: ${memory.conversation_id || 'Unknown'}`;
        
        memoryItem.appendChild(title);
        memoryItem.appendChild(summary);
        memoryItem.appendChild(metadata);
        
        // Add hooks if available
        if (memory.hooks && memory.hooks.length > 0) {
            const hooksContainer = document.createElement('div');
            hooksContainer.className = 'hooks';
            
            memory.hooks.slice(0, 5).forEach(hook => {
                const hookElement = document.createElement('span');
                hookElement.className = 'hook';
                hookElement.textContent = hook;
                hooksContainer.appendChild(hookElement);
            });
            
            if (memory.hooks.length > 5) {
                const moreHooks = document.createElement('span');
                moreHooks.className = 'hook more';
                moreHooks.textContent = `+${memory.hooks.length - 5} more`;
                hooksContainer.appendChild(moreHooks);
            }
            
            memoryItem.appendChild(hooksContainer);
        }
        
        episodicMemoriesList.appendChild(memoryItem);
    });
}

// Display non-episodic memories
function displayNonEpisodicMemories(filter = '') {
    nonEpisodicMemoriesList.innerHTML = '';
    
    const filteredMemories = filter ? 
        nonEpisodicMemories.filter(memory => 
            (memory.content && memory.content.toLowerCase().includes(filter.toLowerCase())) ||
            (memory.hooks && memory.hooks.some(hook => hook.toLowerCase().includes(filter.toLowerCase())))
        ) : 
        nonEpisodicMemories;
    
    if (filteredMemories.length === 0) {
        nonEpisodicMemoriesList.innerHTML = '<div class="empty">No non-episodic memories found</div>';
        return;
    }
    
    filteredMemories.forEach(memory => {
        const memoryItem = document.createElement('div');
        memoryItem.className = 'memory-item';
        memoryItem.onclick = () => showMemoryDetails(memory, 'Non-Episodic Memory');
        
        const title = document.createElement('div');
        title.className = 'title';
        title.textContent = memory.content && memory.content.length > 50 ? 
            memory.content.substring(0, 50) + '...' : 
            memory.content || 'No content available';
        
        const metadata = document.createElement('div');
        metadata.className = 'metadata';
        metadata.textContent = `Created: ${formatDate(memory.timestamp)}`;
        
        memoryItem.appendChild(title);
        memoryItem.appendChild(metadata);
        
        // Add hooks if available
        if (memory.hooks && memory.hooks.length > 0) {
            const hooksContainer = document.createElement('div');
            hooksContainer.className = 'hooks';
            
            memory.hooks.slice(0, 5).forEach(hook => {
                const hookElement = document.createElement('span');
                hookElement.className = 'hook';
                hookElement.textContent = hook;
                hooksContainer.appendChild(hookElement);
            });
            
            if (memory.hooks.length > 5) {
                const moreHooks = document.createElement('span');
                moreHooks.className = 'hook more';
                moreHooks.textContent = `+${memory.hooks.length - 5} more`;
                hooksContainer.appendChild(moreHooks);
            }
            
            memoryItem.appendChild(hooksContainer);
        }
        
        nonEpisodicMemoriesList.appendChild(memoryItem);
    });
}

// Display memory hooks
function displayHooks() {
    hooksList.innerHTML = '';
    
    if (allHooks.length === 0) {
        hooksList.innerHTML = '<div class="empty">No hooks found</div>';
        return;
    }
    
    // Sort hooks alphabetically
    allHooks.sort();
    
    allHooks.forEach(hook => {
        const hookElement = document.createElement('span');
        hookElement.className = 'hook';
        hookElement.textContent = hook;
        hookElement.onclick = () => filterMemoriesByHook(hook);
        
        hooksList.appendChild(hookElement);
    });
}

// Filter episodic memories by search input
function filterEpisodicMemories() {
    const filter = episodicSearch.value.trim();
    displayEpisodicMemories(filter);
}

// Filter non-episodic memories by search input
function filterNonEpisodicMemories() {
    const filter = nonEpisodicSearch.value.trim();
    displayNonEpisodicMemories(filter);
}

// Filter memories by hook
function filterMemoriesByHook(hook) {
    // Set the search inputs to the hook value
    episodicSearch.value = hook;
    nonEpisodicSearch.value = hook;
    
    // Filter memories
    filterEpisodicMemories();
    filterNonEpisodicMemories();
    
    // Switch to episodic tab
    tabButtons[0].click();
}

// Show memory details in a modal
function showMemoryDetails(memory, type) {
    // Set modal title
    modalTitle.textContent = type;
    
    // Build modal content
    let html = '';
    
    if (type === 'Episodic Memory') {
        html += `
            <div class="section">
                <div class="section-title">Time</div>
                <div>${formatDate(memory.timestamp)}</div>
            </div>
            
            <div class="section">
                <div class="section-title">Summary</div>
                <div>${memory.summary || 'No summary available'}</div>
            </div>
            
            <div class="section">
                <div class="section-title">Full Content</div>
                <div>${formatContent(memory.content)}</div>
            </div>
        `;
    } else {
        html += `
            <div class="section">
                <div class="section-title">Time</div>
                <div>${formatDate(memory.timestamp)}</div>
            </div>
            
            <div class="section">
                <div class="section-title">Content</div>
                <div>${memory.content || 'No content available'}</div>
            </div>
        `;
    }
    
    // Add hooks
    if (memory.hooks && memory.hooks.length > 0) {
        html += `
            <div class="section">
                <div class="section-title">Memory Hooks</div>
                <div class="hooks">
                    ${memory.hooks.map(hook => `<span class="hook">${hook}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    // Add metadata (file path)
    if (memory.file_path) {
        html += `
            <div class="section">
                <div class="section-title">Memory ID</div>
                <div>${memory.file_path}</div>
            </div>
        `;
    }
    
    modalContent.innerHTML = html;
    
    // Show modal
    modal.style.display = 'block';
}

// Format date for display
function formatDate(dateStr) {
    if (!dateStr) return 'Unknown date';
    
    try {
        return moment(dateStr).format('MMMM D, YYYY [at] h:mm A');
    } catch (e) {
        return dateStr;
    }
}

// Format content for display
function formatContent(content) {
    if (!content) return 'No content available';
    
    // Replace newlines with HTML line breaks
    return content.replace(/\n/g, '<br>');
}