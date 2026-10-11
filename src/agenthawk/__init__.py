"""AgentHawk public import surface.

The implementation remains in ``mcp_trace`` so existing integrations keep
working. New code may import the query functions from ``agenthawk``.
"""
from mcp_trace import *  # noqa: F401,F403
from mcp_trace import __version__
