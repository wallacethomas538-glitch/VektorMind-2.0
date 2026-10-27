"""Backward-compatible entrypoint for VEKTORFLOW-15."""

from vektorflow.app import app

__all__ = ["app"]


if __name__ == "__main__":
    from vektorflow.__main__ import main

    main()
