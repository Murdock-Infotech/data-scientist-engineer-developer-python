"""Exercise 3: Application Development - RAG Chat Agent."""

from __future__ import annotations

import json
import math
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
import chromadb
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
EXERCISE_2_DIR = PROJECT_DIR / "exercise-2-data-engineering"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentState:
    messages: list[dict[str, str]] = field(default_factory=list)
    current_query: str = ""
    processed_query: str = ""
    retrieved_context: list[dict[str, Any]] = field(default_factory=list)
    response: str = ""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(
        default_factory=lambda: {"searchResults": 0, "tokensUsed": 0, "responseTime": 0}
    )


class RAGChatAgent:
    def __init__(self) -> None:
        self.collection_name = "tech-content-vectors"
        self.collection = None
        self.chroma_client = None
        self.use_chroma_client = False
        self.graph = None
        self.conversation_history: dict[str, list[dict[str, Any]]] = {}
        self.initialized = False
        self.local_vector_index: dict[str, Any] | None = None
        self.embedding_cache: dict[str, list[float]] = {}
        self.bedrock_client = boto3.client(
            "bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.initialize_agent()

    def initialize_agent(self) -> None:
        if self.initialized:
            return

        try:
            self.chroma_client = chromadb.PersistentClient(path=str(EXERCISE_2_DIR / "chroma_db"))
            self.chroma_client.list_collections()
            self.use_chroma_client = True
            print("Connected to ChromaDB using persistent client")
        except Exception:
            self.use_chroma_client = False
            print("Could not connect to ChromaDB, will use local file storage fallback.")

        self.verify_vector_database()

        workflow = StateGraph(dict)
        workflow.add_node("process_query", self.process_query)
        workflow.add_node("search_vector_database", self.search_vector_database)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("update_memory", self.update_memory)

        workflow.add_edge(START, "process_query")
        workflow.add_edge("process_query", "search_vector_database")
        workflow.add_edge("search_vector_database", "generate_response")
        workflow.add_edge("generate_response", "update_memory")
        workflow.add_edge("update_memory", END)

        self.graph = workflow.compile()
        print("RAG Chat Agent initialized")
        self.initialized = True

    def verify_vector_database(self) -> None:
        try:
            if self.use_chroma_client and self.chroma_client:
                collections = self.chroma_client.list_collections()
                collection_names = [
                    collection.name if hasattr(collection, "name") else str(collection)
                    for collection in collections
                ]
                if self.collection_name not in collection_names:
                    raise ValueError(f"Collection '{self.collection_name}' not found in ChromaDB")
                print(f"Vector database ready (ChromaDB): {self.collection_name}")
            else:
                config_path = BASE_DIR / "vector-db-config.json"
                if not config_path.exists():
                    raise FileNotFoundError("vector-db-config.json not found")
                config = json.loads(config_path.read_text(encoding="utf-8"))
                if not config.get("ready"):
                    raise ValueError("Vector DB not marked as ready")
                print(f"Vector database ready (file): {config.get('vectorCount', 0)} vectors available")
        except Exception as error:
            print(f"Vector database verification failed: {error}")
            raise

    def process_query(self, state: dict[str, Any]) -> dict[str, Any]:
        print(f"Processing query: \"{state['current_query']}\"")

        # TODO: Add query preprocessing
        # Hints:
        # 1. Clean and normalize the query
        # 2. Extract key terms for better search
        # 3. Check conversation history for context
        # 4. Determine search strategy
        try:
            clean_query = state["current_query"].strip().lower()

            # TODO: Add more sophisticated query processing
            # - Extract entities (names, technologies, concepts)
            # - Expand abbreviations (ML -> Machine Learning)
            # - Add context from conversation history

            state["processed_query"] = clean_query
            print(f"Query processed: \"{state['processed_query']}\"")
        except Exception as error:
            print(f"Query processing failed: {error}")
            state["response"] = "I'm having trouble understanding your question. Could you rephrase it?"

        return state

    def search_vector_database(self, state: dict[str, Any]) -> dict[str, Any]:
        print("Searching vector database...")

        try:
            if self.use_chroma_client and self.chroma_client:
                collection = self.chroma_client.get_collection(name=self.collection_name)
                results = collection.query(
                    query_texts=[state["processed_query"]],
                    n_results=3,
                )
            else:
                ranked = self.semantic_local_search(state["processed_query"], 3)
                results = {
                    "documents": [[item["content"] for item in ranked]],
                    "metadatas": [[item["metadata"] for item in ranked]],
                    "distances": [[1 - item["similarity"] for item in ranked]],
                }

            documents = results.get("documents", [[]])[0]
            if documents:
                state["retrieved_context"] = [
                    {
                        "content": content,
                        "metadata": results.get("metadatas", [[]])[0][index],
                        "similarity": results.get("distances", [[]])[0][index],
                    }
                    for index, content in enumerate(documents)
                ]
                state["metadata"]["searchResults"] = len(state["retrieved_context"])
                print(f"Found {len(state['retrieved_context'])} relevant documents")
                for index, result in enumerate(state["retrieved_context"], start=1):
                    title = result["metadata"].get("title", "Untitled")
                    print(f"  {index}. {title} (similarity: {result['similarity']:.2f})")
            else:
                print("No relevant documents found")
                state["retrieved_context"] = []
                state["metadata"]["searchResults"] = 0
        except Exception as error:
            print(f"Vector search failed: {error}")
            state["retrieved_context"] = []
            state["metadata"]["searchResults"] = 0

        return state

    def ensure_local_vector_index(self) -> dict[str, Any]:
        if self.local_vector_index:
            return self.local_vector_index

        candidate_paths = [
            BASE_DIR / "chroma_db" / f"{self.collection_name}.json",
            EXERCISE_2_DIR / "chroma_db" / f"{self.collection_name}.json",
        ]

        found_path = next((path for path in candidate_paths if path.exists()), None)
        if not found_path:
            raise FileNotFoundError("Local vector file tech-content-vectors.json not found")

        raw = json.loads(found_path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            records = raw
        elif raw.get("embeddings"):
            records = [
                {
                    "id": item.get("id"),
                    "vector": item.get("vector") or item.get("embedding") or [],
                    "content": item.get("document") or item.get("content") or "",
                    "metadata": item.get("metadata") or {},
                }
                for item in raw["embeddings"]
            ]
        else:
            records = raw.get("vectors", [])

        if not records:
            raise ValueError("No vectors found in local vector file")

        dimension = len(records[0].get("vector", []))
        records = [
            record
            for record in records
            if isinstance(record.get("vector"), list) and len(record["vector"]) == dimension
        ]
        self.local_vector_index = {"vectors": records, "dim": dimension}
        print(f"Loaded {len(records)} local vectors (dim={dimension}) for semantic fallback")
        return self.local_vector_index

    def embed_query(self, text: str) -> list[float] | None:
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        if os.getenv("SKIP_EMBEDDING_FALLBACK") == "1":
            return None

        try:
            model_id = (
                os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID")
                or os.getenv("BEDROCK_EMBED_MODEL")
                or "amazon.titan-embed-text-v2:0"
            )
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({"inputText": text}),
            )
            payload = json.loads(response["body"].read().decode("utf-8"))
            embedding = payload.get("embedding") or payload.get("Embeddings") or payload.get("vector")
            if not isinstance(embedding, list):
                raise ValueError("No embedding array returned")
            self.embedding_cache[text] = embedding
            return embedding
        except Exception as error:
            print(f"Bedrock embedding failed, falling back to keyword similarity: {error}")
            return None

    @staticmethod
    def cosine_similarity(first: list[float], second: list[float]) -> float:
        if not first or not second or len(first) != len(second):
            return -1
        dot = sum(x * y for x, y in zip(first, second))
        first_norm = math.sqrt(sum(x * x for x in first))
        second_norm = math.sqrt(sum(y * y for y in second))
        return dot / ((first_norm * second_norm) + 1e-12)

    @staticmethod
    def keyword_score(query: str, text: str) -> float:
        query_terms = set(term for term in query.split() if term)
        lower_text = text.lower()
        hits = sum(1 for term in query_terms if term in lower_text)
        return hits / (len(query_terms) or 1)

    def semantic_local_search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        index = self.ensure_local_vector_index()
        query_embedding = self.embed_query(query)

        if query_embedding and len(query_embedding) == index["dim"]:
            scored = [
                {
                    **record,
                    "similarity": self.cosine_similarity(query_embedding, record["vector"]),
                }
                for record in index["vectors"]
            ]
        else:
            scored = [
                {
                    **record,
                    "similarity": self.keyword_score(query.lower(), record.get("content", "")),
                }
                for record in index["vectors"]
            ]

        scored.sort(key=lambda item: item["similarity"], reverse=True)
        return scored[:limit]

    def generate_response(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: Generate response using AWS Bedrock Claude with retrieved context
        # Hints:
        # 1. Build prompt with retrieved context
        # 2. Include conversation history if available
        # 3. Call Bedrock Claude model
        # 4. Add source attribution to response
        print("Generating response with Claude...")

        start_time = datetime.now()

        try:
            context_text = "\n\n".join(
                f"Source: {item['metadata'].get('title', 'Untitled')}\nContent: {item['content']}"
                for item in state["retrieved_context"]
            )
            prompt = self.build_rag_prompt(
                state["current_query"], context_text, state["conversation_id"]
            )
            _ = prompt

            # TODO: Call AWS Bedrock Claude
            response = self.mock_bedrock_claude(state)

            state["response"] = response
            state["metadata"]["responseTime"] = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )
            print(f"Response generated ({state['metadata']['responseTime']}ms)")
        except Exception as error:
            print(f"Response generation failed: {error}")
            state["response"] = (
                "I apologize, but I'm having trouble generating a response right now. "
                "Please try again."
            )

        return state

    def build_rag_prompt(self, query: str, context: str, conversation_id: str) -> str:
        # TODO: Create an effective RAG prompt template
        _ = conversation_id
        return f"""You are a helpful AI assistant specializing in technology and machine learning topics.

Use the following context from relevant documents to answer the user's question. If the context does not contain relevant information, say so clearly.

CONTEXT:
{context}

USER QUESTION: {query}

Please provide a helpful, accurate response based on the context above. Include references to specific sources when possible.

RESPONSE:"""

    def mock_bedrock_claude(self, state: dict[str, Any]) -> str:
        # TODO: Replace with actual Bedrock Claude call
        if state["retrieved_context"]:
            sources = ", ".join(
                item["metadata"].get("title", "Untitled") for item in state["retrieved_context"]
            )
            return f"""Based on the available documentation, here's what I can tell you about your question:

{self.generate_mock_answer(state["current_query"])}

This information is sourced from: {sources}

Would you like me to elaborate on any specific aspect?"""

        return (
            "I don't have specific information about that topic in my current knowledge base. "
            "Could you try rephrasing your question or asking about a different aspect?"
        )

    @staticmethod
    def generate_mock_answer(query: str) -> str:
        lower_query = query.lower()

        if "machine learning" in lower_query or "ml" in lower_query:
            return (
                "Machine learning is a powerful subset of AI that allows systems to learn "
                "from data without being explicitly programmed. It is widely used in applications "
                "ranging from recommendation systems to autonomous vehicles."
            )
        if "python" in lower_query:
            return (
                "Python is widely used across data science, data engineering, and application "
                "development because it has strong libraries for analysis, automation, APIs, and AI."
            )
        if "aws" in lower_query or "bedrock" in lower_query:
            return (
                "AWS Bedrock provides managed access to foundation models from companies like "
                "Anthropic and Amazon, making it easier to integrate AI capabilities without "
                "managing model infrastructure."
            )
        return (
            "This appears to be a technology-related question. The available documentation "
            "contains information about various tech topics, tools, and best practices."
        )

    def update_memory(self, state: dict[str, Any]) -> dict[str, Any]:
        print("Updating conversation memory...")

        # TODO: Implement conversation memory management
        # Hints:
        # 1. Store query and response in conversation history
        # 2. Implement memory limits (max turns, token limits)
        # 3. Track conversation context for future queries
        # 4. Update agent metadata
        try:
            conversation_turn = {
                "timestamp": utc_now(),
                "query": state["current_query"],
                "response": state["response"],
                "contextUsed": len(state["retrieved_context"]),
                "sources": [
                    item["metadata"].get("title", "Untitled")
                    for item in state["retrieved_context"]
                ],
            }

            history = self.conversation_history.setdefault(state["conversation_id"], [])
            history.append(conversation_turn)

            if len(history) > 10:
                del history[0]

            print(f"Memory updated ({len(history)} turns stored)")
        except Exception as error:
            print(f"Memory update failed: {error}")

        return state

    def chat(self, query: str, conversation_id: str | None = None) -> dict[str, Any]:
        state = {
            "messages": [],
            "current_query": query,
            "processed_query": "",
            "retrieved_context": [],
            "response": "",
            "conversation_id": conversation_id or str(uuid.uuid4()),
            "metadata": {"searchResults": 0, "tokensUsed": 0, "responseTime": 0},
        }

        print(f"\nNew chat request: \"{query}\"")
        final_state = self.graph.invoke(state)

        return {
            "response": final_state["response"],
            "conversationId": final_state["conversation_id"],
            "metadata": final_state["metadata"],
            "sources": [
                {
                    "title": item["metadata"].get("title"),
                    "url": item["metadata"].get("url"),
                    "similarity": item["similarity"],
                }
                for item in final_state["retrieved_context"]
            ],
        }

    def get_conversation_history(self, conversation_id: str) -> list[dict[str, Any]]:
        return self.conversation_history.get(conversation_id, [])


def main() -> None:
    print("=" * 50)
    print("   EXERCISE 3: APP DEVELOPMENT - CHAT AGENT")
    print("=" * 50)
    print("Role: Application Developer")
    print("Task: Build RAG chat agent with LangGraph\n")

    try:
        # TODO: Uncomment when you have completed the TODO items above
        # agent = RAGChatAgent()
        #
        # test_query = "What is machine learning?"
        # result = agent.chat(test_query)
        #
        # print(f"\nQ: {test_query}")
        # print(f"A: {result['response']}")
        # print(f"Sources: {', '.join(source['title'] for source in result['sources'])}")

        print("TODO LIST:")
        print("1. Review LangGraph agent architecture")
        print("2. Complete search_vector_database() function")
        print("3. Complete generate_response() with Bedrock")
        print("4. Complete update_memory() for conversations")
        print("5. Test chat functionality")
        print("\nTip: Make sure ChromaDB is available and Exercise 2 completed")
        print("Tip: Test individual methods before the full agent")
    except Exception as error:
        print(f"Agent initialization failed: {error}")
        print("\nTroubleshooting:")
        print("1. Run Exercise 2 first to create vector database")
        print("2. Configure AWS credentials")
        print("3. Check exercise-3-app-development/vector-db-config.json")


if __name__ == "__main__":
    main()
