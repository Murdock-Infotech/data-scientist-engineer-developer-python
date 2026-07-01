"""Exercise 1: Data Science - Web Data Exploration.

This file is intentionally scaffolded for the workshop. Complete the TODO
sections during the exercise, then uncomment the analyzer.fetch_and_analyze()
call in main().
"""

from __future__ import annotations

import json
import re
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests
from bs4 import BeautifulSoup


SAMPLE_URLS = [
    # Bad link below
    "https://blog.openai.com/gpt-4",
    "https://aws.amazon.com/blogs/machine-learning/",
    "https://developers.googleblog.com/2023/05/introducing-palm-2.html",
    # Bad link above
    # Add more URLs as needed
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DataAnalysisTools:
    """Small Python equivalent of the JavaScript pandas-like helper."""

    @staticmethod
    def create_data_frame(data: list[dict[str, Any]]) -> dict[str, Any]:
        def describe(column: str) -> dict[str, Any]:
            values = [row[column] for row in data if isinstance(row.get(column), (int, float))]
            if not values:
                return {
                    "count": 0,
                    "mean": None,
                    "median": None,
                    "std": None,
                    "min": None,
                    "max": None,
                }

            return {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
            }

        def group_by(column: str) -> dict[Any, list[dict[str, Any]]]:
            groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
            for row in data:
                groups[row.get(column)].append(row)
            return dict(groups)

        def filter_rows(predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
            return DataAnalysisTools.create_data_frame([row for row in data if predicate(row)])

        return {
            "data": data,
            "length": len(data),
            "columns": list(data[0].keys()) if data else [],
            "describe": describe,
            "group_by": group_by,
            "filter": filter_rows,
        }

    class numpy:
        """Tiny numpy-like namespace for workshop parity."""

        @staticmethod
        def array(data: list[Any]) -> list[Any]:
            return data

        @staticmethod
        def mean(values: list[float]) -> float:
            return statistics.mean(values) if values else 0

        @staticmethod
        def std(values: list[float]) -> float:
            return statistics.stdev(values) if len(values) > 1 else 0

        @staticmethod
        def unique(values: list[Any]) -> list[Any]:
            return list(dict.fromkeys(values))

        @staticmethod
        def count_non_zero(values: list[Any]) -> int:
            return sum(1 for value in values if value not in (0, None))


class WebContentAnalyzer:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []
        self.insights: dict[str, Any] = {}

    def fetch_web_content(self, url: str) -> dict[str, Any] | None:
        # TODO: Implement web content fetching
        # Hints:
        # 1. Use requests.get() to fetch the URL
        # 2. Handle errors gracefully with try/except
        # 3. Return None if fetch fails
        # 4. Use BeautifulSoup to parse HTML and extract text
        try:
            print(f"Fetching content from: {url}")

            # TODO: Add requests.get() call with proper headers
            # response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            # response.raise_for_status()

            # TODO: Parse HTML with BeautifulSoup
            # soup = BeautifulSoup(response.text, "html.parser")

            # TODO: Extract text content and remove scripts/styles
            # for tag in soup(["script", "style"]):
            #     tag.decompose()
            # title = soup.title.get_text(strip=True) if soup.title else "Untitled"
            # content = " ".join(soup.get_text(" ").split())

            # TODO: Return structured data
            return {
                "url": url,
                "title": "Sample Title",  # Replace with actual title
                "content": "Sample content...",  # Replace with actual content
                "wordCount": 100,  # Replace with actual word count
                "fetchedAt": utc_now(),
            }
        except requests.RequestException as error:
            print(f"Failed to fetch {url}: {error}")
            return None

    def analyze_text_content(self, content_data: dict[str, Any]) -> dict[str, Any]:
        # TODO: Implement text analysis (pandas-like operations)
        # Hints:
        # 1. Calculate word frequency
        # 2. Extract keywords/topics
        # 3. Measure readability
        # 4. Generate statistics
        print(f"Analyzing: {content_data['title']}")

        # TODO: Tokenize and analyze text
        words = [
            word
            for word in re.sub(r"[^\w\s]", " ", content_data["content"].lower()).split()
            if len(word) > 3
        ]

        # TODO: Calculate word frequency (like pandas value_counts())
        word_freq: Counter[str] = Counter()

        # TODO: Find top keywords
        _ = words
        _ = word_freq

        # TODO: Calculate readability metrics
        sentences = len(re.split(r"[.!?]+", content_data["content"]))
        avg_words_per_sentence = content_data["wordCount"] / max(sentences, 1)

        return {
            "url": content_data["url"],
            "title": content_data["title"],
            "wordCount": content_data["wordCount"],
            "uniqueWords": 50,  # TODO: Calculate actual unique words
            "topKeywords": ["sample", "keywords"],  # TODO: Replace with actual top words
            "readabilityScore": min(10, avg_words_per_sentence / 2),
            "qualityScore": self.calculate_quality_score(content_data),
            "analyzedAt": utc_now(),
        }

    def calculate_quality_score(self, content: dict[str, Any]) -> float:
        score = 5.0

        if content["wordCount"] > 500:
            score += 2
        if content["wordCount"] > 1000:
            score += 1

        if content.get("title") and len(content["title"]) > 20:
            score += 1

        technical_words = ["algorithm", "model", "data", "analysis", "machine", "learning"]
        tech_word_count = sum(
            1 for word in technical_words if word in content["content"].lower()
        )
        score += min(2, tech_word_count * 0.5)

        return min(10, max(1, score))

    def generate_insights(self) -> None:
        # TODO: Generate insights using DataAnalysisTools (pandas-like analysis)
        # Hints:
        # 1. Create DataFrame from results
        # 2. Calculate summary statistics
        # 3. Identify content patterns
        # 4. Make recommendations for data engineering
        print("\n=== GENERATING INSIGHTS ===")

        if not self.results:
            print("No data to analyze. Run fetch_and_analyze() first.")
            return

        # TODO: Use DataAnalysisTools to create DataFrame
        df = DataAnalysisTools.create_data_frame(self.results)
        _ = df

        # TODO: Calculate statistics (like pandas.describe())

        # TODO: Find patterns and trends

        self.insights = {
            "totalArticles": len(self.results),
            "avgWordCount": round(
                DataAnalysisTools.numpy.mean([row["wordCount"] for row in self.results])
            ),
            "avgQualityScore": round(
                DataAnalysisTools.numpy.mean([row["qualityScore"] for row in self.results]),
                1,
            ),
            "topTopics": self.extract_top_topics(),
            "recommendation": self.generate_recommendation(),
            "generatedAt": utc_now(),
        }

        self.display_insights()
        self.export_for_data_engineering()

    def extract_top_topics(self) -> list[str]:
        # TODO: Implement topic extraction across all articles
        keyword_count = Counter(
            keyword for result in self.results for keyword in result["topKeywords"]
        )
        return [keyword for keyword, _ in keyword_count.most_common(5)]

    def generate_recommendation(self) -> str:
        avg_quality = self.insights.get("avgQualityScore") or DataAnalysisTools.numpy.mean(
            [row["qualityScore"] for row in self.results]
        )

        if avg_quality >= 7:
            return "HIGH: Process all articles for embeddings - excellent content quality"
        if avg_quality >= 5:
            return "MEDIUM: Process articles with quality score > 6 for embeddings"
        return "LOW: Review content sources - quality below threshold"

    def display_insights(self) -> None:
        print("\n=== WEB CONTENT ANALYSIS RESULTS ===")
        print(f"Analyzed {self.insights['totalArticles']} articles")
        print(f"Average length: {self.insights['avgWordCount']} words")
        print(f"Average quality: {self.insights['avgQualityScore']}/10")
        print(f"Top topics: {json.dumps(self.insights['topTopics'])}")
        print(f"Recommendation: {self.insights['recommendation']}")
        print("=====================================\n")

    def export_for_data_engineering(self) -> None:
        export_data = {
            "analysis": self.insights,
            "contentData": [row for row in self.results if row["qualityScore"] >= 6],
            "exportedAt": utc_now(),
            "nextStep": "Use this data in exercise-2-data-engineering",
        }

        output_path = (
            Path(__file__).resolve().parent.parent
            / "exercise-2-data-engineering"
            / "data-science-output.json"
        )
        output_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")

        print("Results exported to exercise-2-data-engineering/data-science-output.json")
        print(f"{len(export_data['contentData'])} high-quality articles ready for embedding pipeline")

    def fetch_and_analyze(self) -> None:
        print("Starting web content analysis...\n")

        for url in SAMPLE_URLS:
            content = self.fetch_web_content(url)
            if content:
                analysis = self.analyze_text_content(content)
                self.results.append(analysis)

                # Add small delay to be respectful to servers.
                time.sleep(1)

        self.generate_insights()


def main() -> None:
    print("=" * 50)
    print("   EXERCISE 1: DATA SCIENCE - WEB ANALYSIS")
    print("=" * 50)
    print("Role: Data Scientist")
    print("Task: Analyze web content for embedding pipeline\n")

    analyzer = WebContentAnalyzer()
    _ = analyzer

    # TODO: Uncomment when you have completed the TODO items above
    # analyzer.fetch_and_analyze()

    # For now, show the scaffolding structure
    print("TODO LIST:")
    print("1. Review this starter code structure")
    print("2. Complete fetch_web_content() function")
    print("3. Complete analyze_text_content() function")
    print("4. Complete generate_insights() function")
    print("5. Test with sample URLs")
    print("\nTip: Start by uncommenting the analyzer.fetch_and_analyze() call above")
    print("Then complete each TODO section in order")


if __name__ == "__main__":
    main()
