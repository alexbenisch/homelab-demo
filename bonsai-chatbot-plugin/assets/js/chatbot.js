/**
 * Bonsai Chatbot Widget JavaScript
 */
(function($) {
    'use strict';

    let isOpen = false;
    let isProcessing = false;

    /**
     * Initialize chatbot
     */
    function initChatbot() {
        const $toggle = $('#bonsai-chatbot-toggle');
        const $close = $('#bonsai-chatbot-close');
        const $widget = $('#bonsai-chatbot-widget');
        const $input = $('#bonsai-chatbot-input');
        const $send = $('#bonsai-chatbot-send');
        const $messages = $('#bonsai-chatbot-messages');

        // Toggle chat window
        $toggle.on('click', function() {
            openChat();
        });

        // Close chat window
        $close.on('click', function() {
            closeChat();
        });

        // Send message on button click
        $send.on('click', function() {
            sendMessage();
        });

        // Send message on Enter key
        $input.on('keypress', function(e) {
            if (e.which === 13 && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Show welcome message when first opened
        showWelcomeMessage();
    }

    /**
     * Open chat window
     */
    function openChat() {
        const $widget = $('#bonsai-chatbot-widget');
        const $toggle = $('#bonsai-chatbot-toggle');

        $widget.fadeIn(300);
        $toggle.fadeOut(200);
        isOpen = true;

        // Focus input
        setTimeout(function() {
            $('#bonsai-chatbot-input').focus();
        }, 350);
    }

    /**
     * Close chat window
     */
    function closeChat() {
        const $widget = $('#bonsai-chatbot-widget');
        const $toggle = $('#bonsai-chatbot-toggle');

        $widget.fadeOut(200);
        $toggle.fadeIn(300);
        isOpen = false;
    }

    /**
     * Show welcome message
     */
    function showWelcomeMessage() {
        const welcomeMessage = bonsaiChatbot.welcome_message || 'Hello! How can I help you today?';
        addMessage(welcomeMessage, 'bot');
    }

    /**
     * Send message to chatbot
     */
    function sendMessage() {
        if (isProcessing) {
            return;
        }

        const $input = $('#bonsai-chatbot-input');
        const message = $input.val().trim();

        if (!message) {
            return;
        }

        // Add user message to chat
        addMessage(message, 'user');

        // Clear input
        $input.val('');

        // Show typing indicator
        showTypingIndicator();

        isProcessing = true;

        // Send to backend
        $.ajax({
            url: bonsaiChatbot.ajax_url,
            type: 'POST',
            data: {
                action: 'bonsai_chatbot_send_message',
                nonce: bonsaiChatbot.nonce,
                message: message
            },
            success: function(response) {
                hideTypingIndicator();

                if (response.success) {
                    const botResponse = response.data.response;
                    const sources = response.data.sources || [];

                    addMessage(botResponse, 'bot', sources);
                } else {
                    const errorMessage = response.data.message || 'Sorry, I encountered an error. Please try again.';
                    addMessage(errorMessage, 'error');
                }

                isProcessing = false;
            },
            error: function(xhr, status, error) {
                hideTypingIndicator();
                addMessage('Sorry, I could not connect to the chatbot. Please try again later.', 'error');
                isProcessing = false;
            }
        });
    }

    /**
     * Add message to chat window
     */
    function addMessage(text, type, sources) {
        const $messages = $('#bonsai-chatbot-messages');
        const timestamp = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

        let messageClass = 'chatbot-message';
        if (type === 'user') {
            messageClass += ' user-message';
        } else if (type === 'bot') {
            messageClass += ' bot-message';
        } else if (type === 'error') {
            messageClass += ' error-message';
        }

        let messageHtml = `
            <div class="${messageClass}">
                <div class="message-content">${escapeHtml(text)}</div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;

        // Add sources if available
        if (sources && sources.length > 0) {
            let sourcesHtml = '<div class="message-sources"><strong>Sources:</strong><ul>';
            sources.forEach(function(source) {
                sourcesHtml += `<li>${escapeHtml(source)}</li>`;
            });
            sourcesHtml += '</ul></div>';
            messageHtml = messageHtml.replace('</div></div>', sourcesHtml + '</div></div>');
        }

        $messages.append(messageHtml);

        // Scroll to bottom
        scrollToBottom();
    }

    /**
     * Show typing indicator
     */
    function showTypingIndicator() {
        const $messages = $('#bonsai-chatbot-messages');
        const typingHtml = `
            <div class="chatbot-message bot-message typing-indicator" id="typing-indicator">
                <div class="message-content">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>
        `;
        $messages.append(typingHtml);
        scrollToBottom();
    }

    /**
     * Hide typing indicator
     */
    function hideTypingIndicator() {
        $('#typing-indicator').remove();
    }

    /**
     * Scroll messages to bottom
     */
    function scrollToBottom() {
        const $messages = $('#bonsai-chatbot-messages');
        $messages.scrollTop($messages[0].scrollHeight);
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Initialize on document ready
    $(document).ready(function() {
        initChatbot();
    });

})(jQuery);
