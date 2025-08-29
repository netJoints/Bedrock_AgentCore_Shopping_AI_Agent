from flask import Flask, request, jsonify, render_template_string
import subprocess
import json
import os
import re

app = Flask(__name__)

# HTML template for single-page chat UI - GOOD UI FROM PREVIOUS VERSION
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

            // Disable input and button while processing
            input.disabled = true;
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';

            // Add user message to chat
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
                // Re-enable input and button
                input.disabled = false;
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
                input.focus();
            });
        }

        // Allow Enter key to send message
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        // Focus on input when page loads
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
        # Basic request validation
        if not request.is_json:
            return jsonify({"response": "Invalid request format", "error": True})

        user_prompt = request.json.get('prompt')
        if not user_prompt:
            return jsonify({"response": "Please provide a valid prompt", "error": True})

        print(f"DEBUG - Processing prompt: {user_prompt}")

        # Step 1: Get AWS credentials using pybritive
        try:
            print("DEBUG - Getting AWS credentials...")
            creds_json = subprocess.check_output([
                "pybritive", "checkout",
                "aws_standalone_app_513826297540/513826297540 (aws_standalone_app_513826297540_environment)/AWS Admin Full Access",
                "-t", "agentic-ai"
            ], text=True, timeout=30)
            creds = json.loads(creds_json)
            print("DEBUG - AWS credentials obtained successfully")
        except subprocess.TimeoutExpired:
            print("DEBUG - Timeout getting AWS credentials")
            return jsonify({"response": "Timeout getting AWS credentials", "error": True})
        except subprocess.CalledProcessError as e:
            print(f"DEBUG - Failed to get AWS credentials: {e}")
            return jsonify({"response": f"Failed to get AWS credentials: {str(e)}", "error": True})
        except Exception as e:
            print(f"DEBUG - Error getting AWS credentials: {e}")
            return jsonify({"response": f"Error getting AWS credentials: {str(e)}", "error": True})

        # Step 2: Export credentials
        try:
            os.environ['AWS_ACCESS_KEY_ID'] = creds['AccessKeyId']
            os.environ['AWS_SECRET_ACCESS_KEY'] = creds['SecretAccessKey']
            os.environ['AWS_SESSION_TOKEN'] = creds['SessionToken']
            print("DEBUG - AWS credentials set in environment")
        except Exception as e:
            print(f"DEBUG - Error setting AWS credentials: {e}")
            return jsonify({"response": f"Error setting AWS credentials: {str(e)}", "error": True})

        # Step 3: Build prompt payload
        prompt_payload = json.dumps({"prompt": user_prompt})
        print(f"DEBUG - Prompt payload created: {prompt_payload}")

        # Step 4: Invoke agentcore
        try:
            print("DEBUG - Invoking agentcore...")
            result = subprocess.run([
                "agentcore", "invoke",
                "--agent", "async_shopping_strands",
                prompt_payload
            ], capture_output=True, text=True, check=True, timeout=60)
            print("DEBUG - Agentcore invoked successfully")
        except subprocess.TimeoutExpired:
            print("DEBUG - Timeout invoking agentcore")
            return jsonify({"response": "Timeout waiting for agent response", "error": True})
        except subprocess.CalledProcessError as e:
            print(f"DEBUG - Agentcore command failed: {e}")
            error_msg = f"Agentcore command failed: {str(e)}"
            if e.stderr:
                error_msg += f"\nError details: {e.stderr}"
                print(f"DEBUG - Agentcore stderr: {e.stderr}")
            return jsonify({"response": error_msg, "error": True})
        except Exception as e:
            print(f"DEBUG - Error invoking agentcore: {e}")
            return jsonify({"response": f"Error invoking agentcore: {str(e)}", "error": True})

        output = result.stdout
        print(f"DEBUG - Got output from agentcore (length: {len(output)})")
        
        # ENHANCED DEBUG: Print the full output to see its structure
        print("DEBUG - Full agentcore output:")
        print("=" * 80)
        print(output)
        print("=" * 80)

        # Step 5: Extract agent response with multiple parsing strategies
        if not output.strip():
            print("DEBUG - Empty output from agentcore")
            return jsonify({"response": "Agentcore returned no output. Please check agentcore logs or configuration.", "error": True})

        agent_reply = None

        # Strategy 1: Try to parse as direct JSON
        try:
            print("DEBUG - Strategy 1: Trying direct JSON parse...")
            response_data = json.loads(output)
            agent_reply = extract_text_from_response(response_data)
            if agent_reply:
                print("DEBUG - Strategy 1 successful")
        except json.JSONDecodeError:
            print("DEBUG - Strategy 1 failed: Not valid JSON")

        # Strategy 2: Look for Response: pattern (case-insensitive)
        if not agent_reply:
            try:
                print("DEBUG - Strategy 2: Looking for Response: pattern...")
                # Try various patterns
                patterns = [
                    r'Response:\s*({.*})',  # Response: followed by JSON
                    r'response:\s*({.*})',  # lowercase response
                    r'"response":\s*(\[.*?\])',  # response field in JSON
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, output, re.IGNORECASE | re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        print(f"DEBUG - Found pattern match, attempting to parse...")
                        response_data = json.loads(json_str)
                        agent_reply = extract_text_from_response(response_data)
                        if agent_reply:
                            print("DEBUG - Strategy 2 successful")
                            break
            except Exception as e:
                print(f"DEBUG - Strategy 2 failed: {e}")

        # Strategy 3: Look for any JSON object in the output
        if not agent_reply:
            try:
                print("DEBUG - Strategy 3: Looking for any JSON object...")
                # Find all JSON-like structures
                json_objects = re.findall(r'\{[^{}]*\}', output)
                for json_str in json_objects:
                    try:
                        data = json.loads(json_str)
                        agent_reply = extract_text_from_response(data)
                        if agent_reply:
                            print("DEBUG - Strategy 3 successful")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"DEBUG - Strategy 3 failed: {e}")

        # Strategy 4: Extract text field directly with regex
        if not agent_reply:
            print("DEBUG - Strategy 4: Direct text extraction with regex...")
            # Look for various text field patterns
            text_patterns = [
                r'"text"\s*:\s*"([^"]*(?:\\.[^"]*)*)"',
                r"'text'\s*:\s*'([^']*(?:\\.[^']*)*)'",
                r'"message"\s*:\s*"([^"]*(?:\\.[^"]*)*)"',
                r'"result"\s*:\s*"([^"]*(?:\\.[^"]*)*)"',
                r'"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"',
            ]
            
            for pattern in text_patterns:
                match = re.search(pattern, output)
                if match:
                    agent_reply = match.group(1)
                    # Unescape common sequences
                    agent_reply = unescape_string(agent_reply)
                    print(f"DEBUG - Strategy 4 successful with pattern: {pattern}")
                    break

        # Strategy 5: If output looks like plain text response
        if not agent_reply and not output.startswith('{') and not 'Response:' in output:
            print("DEBUG - Strategy 5: Treating as plain text...")
            # Check if it's just plain text (no JSON markers)
            if len(output) < 500 and not any(char in output for char in ['{', '}', '[', ']', '"']):
                agent_reply = output.strip()
                print("DEBUG - Strategy 5: Using output as plain text")

        # Final fallback
        if not agent_reply:
            print("DEBUG - All parsing strategies failed")
            # Log first 500 chars for debugging
            print(f"DEBUG - First 500 chars of output: {output[:500]}")
            return jsonify({
                "response": "I received a response but couldn't parse it properly. The system may need configuration adjustment.",
                "error": True
            })

        print(f"DEBUG - Final response length: {len(agent_reply)}")
        return jsonify({"response": agent_reply})

    except Exception as e:
        print(f"DEBUG - Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"response": f"Unexpected error: {str(e)}", "error": True})


def extract_text_from_response(data):
    """Helper function to extract text from various response formats"""
    try:
        # Handle different response structures
        if isinstance(data, dict):
            # Check for direct text field
            if "text" in data:
                return data["text"]
            
            # Check for result.content[0].text structure
            if "result" in data:
                result = data["result"]
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        if isinstance(content[0], dict) and "text" in content[0]:
                            return content[0]["text"]
                        elif isinstance(content[0], str):
                            return content[0]
            
            # Check for response array
            if "response" in data:
                responses = data["response"]
                if isinstance(responses, list) and len(responses) > 0:
                    # Handle byte string format
                    first_response = responses[0]
                    if isinstance(first_response, str):
                        # Handle b'...' format
                        if first_response.startswith("b'") and first_response.endswith("'"):
                            inner_json_str = first_response[2:-1]
                            inner_json_str = inner_json_str.encode().decode('unicode_escape')
                            inner_data = json.loads(inner_json_str)
                            return extract_text_from_response(inner_data)
                        else:
                            # Try parsing as JSON
                            try:
                                inner_data = json.loads(first_response)
                                return extract_text_from_response(inner_data)
                            except:
                                # Return as is if it's plain text
                                return first_response
            
            # Check for message field
            if "message" in data:
                return data["message"]
            
            # Check for content field
            if "content" in data:
                if isinstance(data["content"], str):
                    return data["content"]
                elif isinstance(data["content"], list) and len(data["content"]) > 0:
                    if isinstance(data["content"][0], str):
                        return data["content"][0]
                    elif isinstance(data["content"][0], dict) and "text" in data["content"][0]:
                        return data["content"][0]["text"]
        
        elif isinstance(data, list) and len(data) > 0:
            # If it's a list, try the first element
            return extract_text_from_response(data[0])
        
        elif isinstance(data, str):
            # If it's already a string, return it
            return data
            
    except Exception as e:
        print(f"DEBUG - Error in extract_text_from_response: {e}")
    
    return None


def unescape_string(s):
    """Helper function to unescape common escape sequences"""
    s = s.replace('\\"', '"')
    s = s.replace('\\\\', '\\')
    s = s.replace('\\n', '\n')
    s = s.replace('\\r', '\r')
    s = s.replace('\\t', '\t')
    s = s.replace("\\'", "'")
    return s


if __name__ == '__main__':
    app.run(debug=True)
