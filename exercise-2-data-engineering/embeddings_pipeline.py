"""Exercise 2: Data Engineering - Embeddings Pipeline."""

from __future__ import annotations

import json
import os
import random
import re
import time
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PipelineState:
    input_data: dict[str, Any] | None = None
    processed_content: list[dict[str, Any]] = field(default_factory=list)
    embeddings: list[dict[str, Any]] = field(default_factory=list)
    stored_vectors: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    metrics: dict[str, int] = field(
        default_factory=lambda: {"processed": 0, "embedded": 0, "stored": 0, "failed": 0}
    )
    report: dict[str, Any] | None = None


class EmbeddingsPipeline:
    def __init__(self) -> None:
        self.collection_name = "tech-content-vectors"
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION")
            or os.getenv("BEDROCK_AWS_REGION")
            or "us-east-1",
        )
        self.chroma_client = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db"))
        self.graph = None
        self.initialize_pipeline()

    def initialize_pipeline(self) -> None:
        # Create LangGraph workflow with simplified state management.
        workflow = StateGraph(dict)

        workflow.add_node("load_data", lambda state: {"state": self.load_data(state["state"])})
        workflow.add_node(
            "process_content", lambda state: {"state": self.process_content(state["state"])}
        )
        workflow.add_node(
            "generate_embeddings",
            lambda state: {"state": self.generate_embeddings(state["state"])},
        )
        workflow.add_node(
            "store_vectors", lambda state: {"state": self.store_vectors(state["state"])}
        )
        workflow.add_node(
            "generate_report", lambda state: {"state": self.generate_report(state["state"])}
        )

        workflow.add_edge(START, "load_data")
        workflow.add_edge("load_data", "process_content")
        workflow.add_edge("process_content", "generate_embeddings")
        workflow.add_edge("generate_embeddings", "store_vectors")
        workflow.add_edge("store_vectors", "generate_report")
        workflow.add_edge("generate_report", END)

        self.graph = workflow.compile()

    def load_data(self, state: PipelineState) -> PipelineState:
        print("Loading data from Data Science analysis...")

        try:
            data_path = BASE_DIR / "data-science-output.json"
            if not data_path.exists():
                raise FileNotFoundError("Data Science output not found. Run Exercise 1 first.")

            state.input_data = json.loads(data_path.read_text(encoding="utf-8"))
            content_count = len(state.input_data.get("contentData", []))
            print(f"Loaded {content_count} articles from analysis")
        except Exception as error:
            print(f"Failed to load input data: {error}")
            state.errors.append({"stage": "loadData", "error": str(error)})

        return state

    def process_content(self, state: PipelineState) -> PipelineState:
        # TODO: Implement content processing for embedding pipeline
        # Hints:
        # 1. Take content from state.input_data["contentData"]
        # 2. Clean and chunk content for optimal embedding
        # 3. Add metadata (title, url, keywords, etc.)
        # 4. Handle different content types and sizes
        print("Processing content for embeddings...")

        if not state.input_data or not state.input_data.get("contentData"):
            state.errors.append({"stage": "processContent", "error": "No content data available"})
            return state

        try:
            for article in state.input_data["contentData"]:
                print(f"Processing: {article.get('title', 'Untitled')}")

                # TODO: Implement text chunking strategy
                # chunks = self.create_simple_chunks(article["content"], 500)
                chunks = self.create_simple_chunks(article.get("content", ""), 500)

                for index, chunk in enumerate(chunks):
                    # TODO: Create rich metadata for each chunk
                    processed_chunk = {
                        "id": str(uuid.uuid4()),
                        "content": chunk,
                        "metadata": {
                            "title": article.get("title"),
                            "url": article.get("url"),
                            "chunkIndex": index,
                            "totalChunks": len(chunks),
                            "keywords": article.get("topKeywords", []),
                            "qualityScore": article.get("qualityScore"),
                            "wordCount": len(chunk.split()),
                            "processedAt": utc_now(),
                        },
                    }
                    state.processed_content.append(processed_chunk)

                state.metrics["processed"] += 1

            print(f"Processed {len(state.processed_content)} content chunks")
        except Exception as error:
            print(f"Content processing failed: {error}")
            state.errors.append({"stage": "processContent", "error": str(error)})
            state.metrics["failed"] += 1

        return state

    def create_simple_chunks(self, content: str, max_words: int) -> list[str]:
        sentences = [sentence.strip() for sentence in re.split(r"[.!?]+", content) if sentence.strip()]
        chunks: list[str] = []
        current_chunk = ""
        current_word_count = 0

        for sentence in sentences:
            sentence_word_count = len(sentence.split())

            if current_word_count + sentence_word_count > max_words and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_word_count = sentence_word_count
            else:
                current_chunk = f"{current_chunk}. {sentence}" if current_chunk else sentence
                current_word_count += sentence_word_count

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        if not chunks:
            words = content.split()
            chunks = [" ".join(words[index : index + max_words]) for index in range(0, len(words), max_words)]

        return chunks

    def generate_embeddings(self, state: PipelineState) -> PipelineState:
        print("Generating embeddings with AWS Bedrock...")

        if not state.processed_content:
            state.errors.append(
                {"stage": "generateEmbeddings", "error": "No processed content available"}
            )
            return state

        try:
            for chunk in state.processed_content:
                print(f"Embedding chunk: {chunk['id'][:8]}...")
                embedding = self.call_bedrock_embeddings(chunk["content"])

                if embedding:
                    state.embeddings.append(
                        {
                            "id": chunk["id"],
                            "vector": embedding,
                            "content": chunk["content"],
                            "metadata": chunk["metadata"],
                        }
                    )
                    state.metrics["embedded"] += 1
                else:
                    state.metrics["failed"] += 1

                # Rate limiting delay.
                time.sleep(0.1)

            print(f"Generated {len(state.embeddings)} embeddings")
        except Exception as error:
            print(f"Embedding generation failed: {error}")
            state.errors.append({"stage": "generateEmbeddings", "error": str(error)})

        return state

    def call_bedrock_embeddings(self, text: str) -> list[float]:
        try:
            model_id = os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID")
            if not model_id:
                raise ValueError("BEDROCK_EMBEDDINGS_MODEL_ID is not configured")

            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({"inputText": text}),
            )
            payload = json.loads(response["body"].read().decode("utf-8"))
            embedding = payload.get("embedding")
            if not isinstance(embedding, list):
                raise ValueError("No embedding array returned")
            return embedding
        except Exception as error:
            print(f"Bedrock API error: {error}, using mock embedding")
            return self.mock_bedrock_embeddings(text)

    def mock_bedrock_embeddings(self, text: str) -> list[float]:
        # TODO: Replace with actual Bedrock call
        _ = text
        return [random.random() - 0.5 for _ in range(1536)]

    def store_vectors(self, state: PipelineState) -> PipelineState:
        print("Storing vectors in ChromaDB...")

        if not state.embeddings:
            state.errors.append({"stage": "storeVectors", "error": "No embeddings to store"})
            return state

        storage_dir = BASE_DIR / "chroma_db"
        storage_dir.mkdir(parents=True, exist_ok=True)

        try:
            print(f"Creating/accessing collection: {self.collection_name}")
            print("Using ChromaDB persistent storage in ./chroma_db/")

            use_file_storage = False
            try:
                collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Tech content embeddings for semantic search"},
                )

                batch_size = 10
                for index in range(0, len(state.embeddings), batch_size):
                    batch = state.embeddings[index : index + batch_size]
                    collection.add(
                        ids=[item["id"] for item in batch],
                        embeddings=[item["vector"] for item in batch],
                        documents=[item["content"] for item in batch],
                        metadatas=[
                            {
                                "title": item["metadata"]["title"],
                                "url": item["metadata"]["url"],
                                "chunkIndex": item["metadata"]["chunkIndex"],
                                "totalChunks": item["metadata"]["totalChunks"],
                                "keywords": json.dumps(item["metadata"]["keywords"]),
                                "qualityScore": item["metadata"]["qualityScore"],
                                "wordCount": item["metadata"]["wordCount"],
                                "processedAt": item["metadata"]["processedAt"],
                            }
                            for item in batch
                        ],
                    )

                    print(f"Stored batch {index // batch_size + 1}: {len(batch)} vectors")
                    state.stored_vectors.extend(batch)
                    state.metrics["stored"] += len(batch)
            except Exception:
                print("ChromaDB not available, using local file storage")
                use_file_storage = True

            if use_file_storage:
                collection_file = storage_dir / f"{self.collection_name}.json"
                collection_data = {
                    "name": self.collection_name,
                    "metadata": {"description": "Tech content embeddings for semantic search"},
                    "embeddings": [
                        {
                            "id": item["id"],
                            "vector": item["vector"],
                            "document": item["content"],
                            "metadata": item["metadata"],
                        }
                        for item in state.embeddings
                    ],
                    "createdAt": utc_now(),
                    "totalVectors": len(state.embeddings),
                }
                collection_file.write_text(json.dumps(collection_data, indent=2), encoding="utf-8")
                print(f"Stored {len(state.embeddings)} vectors in local file: {collection_file}")
                state.stored_vectors.extend(state.embeddings)
                state.metrics["stored"] = len(state.embeddings)

            print(f"Stored {len(state.stored_vectors)} vectors successfully")
        except Exception as error:
            print(f"Vector storage failed: {error}")
            state.errors.append({"stage": "storeVectors", "error": str(error)})

        return state

    def generate_report(self, state: PipelineState) -> PipelineState:
        print("\nGenerating pipeline report...")

        duration = round(time.time() - state.start_time)
        report = {
            "pipelineRun": {
                "timestamp": utc_now(),
                "status": "SUCCESS" if not state.errors else "PARTIAL_SUCCESS",
                "duration": f"{duration} seconds",
            },
            "metrics": state.metrics,
            "dataQuality": {
                "inputArticles": len(state.input_data.get("contentData", [])) if state.input_data else 0,
                "processedChunks": len(state.processed_content),
                "successfulEmbeddings": len(state.embeddings),
                "storedVectors": len(state.stored_vectors),
                "errorRate": len(state.errors) / max(1, len(state.processed_content)),
            },
            "vectorDatabase": {
                "collection": self.collection_name,
                "totalVectors": len(state.stored_vectors),
                "dimensions": 1536,
                "ready": len(state.stored_vectors) > 0,
            },
            "errors": state.errors,
            "nextSteps": [
                "Vector database ready for semantic search",
                "Proceed to Exercise 3 for chat agent development",
                "Connection details exported to exercise-3-app-development",
            ],
        }

        config_path = PROJECT_DIR / "exercise-3-app-development" / "vector-db-config.json"
        config_path.write_text(
            json.dumps(
                {
                    "collection": self.collection_name,
                    "vectorCount": len(state.stored_vectors),
                    "ready": True,
                    "createdAt": utc_now(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        report_path = PROJECT_DIR / "pipeline-report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        self.display_report(report)
        state.report = report

        return state

    def display_report(self, report: dict[str, Any]) -> None:
        print("\n=== EMBEDDINGS PIPELINE RESULTS ===")
        print(f"Status: {report['pipelineRun']['status']}")
        print(f"Processed: {report['metrics']['processed']} articles")
        print(f"Generated: {report['metrics']['embedded']} embeddings")
        print(f"Stored: {report['metrics']['stored']} vectors")
        print(f"Errors: {len(report['errors'])}")
        print(f"Quality Score: {(10 - report['dataQuality']['errorRate'] * 10):.1f}/10")
        print("Ready for: Chat agent deployment")
        print("=====================================\n")

        if report["errors"]:
            print("Errors encountered:")
            for index, error in enumerate(report["errors"], start=1):
                print(f"{index}. {error['stage']}: {error['error']}")
            print()

        print("Output files generated:")
        print("  - pipeline-report.json (detailed metrics)")
        print("  - exercise-3-app-development/vector-db-config.json")

    def run(self) -> PipelineState:
        print("Starting embeddings pipeline...\n")
        initial_state = {"state": PipelineState()}
        result = self.graph.invoke(initial_state)
        return result["state"]


def main() -> None:
    print("=" * 50)
    print("  EXERCISE 2: DATA ENGINEERING - EMBEDDINGS")
    print("=" * 50)
    print("Role: Data Engineer")
    print("Task: Build embeddings pipeline with LangGraph\n")

    pipeline = EmbeddingsPipeline()
    pipeline.run()

    print("\nPipeline completed successfully!")
    print("Tip: Check pipeline-report.json for detailed metrics")
    print("Tip: ChromaDB data stored in exercise-2-data-engineering/chroma_db/")


if __name__ == "__main__":
    main()
