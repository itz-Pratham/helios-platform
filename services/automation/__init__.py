"""
Automation Package

MAPE-K (Monitor-Analyze-Plan-Execute-Knowledge) closed-loop automation.
Based on research paper: "AI-Driven Self-Healing Cloud Systems"
"""

from .mape_k import MAPEKLoop, MAPEKPhase

__all__ = [
    "MAPEKLoop",
    "MAPEKPhase"
]
