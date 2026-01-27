"""
Feedback analysis module for chord test app.

This module provides functions for analyzing feedback collected from the
chord test app and generating statistical reports.
"""
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any


def load_feedback_data(directory="feedback") -> List[Dict[str, Any]]:
    """
    Load all feedback data from JSONL files.

    Args:
        directory: Directory containing feedback files

    Returns:
        List of feedback entries
    """
    all_feedback = []

    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    for filename in os.listdir(directory):
        if filename.endswith(".jsonl"):
            with open(os.path.join(directory, filename), "r") as f:
                for line in f:
                    try:
                        feedback = json.loads(line.strip())
                        all_feedback.append(feedback)
                    except json.JSONDecodeError:
                        continue

    return all_feedback


def analyze_feedback(feedback_data: List[Dict[str, Any]]):
    """
    Analyze feedback data and generate reports.

    Args:
        feedback_data: List of feedback entries

    Returns:
        Dictionary with summary statistics
    """
    if not feedback_data:
        return {"total_feedback": 0, "message": "No feedback data available"}

    # Convert to pandas DataFrame for analysis
    df = pd.DataFrame(feedback_data)

    # Calculate average ratings by algorithm version
    avg_by_algorithm = df.groupby("algorithm_version")["rating"].mean()

    # Calculate average ratings by cadence type
    avg_by_cadence = df.groupby(["cadence_type", "algorithm_version"])["rating"].mean().unstack()

    # Generate plots
    plt.figure(figsize=(12, 6))

    # Plot average ratings by algorithm version
    plt.subplot(1, 2, 1)
    avg_by_algorithm.plot(kind="bar")
    plt.title("Average Rating by Algorithm Version")
    plt.ylabel("Rating (1-5)")

    # Plot average ratings by cadence type
    plt.subplot(1, 2, 2)
    avg_by_cadence.plot(kind="bar")
    plt.title("Average Rating by Cadence Type")
    plt.ylabel("Rating (1-5)")

    # Save plots
    os.makedirs("feedback", exist_ok=True)
    plt.tight_layout()
    plt.savefig("feedback/analysis_report.png")

    # Return summary stats
    return {
        "total_feedback": len(df),
        "avg_by_algorithm": avg_by_algorithm.to_dict(),
        "avg_by_cadence": avg_by_cadence.to_dict(),
        "common_comments": extract_common_comments(feedback_data)
    }


def extract_common_comments(feedback_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Extract common themes from feedback comments.

    Args:
        feedback_data: List of feedback entries

    Returns:
        Dictionary mapping keywords to frequency counts
    """
    # Simple keyword analysis
    keywords = [
        "spacing", "voice leading", "bass", "soprano",
        "leap", "smooth", "awkward", "unmusical", "musical"
    ]

    counts = {keyword: 0 for keyword in keywords}

    for entry in feedback_data:
        if "comments" in entry and entry["comments"]:
            comment = entry["comments"].lower()
            for keyword in keywords:
                if keyword in comment:
                    counts[keyword] += 1

    return counts


def generate_report():
    """
    Generate an analysis report of all feedback data.

    Returns:
        Dictionary with report data
    """
    feedback = load_feedback_data()
    return analyze_feedback(feedback)