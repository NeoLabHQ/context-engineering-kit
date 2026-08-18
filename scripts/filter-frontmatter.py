#!/usr/bin/env python3
"""Strip every YAML front-matter field except `name`/`description` in place.

Used by `just sync-provider-formats` to clean the root-level agents/ and
skills/ bundle: Claude Code-specific front-matter fields (`model`, `color`,
`allowed-tools`, ...) are meaningless to Gemini CLI / Antigravity CLI and
would otherwise leak provider-specific metadata into their bundle.

Kept intentionally dependency-free (stdlib only, no PyYAML) so it runs on
any Python 3 install, including CI runners that don't have YAML libraries
pre-installed.
"""
import sys

FRONT_MATTER_DELIMITER = "---"
KEPT_FIELDS = {"name", "description"}


def filter_front_matter(text: str) -> str:
    """Return `text` with only `name`/`description` left in its front matter.

    Front-matter fields are grouped by their key line rather than parsed as
    YAML: a field starts at a line whose first character is not whitespace
    (a top-level "key: value" line). Every subsequent line that IS indented
    belongs to that field's value, which is exactly how YAML distinguishes a
    block-scalar or wrapped multi-line value from the next key — so this
    grouping preserves multi-line descriptions, and any colons or quotes
    inside them, without needing a YAML parser at all.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != FRONT_MATTER_DELIMITER:
        return text  # no front matter: nothing to filter

    closing_line_index = next(
        (i for i in range(1, len(lines)) if lines[i].rstrip("\n") == FRONT_MATTER_DELIMITER),
        None,
    )
    if closing_line_index is None:
        return text  # unterminated front matter: leave the file untouched

    body = "".join(lines[closing_line_index + 1:])
    fields = _group_into_fields(lines[1:closing_line_index])

    kept_text = "".join(field_text for key, field_text in fields if key in KEPT_FIELDS)
    return f"{FRONT_MATTER_DELIMITER}\n{kept_text}{FRONT_MATTER_DELIMITER}\n{body}"


def _group_into_fields(front_matter_lines: list[str]) -> list[list[str]]:
    """Group front-matter lines into `[key, raw_text]` pairs, one per field."""
    fields: list[list[str]] = []
    for line in front_matter_lines:
        is_new_field = line[:1] not in ("", " ", "\t", "\n")
        if is_new_field:
            key = line.split(":", 1)[0].strip()
            fields.append([key, line])
        elif fields:
            fields[-1][1] += line
    return fields


def main() -> None:
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as f:
            original = f.read()

        filtered = filter_front_matter(original)
        if filtered != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(filtered)


if __name__ == "__main__":
    main()
