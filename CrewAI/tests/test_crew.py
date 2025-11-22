"""Tests for the CrewAI crew"""
import pytest
from src.smart_scheduler.crew import create_crew


def test_crew_creation():
    """Test that crew can be created successfully"""
    crew = create_crew()
    assert crew is not None
    assert len(crew.agents) > 0
    assert len(crew.tasks) > 0

