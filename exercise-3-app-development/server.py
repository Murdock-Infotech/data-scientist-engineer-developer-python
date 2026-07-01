"""FastAPI server for Exercise 3."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from chat_agent import RAGChatAgent


app = FastAPI(title="RAG Chat Agent - Exercise 3")
chat_agent: RAGChatAgent | None = None
agent_ready = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatRequest(BaseModel):
    message: str
    conversationId: str | None = None


async def initialize_agent() -> None:
    global chat_agent, agent_ready

    try:
        print("Initializing RAG Chat Agent...")
        chat_agent = RAGChatAgent()
        agent_ready = True
        print("Chat Agent ready for requests")
    except Exception as error:
        agent_ready = False
        print(f"Failed to initialize chat agent: {error}")
        print("\nMake sure to:")
        print("1. Complete Exercise 2 first")
        print("2. Configure AWS credentials")
        print("3. Check vector-db-config.json\n")


@app.on_event("startup")
async def on_startup() -> None:
    await initialize_agent()


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "agentReady": agent_ready,
        "timestamp": utc_now(),
    }


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    # TODO: Implement chat API endpoint
    # Hints:
    # 1. Validate request body (message required)
    # 2. Extract conversationId from request if provided
    # 3. Call chat_agent.chat() with the message
    # 4. Return structured response with metadata
    if not agent_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Chat agent not ready",
                "message": "Please wait for agent initialization to complete",
            },
        )

    message = request.message.strip()
    if not message:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request",
                "message": "Message is required and must be a non-empty string",
            },
        )

    preview = f"{message[:50]}..." if len(message) > 50 else message
    print(f"Chat request: \"{preview}\"")

    # TODO: Call chat agent
    # result = chat_agent.chat(message, request.conversationId)

    # For now, return mock response (replace with actual agent call)
    result = {
        "response": (
            f"I received your message: \"{message}\". The chat agent is not fully "
            "implemented yet. Complete the TODO items in chat_agent.py first."
        ),
        "conversationId": request.conversationId or "mock-conversation-id",
        "metadata": {
            "searchResults": 0,
            "tokensUsed": 0,
            "responseTime": 100,
        },
        "sources": [],
    }

    return {
        "success": True,
        "data": result,
        "timestamp": utc_now(),
    }


@app.get("/conversations/{conversation_id}")
async def conversation_history(conversation_id: str) -> dict[str, Any]:
    # TODO: Implement conversation history endpoint
    if not agent_ready:
        raise HTTPException(status_code=503, detail={"error": "Chat agent not ready"})

    # TODO: Get history from agent
    # history = chat_agent.get_conversation_history(conversation_id)
    history: list[dict[str, Any]] = []

    return {
        "success": True,
        "conversationId": conversation_id,
        "history": history,
        "timestamp": utc_now(),
    }


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """
<!DOCTYPE html>
<html>
<head>
    <title>RAG Chat Agent - Exercise 3</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background-color: #e3f2fd; text-align: right; }
        .agent-message { background-color: #f5f5f5; }
        .input-container { display: flex; gap: 10px; }
        .message-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .send-button { padding: 10px 20px; background-color: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .status { padding: 10px; background-color: #fff3cd; border-radius: 5px; margin-bottom: 10px; }
        .sources { font-size: 0.8em; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>RAG Chat Agent - Exercise 3</h1>

    <div class="status" id="status">
        Agent Status: <span id="agent-status">Checking...</span>
    </div>

    <div class="chat-container" id="chatContainer">
        <div class="message agent-message">
            <strong>Assistant:</strong> Hello! I'm your AI assistant. I can help answer questions about technology and machine learning based on the content that was processed in the previous exercises. What would you like to know?
        </div>
    </div>

    <div class="input-container">
        <input type="text" id="messageInput" class="message-input" placeholder="Ask me about technology, AI, or machine learning..." onkeypress="handleKeyPress(event)">
        <button onclick="sendMessage()" class="send-button">Send</button>
    </div>

    <script>
        let conversationId = null;

        fetch('/health')
            .then(response => response.json())
            .then(data => {
                const statusElement = document.getElementById('agent-status');
                if (data.agentReady) {
                    statusElement.textContent = 'Ready';
                    statusElement.style.color = 'green';
                } else {
                    statusElement.textContent = 'Not Ready (Complete TODOs first)';
                    statusElement.style.color = 'red';
                }
            })
            .catch(error => {
                document.getElementById('agent-status').textContent = 'Error';
            });

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();

            if (!message) return;

            addMessageToChat('You', message, 'user-message');
            input.value = '';

            const typingId = addMessageToChat('Assistant', 'Thinking...', 'agent-message');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        conversationId: conversationId
                    })
                });

                const data = await response.json();
                document.getElementById(typingId).remove();

                if (data.success) {
                    conversationId = data.data.conversationId;

                    let responseText = data.data.response;
                    if (data.data.sources && data.data.sources.length > 0) {
                        const sourcesList = data.data.sources.map(s => s.title).join(', ');
                        responseText += `<div class="sources"><strong>Sources:</strong> ${sourcesList}</div>`;
                    }

                    addMessageToChat('Assistant', responseText, 'agent-message');
                } else {
                    addMessageToChat('Assistant', 'Sorry, I encountered an error: ' + data.message, 'agent-message');
                }
            } catch (error) {
                document.getElementById(typingId).remove();
                addMessageToChat('Assistant', "Sorry, I'm having trouble connecting to the server. Please make sure the agent is properly configured.", 'agent-message');
            }
        }

        function addMessageToChat(sender, message, className) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            const messageId = 'msg-' + Date.now();

            messageDiv.id = messageId;
            messageDiv.className = 'message ' + className;
            messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;

            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            return messageId;
        }
    </script>
</body>
</html>
    """


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Any, error: Exception) -> JSONResponse:
    print(f"Unhandled error: {error}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
        },
    )


def main() -> None:
    print("=" * 50)
    print("   EXERCISE 3: RAG CHAT AGENT SERVER")
    print("=" * 50)
    print("Role: Application Developer")
    print("Task: Deploy chat agent API\n")

    port = int(os.getenv("PORT") or os.getenv("APP_PORT") or "3000")
    print(f"Chat Agent Server starting on port {port}")
    print(f"Web interface: http://localhost:{port}")
    print(f"API endpoint: http://localhost:{port}/chat")
    print(f"Health check: http://localhost:{port}/health")
    print("\nQuick test:")
    print(f"curl -X POST http://localhost:{port}/chat \\")
    print('  -H "Content-Type: application/json" \\')
    print("  -d '{\"message\":\"What is machine learning?\"}'")
    print("\nTip: Complete the TODOs in chat_agent.py to enable full functionality")

    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
