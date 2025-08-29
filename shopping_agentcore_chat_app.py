from flask import Flask, request, jsonify, render_template_string
import subprocess
import json
import os

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

        # Step 5: Extract agent response - FIXED FOR AGENTCORE CLI OUTPUT
        if not output.strip():
            print("DEBUG - Empty output from agentcore")
            return jsonify({"response": "Agentcore returned no output. Please check agentcore logs or configuration.", "error": True})

        agent_reply = None

        try:
            print("DEBUG - Attempting to parse agentcore CLI output...")

            # The agentcore CLI output has this structure:
            # Payload: { "prompt": "Hello" }
            # Session ID: xxx
            # Response: { ... "response": [ "b'{\"result\": ...}'" ] }

            # Find the Response JSON section
            response_start = output.find('Response: {')
            if response_start != -1:
                print("DEBUG - Found 'Response: {' in output")

                # Extract from 'Response: ' onwards
                json_start = response_start + 10  # Skip 'Response: '
                json_part = output[json_start:]

                print(f"DEBUG - Parsing JSON part (first 200 chars): {json_part[:200]}...")

                # Parse the response JSON
                response_data = json.loads(json_part)
                print("DEBUG - Successfully parsed response JSON")

                # Navigate to response array
                if "response" in response_data:
                    responses = response_data["response"]
                    print(f"DEBUG - Found response array with {len(responses)} items")

                    if isinstance(responses, list) and len(responses) > 0:
                        # Get the first response (should be a byte string representation)
                        first_response = responses[0]
                        print(f"DEBUG - First response type: {type(first_response)}")
                        print(f"DEBUG - First response (first 100 chars): {str(first_response)[:100]}...")

                        # Handle the byte string format: b'{"result": {...}}'
                        if isinstance(first_response, str):
                            if first_response.startswith("b'") and first_response.endswith("'"):
                                # Remove b'...' wrapper
                                inner_json_str = first_response[2:-1]
                                print("DEBUG - Removed b'...' wrapper")

                                # Unescape the string
                                inner_json_str = inner_json_str.encode().decode('unicode_escape')
                                print("DEBUG - Unescaped JSON string")

                                # Parse the inner JSON
                                inner_data = json.loads(inner_json_str)
                                print("DEBUG - Parsed inner JSON successfully")

                                # Extract the text from result.content[0].text
                                if "result" in inner_data:
                                    result = inner_data["result"]
                                    if "content" in result and isinstance(result["content"], list):
                                        content_list = result["content"]
                                        if len(content_list) > 0 and "text" in content_list[0]:
                                            agent_reply = content_list[0]["text"]
                                            print("DEBUG - Successfully extracted text from response")
                                        else:
                                            print("DEBUG - Content list is empty or missing 'text' field")
                                    else:
                                        print("DEBUG - Missing 'content' field or not a list")
                                else:
                                    print("DEBUG - Missing 'result' field in inner JSON")
                            else:
                                print("DEBUG - Response doesn't have b'...' format, trying direct parse")
                                # Try parsing directly
                                try:
                                    inner_data = json.loads(first_response)
                                    if "result" in inner_data and "content" in inner_data["result"]:
                                        content = inner_data["result"]["content"]
                                        if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                                            agent_reply = content[0]["text"]
                                except:
                                    print("DEBUG - Direct parsing failed")
                        else:
                            print(f"DEBUG - Unexpected response type: {type(first_response)}")
                    else:
                        print("DEBUG - Response is not a list or is empty")
                else:
                    print("DEBUG - No 'response' field found in parsed JSON")
            else:
                print("DEBUG - Could not find 'Response: {' pattern in output")

        except json.JSONDecodeError as e:
            print(f"DEBUG - JSON parsing error: {e}")
        except Exception as e:
            print(f"DEBUG - General parsing error: {e}")
            import traceback
            traceback.print_exc()

        # If parsing failed, try regex fallback
        if not agent_reply:
            print("DEBUG - Trying regex fallback to extract text...")
            import re

            # Look for "text": "..." pattern
            text_pattern = r'"text":\s*"([^"]*(?:\\.[^"]*)*)"'
            match = re.search(text_pattern, output)
            if match:
                agent_reply = match.group(1)
                # Unescape common sequences
                agent_reply = agent_reply.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n').replace("\\'", "'")
                print("DEBUG - Successfully extracted text using regex")
            else:
                print("DEBUG - Regex fallback also failed")

        # Final fallback - return clean error message
        if not agent_reply:
            print("DEBUG - All parsing methods failed, returning error message")
            return jsonify({"response": "I'm having trouble processing the response right now. Please try again.", "error": True})

        print(f"DEBUG - Final response length: {len(agent_reply)}")
        return jsonify({"response": agent_reply})

    except Exception as e:
        print(f"DEBUG - Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"response": f"Unexpected error: {str(e)}", "error": True})

if __name__ == '__main__':
    app.run(debug=True)
