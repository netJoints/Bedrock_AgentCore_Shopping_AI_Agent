from flask import Flask, request, jsonify, render_template_string
import subprocess
import json
import os
import re

app = Flask(__name__)

# HTML template with AWS Cloudscape Design System
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>AgentCore Chat</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    <!-- Cloudscape Design System -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@cloudscape-design/global-styles@1/index.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@cloudscape-design/components@3/index.min.css">
    
    <style>
        :root {
            --chat-max-width: 1200px;
        }
        
        body {
            margin: 0;
            padding: 0;
            background: var(--awsui-color-background-layout-main);
            min-height: 100vh;
        }
        
        .main-container {
            max-width: var(--chat-max-width);
            margin: 0 auto;
            padding: var(--awsui-space-l);
        }
        
        .chat-container {
            background: var(--awsui-color-background-container-content);
            border-radius: var(--awsui-border-radius-container);
            box-shadow: var(--awsui-shadow-container);
            height: calc(100vh - 100px);
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            padding: var(--awsui-space-l);
            border-bottom: 1px solid var(--awsui-color-border-divider-default);
            background: var(--awsui-color-background-container-header);
            border-radius: var(--awsui-border-radius-container) var(--awsui-border-radius-container) 0 0;
        }
        
        .chat-header h1 {
            margin: 0;
            font-size: var(--awsui-font-size-heading-l);
            color: var(--awsui-color-text-heading-default);
            font-weight: var(--awsui-font-weight-bold);
        }
        
        .chat-header p {
            margin: var(--awsui-space-xs) 0 0 0;
            color: var(--awsui-color-text-body-secondary);
            font-size: var(--awsui-font-size-body-m);
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: var(--awsui-space-l);
            background: var(--awsui-color-background-layout-main);
        }
        
        .message {
            margin-bottom: var(--awsui-space-m);
            animation: messageSlideIn 0.3s ease-out;
        }
        
        @keyframes messageSlideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message-content {
            padding: var(--awsui-space-m);
            border-radius: var(--awsui-border-radius-badge);
            position: relative;
            max-width: 70%;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: var(--awsui-color-background-badge-info);
            color: var(--awsui-color-text-interactive-default);
            margin-left: auto;
            border: 1px solid var(--awsui-color-border-badge-info);
        }
        
        .message.agent .message-content {
            background: var(--awsui-color-background-container-content);
            color: var(--awsui-color-text-body-default);
            border: 1px solid var(--awsui-color-border-container);
        }
        
        .message.error .message-content {
            background: var(--awsui-color-background-status-error);
            color: var(--awsui-color-text-status-error);
            border: 1px solid var(--awsui-color-border-status-error);
        }
        
        .message-label {
            font-size: var(--awsui-font-size-body-s);
            color: var(--awsui-color-text-body-secondary);
            margin-bottom: var(--awsui-space-xs);
            font-weight: var(--awsui-font-weight-bold);
        }
        
        .message.user .message-label {
            text-align: right;
        }
        
        .chat-input-container {
            padding: var(--awsui-space-l);
            border-top: 1px solid var(--awsui-color-border-divider-default);
            background: var(--awsui-color-background-container-content);
            border-radius: 0 0 var(--awsui-border-radius-container) var(--awsui-border-radius-container);
        }
        
        .input-wrapper {
            display: flex;
            gap: var(--awsui-space-s);
        }
        
        .awsui-input {
            flex: 1;
            padding: var(--awsui-space-s) var(--awsui-space-m);
            border: 1px solid var(--awsui-color-border-input-default);
            border-radius: var(--awsui-border-radius-input);
            font-size: var(--awsui-font-size-body-m);
            background: var(--awsui-color-background-input-default);
            color: var(--awsui-color-text-body-default);
            transition: all 0.2s ease;
        }
        
        .awsui-input:focus {
            outline: none;
            border-color: var(--awsui-color-border-input-focused);
            box-shadow: 0 0 0 4px var(--awsui-color-background-control-checked);
        }
        
        .awsui-input:disabled {
            background: var(--awsui-color-background-input-disabled);
            color: var(--awsui-color-text-interactive-disabled);
            cursor: not-allowed;
        }
        
        .awsui-button {
            padding: var(--awsui-space-s) var(--awsui-space-xl);
            background: var(--awsui-color-background-button-primary-default);
            color: var(--awsui-color-text-button-primary-default);
            border: none;
            border-radius: var(--awsui-border-radius-button);
            font-size: var(--awsui-font-size-body-m);
            font-weight: var(--awsui-font-weight-button);
            cursor: pointer;
            transition: all 0.2s ease;
            min-width: 100px;
        }
        
        .awsui-button:hover:not(:disabled) {
            background: var(--awsui-color-background-button-primary-hover);
        }
        
        .awsui-button:active:not(:disabled) {
            background: var(--awsui-color-background-button-primary-active);
        }
        
        .awsui-button:disabled {
            background: var(--awsui-color-background-button-primary-disabled);
            color: var(--awsui-color-text-button-primary-disabled);
            cursor: not-allowed;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: var(--awsui-space-xs);
            padding: var(--awsui-space-xs) 0;
            font-size: var(--awsui-font-size-body-s);
            color: var(--awsui-color-text-body-secondary);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--awsui-color-text-status-inactive);
        }
        
        .status-dot.active {
            background: var(--awsui-color-text-status-success);
            animation: pulse 1.5s infinite;
        }
        
        .status-dot.processing {
            background: var(--awsui-color-text-status-warning);
            animation: pulse 0.8s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .typing-indicator {
            display: none;
            padding: var(--awsui-space-m);
        }
        
        .typing-indicator.show {
            display: block;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--awsui-color-text-body-secondary);
            animation: typing 1.4s infinite;
        }
        
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        
        /* Scrollbar styling */
        .chat-messages::-webkit-scrollbar {
            width: 8px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: var(--awsui-color-background-container-content);
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: var(--awsui-color-border-divider-default);
            border-radius: 4px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: var(--awsui-color-text-body-secondary);
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="chat-container">
            <div class="chat-header">
                <h1>🤖 AgentCore Shopping Assistant</h1>
                <p>Powered by AWS Bedrock • Ask me anything about Amazon shopping</p>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <!-- Messages will appear here -->
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                <div class="message agent">
                    <div class="message-label">Agent is typing</div>
                    <div class="message-content">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="chat-input-container">
                <div class="status-indicator">
                    <span class="status-dot active" id="statusDot"></span>
                    <span id="statusText">Ready to chat</span>
                </div>
                <div class="input-wrapper">
                    <input 
                        type="text" 
                        class="awsui-input" 
                        id="userInput" 
                        placeholder="Type your message here..."
                        autocomplete="off"
                    >
                    <button class="awsui-button" id="sendButton" onclick="sendMessage()">
                        Send
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let isProcessing = false;
        
        function updateStatus(status, text) {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            statusDot.className = 'status-dot';
            
            switch(status) {
                case 'active':
                    statusDot.classList.add('active');
                    break;
                case 'processing':
                    statusDot.classList.add('processing');
                    break;
                default:
                    break;
            }
            
            statusText.textContent = text;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function addMessage(content, type = 'agent') {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const labelDiv = document.createElement('div');
            labelDiv.className = 'message-label';
            labelDiv.textContent = type === 'user' ? 'You' : (type === 'error' ? 'Error' : 'Agent');
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(labelDiv);
            messageDiv.appendChild(contentDiv);
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function showTypingIndicator() {
            document.getElementById('typingIndicator').classList.add('show');
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function hideTypingIndicator() {
            document.getElementById('typingIndicator').classList.remove('show');
        }

        function sendMessage() {
            if (isProcessing) return;
            
            const input = document.getElementById('userInput');
            const sendButton = document.getElementById('sendButton');
            const userMessage = input.value.trim();

            if (!userMessage) return;

            isProcessing = true;
            input.disabled = true;
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';
            updateStatus('processing', 'Processing your message...');

            addMessage(userMessage, 'user');
            input.value = '';
            
            showTypingIndicator();

            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: userMessage })
            })
            .then(response => response.json())
            .then(data => {
                hideTypingIndicator();
                if (data.error) {
                    addMessage(data.response, 'error');
                    updateStatus('active', 'Error occurred - Ready to retry');
                } else {
                    addMessage(data.response, 'agent');
                    updateStatus('active', 'Ready to chat');
                }
            })
            .catch(error => {
                hideTypingIndicator();
                console.error('Error:', error);
                addMessage(`Failed to get response: ${error.message}`, 'error');
                updateStatus('active', 'Connection error - Ready to retry');
            })
            .finally(() => {
                isProcessing = false;
                input.disabled = false;
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
                input.focus();
            });
        }

        // Keyboard shortcuts
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Focus input on load
        window.onload = function() {
            document.getElementById('userInput').focus();
            addMessage('Hello! I\'m your Amazon shopping assistant. How can I help you today?', 'agent');
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        if not request.is_json:
            return jsonify({"response": "Invalid request format", "error": True})

        user_prompt = request.json.get('prompt')
        if not user_prompt:
            return jsonify({"response": "Please provide a valid prompt", "error": True})

        # Get AWS credentials
        creds_json = subprocess.check_output([
            "pybritive", "checkout",
            "aws_standalone_app_513826297540/513826297540 (aws_standalone_app_513826297540_environment)/AWS Admin Full Access",
            "-t", "agentic-ai"
        ], text=True, timeout=30)
        creds = json.loads(creds_json)

        # Set credentials
        os.environ['AWS_ACCESS_KEY_ID'] = creds['AccessKeyId']
        os.environ['AWS_SECRET_ACCESS_KEY'] = creds['SecretAccessKey']
        os.environ['AWS_SESSION_TOKEN'] = creds['SessionToken']

        # Invoke agentcore
        prompt_payload = json.dumps({"prompt": user_prompt})
        result = subprocess.run([
            "agentcore", "invoke",
            "--agent", "async_shopping_strands",
            prompt_payload
        ], capture_output=True, text=True, check=True, timeout=60)

        output = result.stdout
        if not output.strip():
            return jsonify({"response": "No output from agentcore", "error": True})

        # Parse response
        agent_reply = None
        
        # Try direct JSON parse
        try:
            response_data = json.loads(output)
            agent_reply = extract_text_from_response(response_data)
        except json.JSONDecodeError:
            pass

        # Try regex extraction
        if not agent_reply:
            response_match = re.search(r'"response":\s*\[\s*"(b\'.*?\')"\s*\]', output, re.DOTALL)
            if response_match:
                response_item = response_match.group(1)
                if response_item.startswith("b'") and response_item.endswith("'"):
                    inner_json_str = response_item[2:-1]
                    inner_json_str = inner_json_str.replace('\\"', '"').replace("\\'", "'")
                    inner_json_str = inner_json_str.replace('\\\\n', '\n').replace('\\n', '\n')
                    inner_json_str = inner_json_str.replace('\\\\', '\\')
                    
                    try:
                        inner_data = json.loads(inner_json_str)
                        if "result" in inner_data and "content" in inner_data["result"]:
                            content = inner_data["result"]["content"]
                            if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                                agent_reply = content[0]["text"]
                    except json.JSONDecodeError:
                        text_match = re.search(r'"text":\s*"([^"]*(?:\\.[^"]*)*)"', inner_json_str)
                        if text_match:
                            agent_reply = text_match.group(1)

        # Fallback to plain text
        if not agent_reply and len(output) < 500 and not any(char in output for char in ['{', '}', '[', ']', '"']):
            agent_reply = output.strip()

        if not agent_reply:
            return jsonify({"response": "Could not parse response", "error": True})

        # Clean up the text formatting
        agent_reply = clean_agent_text(agent_reply)

        return jsonify({"response": agent_reply})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}", "error": True})


def clean_agent_text(text):
    """Clean up escape sequences and formatting in agent responses"""
    
    # Handle backslash-space patterns that should be line breaks
    # Replace "\ \ " with double line breaks (paragraph breaks)
    text = text.replace('\\ \\ ', '\n\n')
    
    # Handle numbered lists - backslash before number
    text = re.sub(r'\\\s+(\d+\.)', r'\n\1', text)
    
    # Handle colon followed by backslash (typically before lists)
    text = text.replace(':\\\\', ':\n')
    text = text.replace(':\\ ', ':\n')
    
    # Handle single backslash-space (general line break)
    text = text.replace('\\ ', '\n')
    
    # Clean up escape sequences
    text = text.replace('\\n\\n', '\n\n')  # Double newlines
    text = text.replace('\\n', '\n')       # Single newlines
    text = text.replace("\\'", "'")        # Escaped single quotes
    text = text.replace('\\"', '"')        # Escaped double quotes
    text = text.replace('\\t', '\t')       # Tabs
    
    # Handle any remaining double backslashes
    text = text.replace('\\\\', '\\')
    
    # Remove trailing backslash if present
    if text.endswith('\\'):
        text = text[:-1]
    
    return text


def extract_text_from_response(data):
    """Extract text from various response formats"""
    if isinstance(data, dict):
        if "text" in data:
            return data["text"]
        if "result" in data and isinstance(data["result"], dict):
            result = data["result"]
            if "content" in result and isinstance(result["content"], list):
                content = result["content"]
                if len(content) > 0 and isinstance(content[0], dict) and "text" in content[0]:
                    return content[0]["text"]
        if "response" in data and isinstance(data["response"], list):
            if len(data["response"]) > 0:
                response_item = data["response"][0]
                if isinstance(response_item, str) and response_item.startswith("b'"):
                    # Handle byte string format
                    inner_json_str = response_item[2:]
                    if inner_json_str.endswith("'"):
                        inner_json_str = inner_json_str[:-1]
                    inner_json_str = inner_json_str.replace('\\"', '"').replace("\\'", "'")
                    inner_json_str = inner_json_str.replace('\\\\n', '\n').replace('\\n', '\n')
                    inner_json_str = inner_json_str.replace('\\\\', '\\')
                    try:
                        inner_data = json.loads(inner_json_str)
                        return extract_text_from_response(inner_data)
                    except:
                        return response_item
    return None


if __name__ == '__main__':
    app.run(debug=True)
