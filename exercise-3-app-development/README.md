# Exercise 3: Application Development - RAG Chat Agent

**Role:** Application Developer  
**Time:** 22.5 minutes  
**Goal:** Build a chat agent that leverages the vector database using LangGraph and AWS Bedrock

## Learning Objectives

- Create LangGraph agents with memory and tools
- Implement semantic search with vector databases
- Build conversational AI with context awareness
- Deploy a working chat interface

## Your Mission

Create a chat agent that can answer questions about the tech content by searching the vector database and providing contextual responses using AWS Bedrock Claude.

## TODO List (Complete in Order)

### Step 1: Agent Architecture Setup (7.5 min)

- [ ] Review the LangGraph agent structure
- [ ] Complete the semantic search tool
- [ ] Add conversation memory management
- [ ] Test basic agent responses

### Step 2: RAG Implementation (10 min)

- [ ] Complete the `search_vector_database` function
- [ ] Implement context retrieval and ranking
- [ ] Complete the `generate_response` node
- [ ] Add source attribution to responses

### Step 3: Chat Interface (5 min)

- [ ] Complete the FastAPI endpoints
- [ ] Add conversation history tracking
- [ ] Test the chat functionality
- [ ] Add error handling for edge cases

## Quick Start

```bash
cd exercise-3-app-development
python server.py

# In another terminal:
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is machine learning?"}'
```

## Expected Output

```text
=== CHAT AGENT READY ===
Vector Database: Connected (12 vectors)
Bedrock Model: Claude-3 Haiku
Server: Running on port 3000
Test: curl -X POST http://localhost:3000/chat
```

## Key Concepts

- **RAG Pattern**: Retrieve relevant context before generating responses
- **Semantic Search**: Find similar content using vector similarity
- **Agent Memory**: Maintain conversation context across turns
- **Source Attribution**: Reference original content in responses

## Success Criteria

- [ ] Agent successfully searches vector database
- [ ] Responses include relevant context from stored content
- [ ] Conversation memory works across multiple turns
- [ ] API endpoints respond correctly
- [ ] Sources are cited in responses

## Stuck? Quick Tips

- Make sure Exercise 2 completed successfully by checking `vector-db-config.json`
- Test individual components before the full agent
- Use `print()` to debug the retrieval process
- ChromaDB or the local file fallback must be available for vector search

---

**Congratulations!** You have built a complete AI pipeline from data analysis to chat agent.
