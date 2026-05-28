"""Streamlit entry point for the AgroVision simulator prototype.

This file should stay focused on page orchestration. Decision formulas,
input validation, and reusable UI sections belong in the src package.
"""

from src.ui_components import render_app_shell


def main() -> None:
    """Run the Streamlit app."""
    render_app_shell()


if __name__ == "__main__":
    main()

