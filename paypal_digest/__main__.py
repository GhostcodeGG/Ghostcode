"""Command-line entry point for generating the PayPal daily digest."""

from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from .config import load_config
from .digest import run


def validate_output_path(output_path: Path) -> Path:
    """Validate that the output path is safe to write to.

    Args:
        output_path: The requested output path

    Returns:
        The validated absolute path

    Raises:
        ValueError: If the path is outside the project directory or suspicious
    """
    try:
        # Resolve to absolute path
        resolved = output_path.resolve()
        project_root = Path.cwd().resolve()

        # Check if path is within project directory
        try:
            resolved.relative_to(project_root)
        except ValueError:
            raise ValueError(
                f"Output path must be within project directory. "
                f"Got: {resolved}, expected under: {project_root}"
            )

        # Ensure parent directory exists or can be created
        resolved.parent.mkdir(parents=True, exist_ok=True)

        return resolved

    except Exception as e:
        raise ValueError(f"Invalid output path '{output_path}': {e}")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the PayPal daily news digest")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional override for the digest output path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(verbose=args.verbose)

    config = load_config()
    if args.output:
        validated_output = validate_output_path(args.output)
        config = replace(config, digest_dir=validated_output.parent)
    result = run(config)
    if args.output:
        validated_output = validate_output_path(args.output)
        validated_output.write_text(result.digest.to_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
