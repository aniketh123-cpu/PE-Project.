// DOM Elements
const loginBtn = document.querySelector('.login-btn');
const loginModal = document.getElementById('loginModal');
const closeModal = document.querySelector('.close');
const loginForm = document.getElementById('loginForm');
const chatbotInput = document.getElementById('userInput');
const sendMessageBtn = document.getElementById('sendMessage');
const chatMessages = document.getElementById('chatMessages');
const minimizeChatbot = document.getElementById('minimizeChatbot');

// Login Modal Functions
loginBtn.addEventListener('click', () => {
    loginModal.style.display = 'block';
});

closeModal.addEventListener('click', () => {
    loginModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === loginModal) {
        loginModal.style.display = 'none';
    }
});

loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    // Add login logic here
    console.log('Login submitted');
    loginModal.style.display = 'none';
});

// Chatbot Functions
function addMessage(message, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

sendMessageBtn.addEventListener('click', async () => {
    const message = chatbotInput.value.trim();
    if (message) {
        addMessage(message, true);
        chatbotInput.value = '';
        
        // Add API call to Gemini here
        try {
            const response = await processMessageWithGemini(message);
            addMessage(response);
        } catch (error) {
            addMessage('Sorry, I encountered an error. Please try again.');
        }
    }
});

chatbotInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessageBtn.click();
    }
});

// Minimize/Maximize Chatbot
let isChatbotMinimized = false;
minimizeChatbot.addEventListener('click', () => {
    const chatbotMessages = document.querySelector('.chatbot-messages');
    const chatbotInput = document.querySelector('.chatbot-input');
    
    if (isChatbotMinimized) {
        chatbotMessages.style.display = 'block';
        chatbotInput.style.display = 'flex';
        minimizeChatbot.textContent = '−';
    } else {
        chatbotMessages.style.display = 'none';
        chatbotInput.style.display = 'none';
        minimizeChatbot.textContent = '+';
    }
    
    isChatbotMinimized = !isChatbotMinimized;
});

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
}); 