#!/bin/bash
# Run unit tests for g8aural

set -e

echo "Running unit tests..."

# Activate virtual environment
source .venv/bin/activate

# Run tests
python3 -m pytest tests/ -v

echo "All tests passed!"
