from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.container import get_ingestion_service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local documents into the Chroma vector store.")
    parser.add_argument("--doc-dir", type=str, default=None, help="Optional document directory override.")
    args = parser.parse_args()

    service = get_ingestion_service()
    result = service.ingest(doc_dir=Path(args.doc_dir) if args.doc_dir else None)
    print(result)


if __name__ == "__main__":
    main()
