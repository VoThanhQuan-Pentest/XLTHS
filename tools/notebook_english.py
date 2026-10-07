"""Translate notebook prose and display text while preserving computation."""

from __future__ import annotations

import ast
import io
import json
from pathlib import Path
import re
import tokenize


TEXT = json.loads(Path(__file__).with_name("notebook_english_text.json").read_text(encoding="utf-8"))
STUDENT_NAMES = ("Võ Thanh Quân", "Vương Quốc Trung", "Đinh Huỳnh Nguyên Khang")
VIETNAMESE_LETTERS = (
    "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ"
    "òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
)
ACCENTED_TEXT = re.compile("[" + VIETNAMESE_LETTERS + VIETNAMESE_LETTERS.upper() + "]")


def has_untranslated_text(value: str) -> bool:
    """Detect accented prose, allowing the original student names."""
    for name in STUDENT_NAMES:
        value = value.replace(name, "")
    return bool(ACCENTED_TEXT.search(value))


def english_markdown(value: str) -> str:
    """Return the matching English section, rejecting unrecognized prose."""
    result = TEXT["markdown"].get(value, value)
    if has_untranslated_text(result):
        raise ValueError(f"Missing English Markdown translation: {value[:100]!r}")
    return result


def _translate_fstring(value: str) -> str:
    """Translate only literal display fragments, retaining expression syntax."""
    fragments = TEXT["fstrings"]
    if value in fragments:
        return fragments[value]
    for source in sorted(fragments, key=len, reverse=True):
        if source in value:
            value = value.replace(source, fragments[source])
    if has_untranslated_text(value):
        raise ValueError(f"Missing English f-string translation: {value!r}")
    return value


def english_code(source: str) -> str:
    """Translate comments/docstrings/UI strings using their original token spans.

    Nontext tokens, indentation and expressions keep their original spelling.
    Python 3.12+ f-string fragments and earlier whole f-string tokens are handled.
    """
    offsets, offset = [], 0
    for line in source.splitlines(keepends=True):
        offsets.append(offset)
        offset += len(line)
    offsets.append(offset)
    replacements = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        value = token.string
        replacement = value
        if token.type == tokenize.COMMENT:
            replacement = TEXT["comments"].get(value, value)
        elif token.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
            replacement = _translate_fstring(value)
        elif token.type == tokenize.STRING:
            prefix = re.match(r"(?i)^([rubf]*)", value).group(1).lower()
            if "f" in prefix:
                replacement = _translate_fstring(value)
            else:
                literal = ast.literal_eval(value)
                if isinstance(literal, str) and literal in TEXT["strings"]:
                    translated = TEXT["strings"][literal]
                    if value.startswith(('"""', "'''")):
                        replacement = '"""' + translated + '"""'
                    else:
                        replacement = json.dumps(translated, ensure_ascii=False)
        if token.type in (tokenize.COMMENT, tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)):
            if has_untranslated_text(replacement):
                raise ValueError(f"Missing English code translation: {value[:140]!r}")
        if replacement != value:
            start = offsets[token.start[0] - 1] + token.start[1]
            end = offsets[token.end[0] - 1] + token.end[1]
            replacements.append((start, end, replacement))
    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    ast.parse(source)
    return source


def validate_english_notebook(nb) -> None:
    """Check cell sources and rendered text outputs for untranslated prose."""
    for index, cell in enumerate(nb.cells, 1):
        if has_untranslated_text(cell.source):
            raise ValueError(f"Cell {index} contains untranslated prose")
        for output in cell.get("outputs", []):
            texts = [output.get("text", "")]
            texts.extend(value for mime, value in output.get("data", {}).items()
                         if mime.startswith("text/"))
            for value in texts:
                text = "".join(value) if isinstance(value, list) else value
                if has_untranslated_text(text):
                    raise ValueError(f"Cell {index} output contains untranslated prose")
