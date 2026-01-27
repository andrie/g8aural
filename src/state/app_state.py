"""
Application-wide state management dataclass for g8aural.

This module provides the global app state that applies across all features.
"""
from dataclasses import dataclass
from shiny import reactive


@dataclass
class AppState:
    """Application-wide state."""

    level: reactive.Value  # Current grade level (5, 6, 7, or 8)
    restored: reactive.Value  # Whether grade restoration is complete

    @staticmethod
    def create(default_level: int = 6):
        """Factory function to create initialized state."""
        return AppState(
            level=reactive.Value(default_level),
            restored=reactive.Value(False)
        )