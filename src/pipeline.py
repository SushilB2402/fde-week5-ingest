"""
Week 5 ingestion pipeline.
"""

from pathlib import Path


def main() -> None:

    Path("data/out").mkdir(
        parents=True,
        exist_ok=True,
    )

    Path("reports").mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Pipeline started")
    print("Output folders ready")


if __name__ == "__main__":
    main()
    