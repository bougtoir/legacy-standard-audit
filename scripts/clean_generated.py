import shutil
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "outputs"


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    print("Removed generated outputs")


if __name__ == "__main__":
    main()
