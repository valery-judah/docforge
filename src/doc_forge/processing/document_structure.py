from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from marko import Markdown, block
from marko.ext.gfm import elements, make_extension
from marko.parser import Parser
from marko.source import Source

from doc_forge.documents import DocumentRecord, DocumentType


class DocumentStructureError(Exception):
    pass


class UnsupportedStructuredDocumentType(DocumentStructureError):
    pass


class DocumentPassageKind(StrEnum):
    PARAGRAPH = "paragraph"
    LIST = "list"
    BLOCKQUOTE = "blockquote"
    CODE = "code"
    TABLE = "table"


@dataclass(frozen=True)
class DocumentPassage:
    passage_id: str
    document_id: str
    section_id: str
    ordinal: int
    kind: DocumentPassageKind
    text: str
    start_line: int
    end_line: int
    token_count: int


@dataclass(frozen=True)
class DocumentSection:
    section_id: str
    document_id: str
    ordinal: int
    heading_level: int | None
    heading_title: str | None
    section_path: tuple[str, ...]
    start_line: int
    end_line: int
    passages: tuple[DocumentPassage, ...]
    token_count: int


@dataclass(frozen=True)
class ParsedDocument:
    document_id: str
    corpus_id: str
    filename: str
    sections: tuple[DocumentSection, ...]


_TOKEN_RE = re.compile(r"\S+")


def parse_document_structure(document: DocumentRecord) -> ParsedDocument:
    """Parse a Markdown document record into sections and passages.

    Args:
        document: Markdown document record to parse.

    Returns:
        A storage-friendly parsed document. Each heading creates a section,
        and each non-heading Markdown block in a section creates one passage.

    Raises:
        UnsupportedStructuredDocumentType: If the document is not Markdown.
    """

    if document.document_type is not DocumentType.MARKDOWN:
        raise UnsupportedStructuredDocumentType

    nodes = _marko_nodes_for(document.body)
    section_drafts = _section_drafts_for(nodes=nodes, total_line_count=_line_count(document.body))
    sections = _sections_for(document=document, section_drafts=section_drafts)

    return ParsedDocument(
        document_id=document.document_id,
        corpus_id=document.corpus_id,
        filename=document.filename,
        sections=sections,
    )


@dataclass(frozen=True)
class _HeadingRecord:
    level: int
    title: str


@dataclass(frozen=True)
class _MarkoNode:
    node: Any
    source_text: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class _SectionDraft:
    ordinal: int
    heading_level: int | None
    heading_title: str | None
    section_path: tuple[str, ...]
    start_line: int
    end_line: int
    content_nodes: tuple[_MarkoNode, ...]


class _SourcePositionParser(Parser):
    def parse_source(self, source: Source) -> list[block.BlockElement]:
        element_list = self._build_block_element_list()
        ast: list[block.BlockElement] = []
        while not source.exhausted:
            for element_type in element_list:
                start_offset = source.pos
                if element_type.match(source):
                    result = element_type.parse(source)
                    end_offset = source.pos
                    if not hasattr(result, "priority"):
                        result = cast(Any, element_type)(result)
                    parsed_node = cast(block.BlockElement, result)
                    dynamic_node = cast(Any, parsed_node)
                    dynamic_node.source_start = start_offset
                    dynamic_node.source_end = end_offset
                    ast.append(parsed_node)
                    break
            else:
                break
        return ast


def _marko_nodes_for(text: str) -> tuple[_MarkoNode, ...]:
    parsed = Markdown(parser=_SourcePositionParser, extensions=[make_extension()]).parse(text)
    nodes: list[_MarkoNode] = []
    for node in parsed.children:
        if isinstance(node, block.BlankLine):
            continue

        start_offset = cast(int | None, getattr(node, "source_start", None))
        end_offset = cast(int | None, getattr(node, "source_end", None))
        if start_offset is None or end_offset is None:
            continue

        nodes.append(
            _MarkoNode(
                node=node,
                source_text=text[start_offset:end_offset].strip(),
                start_line=_line_at_offset(text=text, offset=start_offset),
                end_line=_end_line_for_span(text=text, start=start_offset, end=end_offset),
            )
        )

    return tuple(nodes)


def _section_drafts_for(
    *,
    nodes: tuple[_MarkoNode, ...],
    total_line_count: int,
) -> tuple[_SectionDraft, ...]:
    if not nodes:
        return (
            _SectionDraft(
                ordinal=0,
                heading_level=None,
                heading_title=None,
                section_path=(),
                start_line=1,
                end_line=1,
                content_nodes=(),
            ),
        )

    drafts: list[_SectionDraft] = []
    heading_stack: list[tuple[int, str]] = []
    current_heading_level: int | None = None
    current_heading_title: str | None = None
    current_section_path: tuple[str, ...] = ()
    current_start_line = 1
    current_content_nodes: list[_MarkoNode] = []

    for parsed_node in nodes:
        heading = _heading_for_node(parsed_node.node)
        if heading is not None:
            drafts.append(
                _SectionDraft(
                    ordinal=len(drafts),
                    heading_level=current_heading_level,
                    heading_title=current_heading_title,
                    section_path=current_section_path,
                    start_line=current_start_line,
                    end_line=max(current_start_line, parsed_node.start_line - 1),
                    content_nodes=tuple(current_content_nodes),
                )
            )

            heading_stack = [
                stack_item for stack_item in heading_stack if stack_item[0] < heading.level
            ]
            heading_stack.append((heading.level, heading.title))
            current_heading_level = heading.level
            current_heading_title = heading.title
            current_section_path = tuple(title for _, title in heading_stack)
            current_start_line = parsed_node.start_line
            current_content_nodes = []
        else:
            current_content_nodes.append(parsed_node)

    drafts.append(
        _SectionDraft(
            ordinal=len(drafts),
            heading_level=current_heading_level,
            heading_title=current_heading_title,
            section_path=current_section_path,
            start_line=current_start_line,
            end_line=total_line_count,
            content_nodes=tuple(current_content_nodes),
        )
    )

    return tuple(
        draft for draft in drafts if draft.heading_title is not None or draft.content_nodes
    )


def _sections_for(
    *,
    document: DocumentRecord,
    section_drafts: tuple[_SectionDraft, ...],
) -> tuple[DocumentSection, ...]:
    sections: list[DocumentSection] = []
    for draft in section_drafts:
        section_id = f"{document.document_id}:section:{len(sections)}"
        passages = _passages_for(
            document_id=document.document_id,
            section_id=section_id,
            nodes=draft.content_nodes,
        )
        sections.append(
            DocumentSection(
                section_id=section_id,
                document_id=document.document_id,
                ordinal=len(sections),
                heading_level=draft.heading_level,
                heading_title=draft.heading_title,
                section_path=draft.section_path,
                start_line=draft.start_line,
                end_line=draft.end_line,
                passages=passages,
                token_count=sum(passage.token_count for passage in passages),
            )
        )

    if sections:
        return tuple(sections)

    root_section_id = f"{document.document_id}:section:0"
    return (
        DocumentSection(
            section_id=root_section_id,
            document_id=document.document_id,
            ordinal=0,
            heading_level=None,
            heading_title=None,
            section_path=(),
            start_line=1,
            end_line=1,
            passages=(),
            token_count=0,
        ),
    )


def _passages_for(
    *,
    document_id: str,
    section_id: str,
    nodes: tuple[_MarkoNode, ...],
) -> tuple[DocumentPassage, ...]:
    passages: list[DocumentPassage] = []
    for node in nodes:
        text = node.source_text
        if text:
            passages.append(
                DocumentPassage(
                    passage_id=f"{section_id}:passage:{len(passages)}",
                    document_id=document_id,
                    section_id=section_id,
                    ordinal=len(passages),
                    kind=_passage_kind_for_node(node.node),
                    text=text,
                    start_line=node.start_line,
                    end_line=node.end_line,
                    token_count=_token_count(text),
                )
            )

    return tuple(passages)


def _heading_for_node(node: Any) -> _HeadingRecord | None:
    if not isinstance(node, block.Heading):
        return None

    return _HeadingRecord(level=node.level, title=_plain_text(node))


def _passage_kind_for_node(node: Any) -> DocumentPassageKind:
    if isinstance(node, (block.FencedCode, block.CodeBlock)):
        return DocumentPassageKind.CODE
    if isinstance(node, block.Quote):
        return DocumentPassageKind.BLOCKQUOTE
    if isinstance(node, block.List):
        return DocumentPassageKind.LIST
    if isinstance(node, elements.Table):
        return DocumentPassageKind.TABLE
    return DocumentPassageKind.PARAGRAPH


def _plain_text(node: Any) -> str:
    if isinstance(node, str):
        return node

    children = getattr(node, "children", None)
    if isinstance(children, str):
        return children
    if children is None:
        inline_body = getattr(node, "inline_body", "")
        return str(inline_body)

    return "".join(_plain_text(child) for child in children).strip()


def _line_count(text: str) -> int:
    return max(1, len(text.splitlines()))


def _line_at_offset(*, text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _end_line_for_span(*, text: str, start: int, end: int) -> int:
    if end <= start:
        return _line_at_offset(text=text, offset=start)
    return text.count("\n", 0, end - 1) + 1


def _token_count(text: str) -> int:
    return len(_TOKEN_RE.findall(text))
