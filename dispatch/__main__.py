"""Command-line entry point for Dispatch."""

from .app import DispatchApp


def main() -> None:
    DispatchApp().run()


if __name__ == "__main__":
    main()
