# LMArena-to-API Setup Guide

Welcome to the comprehensive setup guide for LMArena-to-API! This document will walk you through the complete installation and configuration process to get your API bridge up and running.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Starting the Server](#starting-the-server)
5. [Browser Setup](#browser-setup)
6. [Session ID Capture](#session-id-capture)
7. [Model List Updates](#model-list-updates)
8. [Testing the API](#testing-the-api)
9. [Integration Examples](#integration-examples)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Features](#advanced-features)

---

## Prerequisites

Before you begin, ensure you have the following:

### Required Software

1. **Python 3.8 or higher**
   - Check your Python version:
     ```bash
     python --version
     # or
     python3 --version
     ```
   - Download from [python.org](https://www.python.org/downloads/) if needed

2. **A Modern Web Browser**
   - Google Chrome (recommended)
   - Mozilla Firefox
   - Microsoft Edge
   - Any Chromium-based browser

3. **Tampermonkey Extension**
   - Install from [tampermonkey.net](https://www.tampermonkey.net/)
   - Available for Chrome, Firefox, Edge, Safari, and Opera

4. **Git** (for cloning the repository)
   - Download from [git-scm.com](https://git-scm.com/downloads)

### System Requirements

- **RAM**: 2GB minimum (4GB+ recommended)
- **Disk Space**: 500MB for the project and dependencies
- **Network**: Stable internet connection to access LMArena.ai

---

## Installation

### Step 1: Clone the Repository

Open your terminal (Command Prompt, PowerShell, or Terminal app) and run:

```bash
git clone https://github.com/lianues/LMArena-to-api.git
cd LMArena-to-api
```

### Step 2: Create a Virtual Environment

Creating a virtual environment keeps your project dependencies isolated.

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` prefix in your terminal prompt, indicating the virtual environment is active.

### Step 3: Install Dependencies

With the virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

This will install:
- `fastapi` - Modern web framework for building APIs
- `uvicorn[standard]` - ASGI server for running FastAPI
- `requests` - HTTP library for making requests
- `aiohttp` - Async HTTP client/server
- `packaging` - Version comparison utilities
- `selenium` - Browser automation (for Docker features)

### Step 4: Verify Installation

Check that FastAPI was installed correctly:

```bash
python -c "import fastapi; print('FastAPI version:', fastapi.__version__)"
```

---

## Configuration

The project uses several configuration files. Let's set them up properly.

### Understanding Configuration Files

- **`config.jsonc`** - Main configuration file with global settings
- **`models.json`** - Maps model names to LMArena model IDs (required)
- **`model_endpoint_map.json`** - Advanced per-model session mapping (optional)
- **`available_models.json`** - Generated reference list of available models (auto-generated)

### Step 1: Configure `config.jsonc`

The default `config.jsonc` should work out of the box, but here are the key settings you might want to adjust:

```jsonc
{
  // Session IDs - These will be automatically updated by id_updater.py
  "session_id": "your-session-id-here",
  "message_id": "your-message-id-here",
  
  // API Security - Set a custom API key to protect your server
  "api_key": "",  // Leave empty for no authentication
  
  // Feature Flags
  "bypass_enabled": true,          // Attempt to bypass content filters
  "tavern_mode_enabled": false,    // Enable for SillyTavern compatibility
  "enable_auto_update": true,      // Check for updates on startup
  "enable_idle_restart": true,     // Auto-restart after idle timeout
  
  // Timeout Settings
  "stream_response_timeout_seconds": 360,  // Max wait time for responses
  "idle_restart_timeout_seconds": -1,      // -1 disables idle restart
  
  // Model Mapping Behavior
  "use_default_ids_if_mapping_not_found": true  // Fallback to default IDs
}
```

**Important Settings Explained:**

- **`api_key`**: If set, clients must provide this key in the `Authorization: Bearer <key>` header
- **`bypass_enabled`**: Injects an empty message to try bypassing LMArena's content filters
- **`tavern_mode_enabled`**: Merges system messages for SillyTavern compatibility
- **`use_default_ids_if_mapping_not_found`**: When `true`, uses default session IDs if a model isn't in `model_endpoint_map.json`

### Step 2: Set Up `models.json`

This file maps friendly model names to LMArena's internal model IDs. The project comes with a pre-configured `models.json`, but you'll want to keep it updated.

**Format:**
```json
{
  "model-name": "model-id",
  "image-model-name": "model-id:image"
}
```

**Example:**
```json
{
  "gpt-4.1-2025-04-14": "14e9311c-94d2-40c2-8c54-273947e208b0",
  "claude-opus-4-20250514": "ee116d12-64d6-48a8-88e5-b2d06325cdd2",
  "gemini-2.5-pro": "e2d9d353-6dbe-4414-bf87-bd289d523726",
  "dall-e-3:image": "bb97bc68-131c-4ea4-a59e-03a6252de0d2:image"
}
```

**Notes:**
- Image generation models must have `:image` suffix
- Model names are case-sensitive
- You'll update this after running `model_updater.py` (see [Model List Updates](#model-list-updates))

### Step 3: Configure `model_endpoint_map.json` (Optional, Advanced)

This file allows you to assign specific session IDs to individual models, enabling:
- **Session isolation** between different models
- **Load balancing** through session ID pools
- **Mode binding** (direct_chat vs battle mode)

**Example Configuration:**
```json
{
  "claude-opus-4-20250514": [
    {
      "session_id": "session-abc-123",
      "message_id": "message-xyz-456",
      "mode": "direct_chat"
    },
    {
      "session_id": "session-def-789",
      "message_id": "message-uvw-012",
      "mode": "battle",
      "battle_target": "A"
    }
  ],
  "gemini-2.5-pro": {
    "session_id": "session-single-id",
    "message_id": "message-single-id"
  }
}
```

**When to use this:**
- You want different models to use separate browser sessions
- You need to bypass rate limits by rotating through multiple sessions
- You want specific models locked to battle or direct_chat mode

**When to skip this:**
- You're just getting started (use the default global session IDs first)
- You only use a few models occasionally

---

## Starting the Server

### Basic Server Start

With your virtual environment activated, run:

```bash
python api_server.py
```

You should see output like:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:5102 (Press CTRL+C to quit)
```

### Server Configuration

The server runs on:
- **HTTP API**: `http://127.0.0.1:5102`
- **WebSocket**: `ws://127.0.0.1:5102/ws`
- **Internal API**: `http://127.0.0.1:5103` (used by helper scripts)

### Running in the Background

**On Windows (PowerShell):**
```powershell
Start-Process python -ArgumentList "api_server.py" -WindowStyle Hidden
```

**On macOS/Linux:**
```bash
nohup python api_server.py > api_server.log 2>&1 &
```

To stop the background process, find its PID:
```bash
# Linux/Mac
ps aux | grep api_server.py
kill <PID>

# Windows
tasklist | findstr python
taskkill /PID <PID> /F
```

---

## Browser Setup

The Tampermonkey userscript acts as the bridge between your local API server and LMArena.ai.

### Step 1: Install Tampermonkey

If you haven't already, install the Tampermonkey extension for your browser:
- [Chrome/Edge](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)

### Step 2: Install the Userscript

1. **Open Tampermonkey Dashboard**
   - Click the Tampermonkey icon in your browser toolbar
   - Select "Dashboard"

2. **Create a New Script**
   - Click the "+" icon or "Create a new script" button

3. **Paste the Script**
   - Open `TampermonkeyScript/LMArenaApiBridge.js` from the project folder
   - Copy all contents
   - Paste into the Tampermonkey editor (replacing any default content)

4. **Save the Script**
   - Press `Ctrl+S` (Windows/Linux) or `Cmd+S` (Mac)
   - Or click File → Save

### Step 3: Verify Connection

1. **Make sure `api_server.py` is running**

2. **Open LMArena.ai**
   - Navigate to https://lmarena.ai/ or any subpage
   - You can use the leaderboard page, arena page, or direct chat page

3. **Check Connection Status**
   - Look at the browser tab title
   - If successfully connected, you'll see a **✅** prefix
   - Example: `✅ LM Arena - Side by Side`

4. **Check Browser Console** (optional)
   - Press `F12` to open Developer Tools
   - Go to the Console tab
   - You should see: `[API Bridge] ✅ 与本地服务器的 WebSocket 连接已建立。`

### Troubleshooting Connection Issues

If the ✅ doesn't appear:

1. **Verify the server is running** on port 5102
2. **Check the script is enabled** in Tampermonkey dashboard
3. **Refresh the LMArena page** (`F5` or `Ctrl+R`)
4. **Check for console errors** in browser Developer Tools (F12)
5. **Verify WebSocket port** in the script matches `api_server.py` (default: 5102)

---

## Session ID Capture

Session IDs are required for the API to communicate with LMArena. You need to capture at least one session ID before you can make API requests.

### Why Session IDs Matter

- LMArena uses session IDs to track conversations
- Each request needs a valid `session_id` and `message_id`
- Session IDs are tied to specific browser sessions and can expire
- You can capture multiple session IDs for different models

### Automated Method: Using `id_updater.py`

This is the recommended method for capturing session IDs.

#### Prerequisites
- `api_server.py` is running
- Browser with Tampermonkey script is connected (✅ in title)
- You have access to LMArena.ai

#### Steps

1. **Open a new terminal** (keep `api_server.py` running in the original terminal)

2. **Activate virtual environment** (if not already active)
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Run the ID updater**
   ```bash
   python id_updater.py
   ```

4. **Select Mode**
   - Choose between:
     - `1` - Direct Chat mode (recommended for beginners)
     - `2` - Battle mode

5. **Watch for Visual Indicator**
   - Your LMArena browser tab title will now show **🎯** prefix
   - Example: `🎯 ✅ LM Arena - Side by Side`
   - This means ID capture mode is active

6. **Trigger a Retry in Browser**
   - Navigate to an LMArena chat page (Direct Chat or Battle)
   - Make sure there's at least one AI response visible
   - **Important for Battle mode**: Do NOT reveal the model names - keep them anonymous
   - Ensure the last message in the conversation is from the AI model
   - **Click the "Retry" button** (↻) in the top-right corner of the AI's response card

7. **Capture Complete**
   - The terminal running `id_updater.py` will display the captured IDs
   - The script will automatically update `config.jsonc`
   - The 🎯 indicator will disappear from your browser
   - Example output:
     ```
     ✅ 成功捕获到会话ID！
     Session ID: 2c18cce8-77ee-4344-99f0-d0b944cd5571
     Message ID: 51985cc6-af61-4c8a-b6c5-c240f7456cab
     已更新 config.jsonc
     ```

### Manual Method: Using `model_endpoint_map.json`

If you want to set up multiple session IDs for different models:

1. **Capture session IDs** using `id_updater.py` as described above (do this once per model)
2. **Copy the IDs** from the terminal output
3. **Edit `model_endpoint_map.json`** and add entries:
   ```json
   {
     "your-model-name": {
       "session_id": "captured-session-id",
       "message_id": "captured-message-id",
       "mode": "direct_chat"
     }
   }
   ```

### Session ID Best Practices

- **Capture fresh IDs** if you encounter authentication errors
- **Use direct_chat mode** for most models (simpler and more reliable)
- **Battle mode** should only be used if you specifically need it
- **Keep sessions active** by making requests regularly (sessions can expire)
- **Multiple IDs** can be useful for load balancing across popular models

---

## Model List Updates

LMArena frequently adds new models. You'll want to keep your `models.json` updated to access them.

### Method 1: Automated Update (Recommended)

This method automatically fetches the current model list from LMArena.

#### Prerequisites
- `api_server.py` is running
- Browser with Tampermonkey script is connected (✅ in title)

#### Steps

1. **Open a new terminal** (keep `api_server.py` running)

2. **Activate virtual environment**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Run the model updater**
   ```bash
   python model_updater.py
   ```

4. **Wait for completion**
   - The script will request the browser to scrape the model list
   - Output example:
     ```
     [INFO] 正在请求浏览器获取最新的模型列表...
     [INFO] 成功接收到模型列表！共 123 个模型。
     [INFO] 已将可用模型列表保存到: available_models.json
     ```

5. **Check `available_models.json`**
   - This file now contains all available models with full metadata
   - Example entry:
     ```json
     {
       "id": "14e9311c-94d2-40c2-8c54-273947e208b0",
       "publicName": "gpt-4.1-2025-04-14",
       "organization": "OpenAI",
       "capabilities": {
         "inputCapabilities": {
           "image": false,
           "audio": false
         }
       }
     }
     ```

6. **Generate `models.json` automatically**
   ```bash
   python use-model.py
   ```
   
   - This script reads `available_models.json` and generates a complete `models.json`
   - Automatically adds `:image` suffix to image generation models
   - Output example:
     ```
     ✅ 已生成 models.json，共 123 个模型。
     ```

7. **Restart the API server** to load the new models
   - Stop the server: `Ctrl+C`
   - Start again: `python api_server.py`

### Method 2: Manual Update

If you only want to add specific models:

1. **Run the model updater** to generate `available_models.json` (as above)

2. **Open `available_models.json`** and find the models you want

3. **Copy model entries** to `models.json`:
   ```json
   {
     "model-public-name": "model-id"
   }
   ```
   
   For image models, add `:image`:
   ```json
   {
     "dall-e-3": "model-id:image"
   }
   ```

4. **Save and restart** the API server

### Verifying Model Updates

After updating, verify the models are loaded:

```bash
curl http://127.0.0.1:5102/v1/models
```

You should see a JSON response with all your models listed.

---

## Testing the API

Now that everything is set up, let's test the API to make sure it works!

### Prerequisites Checklist
- ✅ `api_server.py` is running
- ✅ Browser has Tampermonkey script installed and connected (✅ in title)
- ✅ Session IDs captured in `config.jsonc`
- ✅ `models.json` is configured

### Test 1: List Available Models

This verifies the API server is running and can read your `models.json`.

```bash
curl http://127.0.0.1:5102/v1/models
```

**Expected Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4.1-2025-04-14",
      "object": "model",
      "created": 1234567890,
      "owned_by": "lmarena"
    },
    {
      "id": "claude-opus-4-20250514",
      "object": "model",
      "created": 1234567890,
      "owned_by": "lmarena"
    }
  ]
}
```

### Test 2: Simple Chat Completion (Non-Streaming)

Test a basic chat request:

```bash
curl http://127.0.0.1:5102/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1-2025-04-14",
    "messages": [
      {
        "role": "user",
        "content": "Say hello in one sentence."
      }
    ],
    "stream": false
  }'
```

**Expected Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4.1-2025-04-14",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

### Test 3: Streaming Chat Completion

Test real-time streaming responses:

```bash
curl http://127.0.0.1:5102/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-pro",
    "messages": [
      {
        "role": "user",
        "content": "Count from 1 to 5."
      }
    ],
    "stream": true
  }'
```

**Expected Response** (streamed chunks):
```
data: {"id":"chatcmpl-xyz","object":"chat.completion.chunk","created":1234567890,"model":"gemini-2.5-pro","choices":[{"index":0,"delta":{"role":"assistant","content":"1"},"finish_reason":null}]}

data: {"id":"chatcmpl-xyz","object":"chat.completion.chunk","created":1234567890,"model":"gemini-2.5-pro","choices":[{"index":0,"delta":{"content":", 2"},"finish_reason":null}]}

data: {"id":"chatcmpl-xyz","object":"chat.completion.chunk","created":1234567890,"model":"gemini-2.5-pro","choices":[{"index":0,"delta":{"content":", 3, 4, 5"},"finish_reason":"stop"}]}

data: [DONE]
```

### Test 4: Image Generation

Test image generation (make sure you have an image model in `models.json`):

```bash
curl http://127.0.0.1:5102/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "dall-e-3",
    "messages": [
      {
        "role": "user",
        "content": "A serene mountain landscape at sunset"
      }
    ],
    "n": 1
  }'
```

**Expected Response:**
```json
{
  "id": "img-as-chat-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "dall-e-3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "![A serene mountain landscape at sunset](https://lmarena.ai/...image-url...)"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

### Test 5: With API Key Authentication

If you set an `api_key` in `config.jsonc`, include it in your requests:

```bash
curl http://127.0.0.1:5102/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key-here" \
  -d '{
    "model": "claude-opus-4-20250514",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

### Windows-Specific curl Notes

If you're on Windows Command Prompt, use `^` for line continuation and escape quotes:

```cmd
curl http://127.0.0.1:5102/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"gpt-4.1-2025-04-14\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}"
```

Or use PowerShell:

```powershell
$body = @{
    model = "gpt-4.1-2025-04-14"
    messages = @(
        @{
            role = "user"
            content = "Hello!"
        }
    )
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5102/v1/chat/completions" -Method Post -Body $body -ContentType "application/json"
```

---

## Integration Examples

### Using with OpenAI Python Library

The API is fully compatible with OpenAI's official Python library.

#### Installation

```bash
pip install openai
```

#### Basic Usage

```python
from openai import OpenAI

# Initialize client pointing to your local server
client = OpenAI(
    base_url="http://127.0.0.1:5102/v1",
    api_key="your-api-key-or-anything"  # Use your api_key from config.jsonc, or any string if not set
)

# List available models
models = client.models.list()
print("Available models:")
for model in models.data:
    print(f"  - {model.id}")

# Simple chat completion
response = client.chat.completions.create(
    model="gpt-4.1-2025-04-14",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)
print(response.choices[0].message.content)

# Streaming chat completion
stream = client.chat.completions.create(
    model="claude-opus-4-20250514",
    messages=[
        {"role": "user", "content": "Tell me a short joke"}
    ],
    stream=True
)

print("Streaming response:")
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

#### With Conversation History

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:5102/v1",
    api_key="anything"
)

# Maintain conversation context
messages = [
    {"role": "user", "content": "My name is Alice."},
]

response = client.chat.completions.create(
    model="gemini-2.5-pro",
    messages=messages
)
messages.append({"role": "assistant", "content": response.choices[0].message.content})

# Continue conversation
messages.append({"role": "user", "content": "What's my name?"})
response = client.chat.completions.create(
    model="gemini-2.5-pro",
    messages=messages
)
print(response.choices[0].message.content)  # Should respond with "Alice"
```

### Using with SillyTavern

SillyTavern is a popular UI for chatting with AI models.

#### Configuration Steps

1. **Enable Tavern Mode** in `config.jsonc`:
   ```jsonc
   {
     "tavern_mode_enabled": true
   }
   ```

2. **Restart the API server**

3. **Open SillyTavern** and go to API Settings

4. **Configure API Connection:**
   - API Type: `OpenAI`
   - API URL: `http://127.0.0.1:5102/v1`
   - API Key: Your `api_key` from `config.jsonc` (or leave empty if not set)
   - Model: Choose from your `models.json` (e.g., `claude-opus-4-20250514`)

5. **Test Connection** using SillyTavern's "Test API" button

6. **Start Chatting!**

#### Why Tavern Mode?

Tavern mode intelligently merges system prompts with user messages, ensuring compatibility with SillyTavern's message format. Without it, system prompts might not be properly sent to LMArena.

### Using with Other OpenAI-Compatible Clients

Any application that supports OpenAI's API can use LMArena-to-API:

- **LangChain**
  ```python
  from langchain.chat_models import ChatOpenAI
  
  llm = ChatOpenAI(
      openai_api_base="http://127.0.0.1:5102/v1",
      openai_api_key="anything",
      model_name="gpt-4.1-2025-04-14"
  )
  ```

- **LlamaIndex**
  ```python
  from llama_index.llms import OpenAI
  
  llm = OpenAI(
      api_base="http://127.0.0.1:5102/v1",
      api_key="anything",
      model="claude-opus-4-20250514"
  )
  ```

- **BetterChatGPT, ChatGPT-Next-Web**, and similar web UIs:
  - Set API endpoint to `http://127.0.0.1:5102`
  - Set API key to your configured key (or any value if authentication is disabled)

---

## Troubleshooting

### Connection Issues

#### Problem: Browser shows no ✅ in title

**Symptoms:**
- LMArena page doesn't show ✅ prefix
- Console shows WebSocket connection errors

**Solutions:**
1. **Verify server is running:**
   ```bash
   curl http://127.0.0.1:5102/v1/models
   ```
   If this fails, start `api_server.py`

2. **Check Tampermonkey script is enabled:**
   - Click Tampermonkey icon
   - Ensure "LMArena API Bridge" is toggled ON

3. **Verify script URL matches server:**
   - Open the script in Tampermonkey
   - Check line: `const SERVER_URL = "ws://localhost:5102/ws";`
   - Ensure port matches your `api_server.py` port

4. **Check for port conflicts:**
   ```bash
   # Linux/Mac
   lsof -i :5102
   
   # Windows
   netstat -ano | findstr :5102
   ```

5. **Refresh the browser page** (`Ctrl+R` or `F5`)

6. **Check browser console for errors** (F12 → Console tab)

#### Problem: WebSocket connection refused

**Symptoms:**
- Console error: `WebSocket connection to 'ws://localhost:5102/ws' failed`

**Solutions:**
1. **Ensure `api_server.py` is running**
2. **Check firewall/antivirus** isn't blocking local connections
3. **Try using `127.0.0.1` instead of `localhost`** in the script
4. **Verify no other application is using port 5102**

### API Request Issues

#### Problem: `401 Unauthorized` error

**Symptoms:**
```json
{"detail": "Invalid API Key"}
```

**Solutions:**
1. **Check your `config.jsonc`:**
   - If `api_key` is set, ensure you're sending it in requests
   - Header format: `Authorization: Bearer your-api-key`

2. **If you don't want authentication:**
   - Set `"api_key": ""` in `config.jsonc`
   - Restart the server

#### Problem: `404 Model not found`

**Symptoms:**
```json
{"detail": "Model 'xyz' not found in models.json"}
```

**Solutions:**
1. **Check model name spelling** - it's case-sensitive
2. **Verify model exists in `models.json`**
3. **Restart the server** after updating `models.json`
4. **List available models:**
   ```bash
   curl http://127.0.0.1:5102/v1/models
   ```

#### Problem: `500 Internal Server Error` or timeout

**Symptoms:**
- Request hangs or times out
- Server logs show errors

**Solutions:**
1. **Check server logs** for specific errors
2. **Verify session IDs are valid:**
   - Re-run `id_updater.py` to capture fresh session IDs
   - Old sessions may have expired

3. **Increase timeout in `config.jsonc`:**
   ```jsonc
   {
     "stream_response_timeout_seconds": 600
   }
   ```

4. **Ensure LMArena page is open** and connected (✅ in title)

5. **Check browser console** for errors

### Session ID Issues

#### Problem: Session IDs not capturing

**Symptoms:**
- `id_updater.py` doesn't receive session IDs
- Script hangs waiting for capture

**Solutions:**
1. **Ensure `api_server.py` is running first**
2. **Verify browser shows 🎯 indicator** after running `id_updater.py`
3. **Make sure you click "Retry" on an AI message**, not a user message
4. **Ensure the message is from the model itself**, not an error message
5. **Check browser console** for capture-related errors

#### Problem: Captured session IDs don't work

**Symptoms:**
- API requests fail with authentication errors
- LMArena returns "session not found" errors

**Solutions:**
1. **Verify you're using the same browser** where you captured IDs
2. **Check if LMArena session expired:**
   - Sessions can expire after inactivity
   - Capture fresh session IDs

3. **Ensure you captured in the correct mode:**
   - Direct Chat IDs only work in direct chat
   - Battle IDs only work in battle mode

### Model List Issues

#### Problem: `model_updater.py` fails or times out

**Symptoms:**
- Script hangs
- No `available_models.json` generated
- Timeout errors

**Solutions:**
1. **Verify prerequisites:**
   - `api_server.py` is running
   - Browser is connected (✅ in title)

2. **Check LMArena page is accessible:**
   - Navigate to https://lmarena.ai/ manually
   - Ensure no Cloudflare challenges are blocking

3. **Check server logs** for WebSocket communication errors

4. **Increase timeout if on slow connection**

#### Problem: `use-model.py` fails

**Symptoms:**
```
FileNotFoundError: available_models.json not found
```

**Solutions:**
1. **Run `model_updater.py` first** to generate `available_models.json`
2. **Ensure you're in the project root directory** when running the script

### Performance Issues

#### Problem: Slow response times

**Solutions:**
1. **Check your internet connection** to LMArena.ai
2. **Verify LMArena itself isn't experiencing issues** by testing directly on their website
3. **Try a different model** - some models are naturally slower
4. **Check if browser has resource issues** (too many tabs, low memory)

#### Problem: Requests fail intermittently

**Solutions:**
1. **Use `model_endpoint_map.json` to set up multiple session IDs** for load balancing
2. **Capture fresh session IDs regularly** to avoid expiration
3. **Check for LMArena rate limiting** - add delays between requests if needed

---

## Advanced Features

### Docker + noVNC Browser Automation

For advanced users, LMArena-to-API supports running a headless Chrome instance in Docker with remote access via noVNC.

#### Use Cases
- Running on a server without a desktop environment
- Automated session ID capture
- Bypassing Cloudflare challenges via remote browser access

#### Prerequisites
- Docker Desktop installed and running
- `api_server.py` running locally

#### Quick Start (Windows)

```bash
.\run_docker_browser.bat --url https://lmarena.ai/
```

#### Quick Start (Cross-platform)

```bash
python scripts/docker_browser_runner.py --url https://lmarena.ai/
```

#### With Self-Test

Verify the container browser can communicate with your local API server:

```bash
python scripts/docker_browser_runner.py --url https://lmarena.ai/ --self-test
```

#### Accessing noVNC

If you encounter a Cloudflare challenge, the script will prompt you to access the browser GUI:

```
🌐 Please open noVNC in your browser:
   http://localhost:7900/?autoconnect=1&resize=scale&password=secret
```

Open this URL in your browser to interact with the remote Chrome instance.

#### Docker Compose Method

For persistent container setup:

1. **Start the container:**
   ```bash
   docker compose up -d browser
   ```

2. **Run the connector script:**
   ```bash
   python scripts/docker_browser_runner.py --url https://lmarena.ai/ --keep-container
   ```

3. **Stop when done:**
   ```bash
   docker compose down
   ```

#### Options

- `--url <URL>` - Starting URL (default: https://lmarena.ai/)
- `--image <IMAGE>` - Docker image (default: selenium/standalone-chrome:latest)
- `--name <NAME>` - Container name (default: lm_cf_browser)
- `--keep-container` - Don't remove container on exit
- `--self-test` - Run connectivity test after startup
- `--test-timeout <SECONDS>` - Self-test timeout (default: 45)

### Helper Scripts

#### `use-model.py` - Auto-generate models.json

Quickly generate `models.json` from `available_models.json`:

```bash
python use-model.py
```

- Reads `available_models.json`
- Automatically detects image generation models
- Adds `:image` suffix where appropriate
- Overwrites existing `models.json`

**Backup before using:**
```bash
cp models.json models.json.backup
```

#### Monitoring and Logging

**View server logs in real-time:**

```bash
# Linux/Mac
tail -f api_server.log

# Windows PowerShell
Get-Content api_server.log -Wait -Tail 50
```

**Enable debug logging** (modify `api_server.py`):
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Multiple Session Management

For heavy usage, set up multiple session IDs per model:

1. **Capture multiple session IDs** for the same model using `id_updater.py`
2. **Edit `model_endpoint_map.json`:**
   ```json
   {
     "popular-model": [
       {
         "session_id": "session-1",
         "message_id": "message-1",
         "mode": "direct_chat"
       },
       {
         "session_id": "session-2",
         "message_id": "message-2",
         "mode": "direct_chat"
       },
       {
         "session_id": "session-3",
         "message_id": "message-3",
         "mode": "direct_chat"
       }
     ]
   }
   ```

The server will randomly select from the pool for each request, distributing load.

### Auto-Update Feature

The server can automatically check for updates from GitHub:

**In `config.jsonc`:**
```jsonc
{
  "enable_auto_update": true
}
```

On startup, the server will:
1. Check the GitHub repository for new versions
2. Download and apply updates if available
3. Restart automatically with the new version

**To disable:**
```jsonc
{
  "enable_auto_update": false
}
```

### Idle Restart

Configure the server to restart after a period of inactivity:

```jsonc
{
  "enable_idle_restart": true,
  "idle_restart_timeout_seconds": 300  // 5 minutes
}
```

Set to `-1` to disable idle restart.

### Content Filter Bypass

Attempt to bypass LMArena's content filtering:

```jsonc
{
  "bypass_enabled": true
}
```

When enabled, the server injects an empty user message to try bypassing sensitive content filters. This doesn't guarantee success but may help in some cases.

### Using SOCKS5 Proxy (Experimental)

Route requests through a SOCKS5 proxy:

```jsonc
{
  "socks5_enabled": true,
  "socks5_candidates": [
    "127.0.0.1:1080",
    "user:pass@127.0.0.1:1080"
  ]
}
```

The server will test each candidate and use the first working one.

---

## Next Steps

Congratulations on setting up LMArena-to-API! Here are some suggestions for what to do next:

1. **Explore Different Models**
   - Run `model_updater.py` to see all available models
   - Try different models to find your favorites

2. **Integrate with Your Projects**
   - Use the OpenAI Python library to build AI-powered applications
   - Connect SillyTavern for a better chat experience

3. **Optimize Performance**
   - Set up multiple session IDs for frequently used models
   - Configure model-specific mappings in `model_endpoint_map.json`

4. **Automate Setup**
   - Create scripts to automatically update models
   - Schedule periodic session ID refreshes

5. **Join the Community**
   - Report issues on GitHub
   - Share your use cases and configurations
   - Contribute improvements to the project

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check the browser console** (F12) for error messages
2. **Review server logs** for detailed error information
3. **Search existing GitHub issues** for similar problems
4. **Open a new issue** with:
   - Your operating system and Python version
   - Steps to reproduce the problem
   - Relevant log excerpts
   - Configuration file contents (remove sensitive data)

---

## Additional Resources

- **Project Repository:** https://github.com/lianues/LMArena-to-api
- **LMArena Website:** https://lmarena.ai/
- **OpenAI API Documentation:** https://platform.openai.com/docs/api-reference
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

**Happy chatting with LMArena models! 🚀**
