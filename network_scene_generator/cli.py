from __future__ import annotations

import argparse
from typing import Sequence

from .cleaner import clean
from .runner import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="network_scene_generator",
        description="Generate or clean reproducible network scene outputs from one YAML config file.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("generate", "clean"),
        default="generate",
        help="Use 'generate' to build scenes or 'clean' to remove generated scene directories for the config output_root.",
    )
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "clean":
        output_root, removed = clean(args.config)
        if removed:
            print(f"Removed {len(removed)} scene directories from {output_root}")
            for scene_dir in removed:
                print(scene_dir)
        else:
            print(f"No generated scene directories found under {output_root}")
        return 0

    scene_dirs = run(args.config)
    for scene_dir in scene_dirs:
        print(scene_dir)
    return 0
