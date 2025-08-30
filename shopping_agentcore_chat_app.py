from flask import Flask, request, jsonify, render_template_string
import subprocess
import json
import os
import re

app = Flask(__name__)

# HTML template for single-page chat UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AgentCore Chat</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        #chatbox {
            border: 1px solid #ccc;
            padding: 15px;
            height: 400px;
            overflow-y: scroll;
            background-color: #fafafa;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 6px;
            white-space: pre-wrap;  /* Preserve formatting and line breaks */
        }
        .user {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
        .agent {
            background-color: #e8f5e8;
            border-left: 4px solid #4caf50;
        }
        .error {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            color: #c62828;
        }
        .input-container {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        #userInput {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        #sendButton {
            padding: 10px 20px;
            background-color: #2196f3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        #sendButton:hover {
            background-color: #1976d2;
        }
        #sendButton:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Chat with AgentCore</h2>
        <div id="chatbox"></div>
        <div class="input-container">
            <input type="text" id="userInput" placeholder="Type your message here...">
            <button id="sendButton" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function addMessage(content, isUser, isError = false) {
            const chatbox = document.getElementById('chatbox');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'agent'} ${isError ? 'error' : ''}`;

            const label = isUser ? 'You' : (isError ? 'Error' : 'Agent');
            const escapedContent = escapeHtml(content);
            messageDiv.innerHTML = `<b>${label}:</b> ${escapedContent}`;

            chatbox.appendChild(messageDiv);
            chatbox.scrollTop = chatbox.scrollHeight;
        }

        function sendMessage() {
            const input = document.getElementById('userInput');
            const sendButton = document.getElementById('sendButton');
            const userMessage = input.value.trim();

            if (!userMessage) return;

            input.disabled = true;
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';

            addMessage(userMessage, true);
            input.value = '';

            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: userMessage })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addMessage(data.response, false, true);
                } else {
                    addMessage(data.response, false);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage(`Failed to get response: ${error.message}`, false, true);
            })
            .finally(() => {
                input.disabled = false;
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
                input.focus();
            });
        }

        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        window.onload = function() {
            document.getElementById('userInput').focus();
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
