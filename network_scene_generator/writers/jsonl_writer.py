from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False))
            handle.write("\n")
