# Exercise 1: Data Science - Web Data Exploration

**Role:** Data Scientist  
**Time:** 22.5 minutes  
**Goal:** Analyze web content to understand patterns and prepare data for the pipeline

## Learning Objectives

- Use Python for data analysis with pandas/numpy-style patterns
- Implement web scraping with error handling
- Generate statistical insights from unstructured data
- Create data summaries for downstream processing

## Your Mission

You are analyzing technology blog posts to understand trending topics. Your analysis will inform what content gets processed into embeddings.

## TODO List (Complete in Order)

### Step 1: Basic Data Collection (5 min)

- [ ] Run the starter code to see the scaffolding
- [ ] Complete the `fetch_web_content()` function
- [ ] Add error handling for failed requests
- [ ] Test with 3-5 tech blog URLs

### Step 2: Data Analysis (10 min)

- [ ] Complete the `analyze_text_content()` function
- [ ] Implement word frequency analysis
- [ ] Calculate readability metrics
- [ ] Generate content statistics

### Step 3: Data Insights (7.5 min)

- [ ] Complete the `generate_insights()` function
- [ ] Identify trending topics
- [ ] Create data quality report
- [ ] Export findings for data engineers

## Quick Start

```bash
cd exercise-1-data-science
python starter_code.py
```

## Expected Output

```text
=== WEB CONTENT ANALYSIS RESULTS ===
Analyzed 5 articles
Average length: 1,247 words
Top topics: ["AI", "Python", "Machine Learning"]
Quality score: 8.2/10
Recommendation: Process all articles for embeddings
```

## Key Concepts

- **Data Quality Assessment**: Not all web content is suitable for embeddings
- **Statistical Analysis**: Use Python like you would use pandas
- **Insight Generation**: Summarize findings for technical handoff

## Success Criteria

- [ ] Successfully fetch and parse 5+ web articles
- [ ] Generate meaningful statistics about content
- [ ] Identify which content should be processed further
- [ ] Create data summary for Exercise 2

## Stuck? Quick Tips

- Focus on TODO comments only
- The scaffolding handles complex parts
- Use `print()` liberally for debugging
- Do not optimize. Just get it working.

---

**Next:** Your analysis results feed into `exercise-2-data-engineering`.
