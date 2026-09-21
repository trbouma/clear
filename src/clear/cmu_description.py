"""Shared CLI input for public CMU descriptions."""

from pathlib import Path


def add_description_arguments(parser) -> None:
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--description", help="Public plain-text description (up to 10000 characters).")
    source.add_argument("--description-file", type=Path, help="Read a UTF-8 description file.")
    source.add_argument("--clear", action="store_true", help="Remove the description.")


def read_description(args) -> str:
    if args.clear:
        return ""
    try:
        text = (
            args.description_file.read_text(encoding="utf-8")
            if args.description_file is not None else args.description
        )
    except OSError as exc:
        raise ValueError(f"could not read description file: {exc}") from exc
    if len(text) > 10000:
        raise ValueError("description must be at most 10000 characters")
    return text
