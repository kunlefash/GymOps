#!/usr/bin/env python3
"""Helpers for rendering plain text and markdown into Atlassian Document Format."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence


ADFNode = Dict[str, Any]

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_ORDERED_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$")
_BLOCKQUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
_FENCE_RE = re.compile(r"^\s*```([A-Za-z0-9_+-]+)?\s*$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_STRONG_RE = re.compile(r"(\*\*|__)(.+?)\1")
_EM_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)")
_CODE_RE = re.compile(r"`([^`\n]+)`")


def render_adf(text: str, fmt: str = "plain") -> ADFNode:
    """Render text into an Atlassian Document Format document."""
    normalized = _normalize(text)
    content = markdown_to_blocks(normalized) if fmt == "markdown" else plain_to_blocks(normalized)
    if not content:
        content = [_paragraph_node("")]  # Jira expects a non-empty doc body.
    return {"type": "doc", "version": 1, "content": content}


def _normalize(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def plain_to_blocks(text: str) -> List[ADFNode]:
    if not text:
        return []
    blocks = re.split(r"\n\s*\n", text)
    return [_paragraph_node(block) for block in blocks if block.strip()]


def markdown_to_blocks(text: str) -> List[ADFNode]:
    if not text:
        return []

    lines = text.split("\n")
    nodes: List[ADFNode] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if not line.strip():
            index += 1
            continue

        fence_match = _FENCE_RE.match(line)
        if fence_match:
            language = fence_match.group(1)
            index += 1
            code_lines: List[str] = []
            while index < len(lines) and not _FENCE_RE.match(lines[index]):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines) and _FENCE_RE.match(lines[index]):
                index += 1
            nodes.append(_code_block_node("\n".join(code_lines), language))
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            nodes.append(_heading_node(level, heading_match.group(2)))
            index += 1
            continue

        if _BLOCKQUOTE_RE.match(line):
            quote_lines: List[str] = []
            while index < len(lines):
                quote_match = _BLOCKQUOTE_RE.match(lines[index])
                if not quote_match:
                    break
                quote_lines.append(quote_match.group(1))
                index += 1
            quote_content = plain_to_blocks("\n".join(quote_lines))
            nodes.append({"type": "blockquote", "content": quote_content or [_paragraph_node("")]})
            continue

        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            items: List[ADFNode] = []
            while index < len(lines):
                current_match = _BULLET_RE.match(lines[index])
                if not current_match:
                    break
                items.append(_list_item_node(current_match.group(1)))
                index += 1
            nodes.append({"type": "bulletList", "content": items})
            continue

        ordered_match = _ORDERED_RE.match(line)
        if ordered_match:
            items = []
            order = 1
            while index < len(lines):
                current_match = _ORDERED_RE.match(lines[index])
                if not current_match:
                    break
                items.append(_list_item_node(current_match.group(2)))
                index += 1
            nodes.append({"type": "orderedList", "attrs": {"order": order}, "content": items})
            continue

        paragraph_lines = [line]
        index += 1
        while index < len(lines):
            next_line = lines[index]
            if not next_line.strip():
                break
            if (
                _FENCE_RE.match(next_line)
                or _HEADING_RE.match(next_line)
                or _BLOCKQUOTE_RE.match(next_line)
                or _BULLET_RE.match(next_line)
                or _ORDERED_RE.match(next_line)
            ):
                break
            paragraph_lines.append(next_line)
            index += 1
        nodes.append(_paragraph_node("\n".join(paragraph_lines), markdown=True))

    return nodes


def _heading_node(level: int, text: str) -> ADFNode:
    return {"type": "heading", "attrs": {"level": level}, "content": _inline_nodes(text, markdown=True)}


def _paragraph_node(text: str, markdown: bool = False) -> ADFNode:
    lines = text.split("\n") if text else [""]
    content: List[ADFNode] = []
    for line_index, line in enumerate(lines):
        content.extend(_inline_nodes(line, markdown=markdown))
        if line_index < len(lines) - 1:
            content.append({"type": "hardBreak"})
    return {"type": "paragraph", "content": content}


def _list_item_node(text: str) -> ADFNode:
    return {"type": "listItem", "content": [_paragraph_node(text, markdown=True)]}


def _code_block_node(text: str, language: Optional[str] = None) -> ADFNode:
    node: ADFNode = {
        "type": "codeBlock",
        "content": [{"type": "text", "text": text or ""}],
    }
    if language:
        node["attrs"] = {"language": language}
    return node


def _inline_nodes(text: str, markdown: bool = False, marks: Optional[Sequence[ADFNode]] = None) -> List[ADFNode]:
    if not markdown:
        return _text_node(text, marks)

    marks = list(marks or [])
    nodes: List[ADFNode] = []
    position = 0

    while position < len(text):
        match = _next_inline_match(text, position)
        if not match:
            nodes.extend(_text_node(text[position:], marks))
            break

        start, end, token_type, token_match = match
        if start > position:
            nodes.extend(_text_node(text[position:start], marks))

        if token_type == "code":
            nodes.extend(_text_node(token_match.group(1), [*marks, {"type": "code"}]))
        elif token_type == "link":
            href = token_match.group(2)
            nodes.extend(_inline_nodes(token_match.group(1), markdown=True, marks=[*marks, {"type": "link", "attrs": {"href": href}}]))
        elif token_type == "strong":
            inner = token_match.group(2)
            nodes.extend(_inline_nodes(inner, markdown=True, marks=[*marks, {"type": "strong"}]))
        elif token_type == "em":
            inner = token_match.group(1) or token_match.group(2) or ""
            nodes.extend(_inline_nodes(inner, markdown=True, marks=[*marks, {"type": "em"}]))

        position = end

    return nodes


def _next_inline_match(text: str, start: int) -> Optional[tuple[int, int, str, re.Match[str]]]:
    matches: List[tuple[int, int, str, re.Match[str]]] = []
    for token_type, pattern in (
        ("code", _CODE_RE),
        ("link", _LINK_RE),
        ("strong", _STRONG_RE),
        ("em", _EM_RE),
    ):
        match = pattern.search(text, start)
        if match:
            matches.append((match.start(), match.end(), token_type, match))

    if not matches:
        return None

    matches.sort(key=lambda item: (item[0], item[1]))
    return matches[0]


def _text_node(text: str, marks: Optional[Sequence[ADFNode]] = None) -> List[ADFNode]:
    if not text:
        return []

    node: ADFNode = {"type": "text", "text": text}
    if marks:
        node["marks"] = list(marks)
    return [node]
