"""
CLI entry point for the semantic extraction layer.

Usage:
    python -m app.semantic.run_semantic
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    from app.semantic.processor import run_semantic

    run_semantic()
