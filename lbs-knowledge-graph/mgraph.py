"""
MGraph compatibility shim.

Re-exports MGraph from src.graph.mgraph_compat so that
'from mgraph import MGraph' works throughout the codebase.
"""

from src.graph.mgraph_compat import MGraph, MNode, MEdge

__all__ = ['MGraph', 'MNode', 'MEdge']
