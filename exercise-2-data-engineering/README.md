# Exercise 2: Data Engineering - Embeddings Pipeline

**Role:** Data Engineer  
**Time:** 30 minutes  
**Goal:** Transform analyzed content into searchable embeddings using LangGraph and AWS Bedrock

## Learning Objectives

- Build LangGraph workflows for data processing
- Generate embeddings using AWS Bedrock (Titan)
- Implement vector storage with metadata
- Add data quality monitoring and error handling

## Your Mission

Take the analyzed content from Exercise 1 and build a production-ready embeddings pipeline that stores vectors with rich metadata for the chat agent.

## TODO List (Complete in Order)

### Step 1: LangGraph Pipeline Setup (7.5 min)

- [ ] Review the LangGraph state management
- [ ] Complete the `process_content` node
- [ ] Add error handling for failed processing
- [ ] Test pipeline with sample data

### Step 2: AWS Bedrock Integration (10 min)

- [ ] Complete the `generate_embeddings` node
- [ ] Configure Bedrock Titan embeddings model
- [ ] Handle API rate limiting and retries
- [ ] Test embedding generation

### Step 3: Vector Storage (7.5 min)

- [ ] Complete the `store_vectors` node
- [ ] Set up ChromaDB collection with metadata
- [ ] Implement batch insertion for efficiency
- [ ] Add data validation

### Step 4: Pipeline Orchestration (5 min)

- [ ] Complete the LangGraph workflow definition
- [ ] Add monitoring and logging
- [ ] Test end-to-end pipeline
- [ ] Generate pipeline report

## Quick Start

```bash
cd exercise-2-data-engineering
python embeddings_pipeline.py
```

## Expected Output

```text
=== EMBEDDINGS PIPELINE RESULTS ===
Processed: 4/5 articles successfully
Generated: 12 embeddings (chunked content)
Stored: 12 vectors in ChromaDB
Quality Score: 9.2/10
Ready for: Chat agent queries
```

## Key Concepts

- **LangGraph State**: Manages data flow between pipeline stages
- **Chunking Strategy**: Split content for optimal embedding size
- **Metadata Enrichment**: Add searchable attributes to vectors
- **Error Recovery**: Handle API failures gracefully

## Success Criteria

- [ ] Successfully process data from Exercise 1
- [ ] Generate embeddings using AWS Bedrock
- [ ] Store vectors with rich metadata
- [ ] Create pipeline monitoring dashboard
- [ ] Export connection details for Exercise 3

## Stuck? Quick Tips

- Check AWS credentials with `aws sts get-caller-identity`
- Bedrock may need model access enabled in the AWS console
- ChromaDB persists locally in `chroma_db/` for this tutorial
- Focus on TODO comments. The scaffolding handles complexity.

---

**Next:** Your vector database powers the chat agent in `exercise-3-app-development`.
