from __future__ import annotations

from pathlib import Path
from typing import cast

from doc_forge.documents import (
    DocumentRecord,
    DocumentStatus,
    DocumentType,
)
from doc_forge.processing.document_structure import (
    DocumentPassageKind,
    UnsupportedStructuredDocumentType,
    parse_document_structure,
)

COMPLEX_TECHNICAL_MARKDOWN_PATH = (
    Path(__file__).parent / "fixtures" / "complex-technical-document.md"
)


def test_parse_document_structure_example_output_for_embedding_inputs() -> None:
    structure = parse_document_structure(
        _document(
            "# Guide\n"
            "\n"
            "Overview paragraph.\n"
            "\n"
            "## Install\n"
            "\n"
            "- uv sync\n"
            "- uv run poe verify\n"
            "\n"
            "## Configure\n"
            "\n"
            "| Key | Value |\n"
            "|---|---|\n"
            "| env | local |\n"
            "\n"
            "Done."
        )
    )

    assert [
        {
            "path": section.section_path,
            "heading": section.heading_title,
            "passages": [
                {
                    "kind": passage.kind,
                    "text": passage.text,
                    "lines": (passage.start_line, passage.end_line),
                }
                for passage in section.passages
            ],
        }
        for section in structure.sections
    ] == [
        {
            "path": ("Guide",),
            "heading": "Guide",
            "passages": [
                {
                    "kind": DocumentPassageKind.PARAGRAPH,
                    "text": "Overview paragraph.",
                    "lines": (3, 3),
                },
            ],
        },
        {
            "path": ("Guide", "Install"),
            "heading": "Install",
            "passages": [
                {
                    "kind": DocumentPassageKind.LIST,
                    "text": "- uv sync\n- uv run poe verify",
                    "lines": (7, 8),
                },
            ],
        },
        {
            "path": ("Guide", "Configure"),
            "heading": "Configure",
            "passages": [
                {
                    "kind": DocumentPassageKind.TABLE,
                    "text": "| Key | Value |\n|---|---|\n| env | local |",
                    "lines": (12, 14),
                },
                {
                    "kind": DocumentPassageKind.PARAGRAPH,
                    "text": "Done.",
                    "lines": (16, 16),
                },
            ],
        },
    ]
    assert [
        {
            "path": section.section_path,
            "kind": passage.kind,
            "text": passage.text,
            "lines": (passage.start_line, passage.end_line),
        }
        for section in structure.sections
        for passage in section.passages
    ] == [
        {
            "path": ("Guide",),
            "kind": DocumentPassageKind.PARAGRAPH,
            "text": "Overview paragraph.",
            "lines": (3, 3),
        },
        {
            "path": ("Guide", "Install"),
            "kind": DocumentPassageKind.LIST,
            "text": "- uv sync\n- uv run poe verify",
            "lines": (7, 8),
        },
        {
            "path": ("Guide", "Configure"),
            "kind": DocumentPassageKind.TABLE,
            "text": "| Key | Value |\n|---|---|\n| env | local |",
            "lines": (12, 14),
        },
        {
            "path": ("Guide", "Configure"),
            "kind": DocumentPassageKind.PARAGRAPH,
            "text": "Done.",
            "lines": (16, 16),
        },
    ]


def test_parse_document_structure_smoke_for_complex_technical_markdown() -> None:
    structure = parse_document_structure(
        _document(COMPLEX_TECHNICAL_MARKDOWN_PATH.read_text(encoding="utf-8"))
    )

    assert [section.section_path for section in structure.sections] == [
        ("DocForge Operator Guide",),
        ("DocForge Operator Guide", "Environment Setup"),
        ("DocForge Operator Guide", "Environment Setup", "Configuration Matrix"),
        ("DocForge Operator Guide", "Ingestion Workflow"),
        ("DocForge Operator Guide", "Ingestion Workflow", "Failure Modes"),
        ("DocForge Operator Guide", "Environment Setup"),
        ("DocForge Operator Guide", "Environment Setup", "Verification"),
    ]
    assert [section.heading_level for section in structure.sections] == [1, 2, 3, 2, 3, 2, 3]
    assert [(section.start_line, section.end_line) for section in structure.sections] == [
        (1, 4),
        (5, 20),
        (21, 29),
        (30, 37),
        (38, 45),
        (46, 49),
        (50, 54),
    ]
    assert [[passage.kind for passage in section.passages] for section in structure.sections] == [
        [DocumentPassageKind.PARAGRAPH],
        [
            DocumentPassageKind.PARAGRAPH,
            DocumentPassageKind.LIST,
            DocumentPassageKind.BLOCKQUOTE,
            DocumentPassageKind.CODE,
        ],
        [DocumentPassageKind.TABLE, DocumentPassageKind.PARAGRAPH],
        [DocumentPassageKind.PARAGRAPH, DocumentPassageKind.LIST],
        [DocumentPassageKind.PARAGRAPH, DocumentPassageKind.CODE],
        [DocumentPassageKind.PARAGRAPH],
        [DocumentPassageKind.PARAGRAPH, DocumentPassageKind.PARAGRAPH],
    ]
    assert structure.sections[0].passages[0].text == (
        "This guide explains how operators prepare DocForge for local ingestion. "
        "It intentionally includes inline **formatting**, `commands`, and a "
        "[reference link](https://example.test/docs) so the parser preserves the "
        "original Markdown passage text."
    )
    assert structure.sections[1].passages[1].text == (
        "1. Run `uv sync`.\n2. Copy `.env.example` to `.env`.\n3. Confirm PostgreSQL is reachable."
    )
    assert structure.sections[1].passages[2].text == (
        "> Keep local credentials out of committed documentation.\n"
        "> Rotate shared secrets after demos."
    )
    assert structure.sections[1].passages[3].text == (
        "```markdown\n"
        "# This heading is inside a fenced code block and must not create a section\n"
        "## Neither should this one\n"
        "```"
    )
    assert structure.sections[2].passages[0].text == (
        "| Setting | Default | Purpose |\n"
        "|---|---|---|\n"
        "| DOCFORGE_ENV | local | Selects local runtime defaults. |\n"
        "| DOCFORGE_LOG_LEVEL | info | Controls structured log verbosity. |"
    )
    assert structure.sections[4].passages[1].text == (
        "```text\nparse failed: unsupported document type\n```"
    )
    assert [section.section_id for section in structure.sections] == [
        "doc-1:section:0",
        "doc-1:section:1",
        "doc-1:section:2",
        "doc-1:section:3",
        "doc-1:section:4",
        "doc-1:section:5",
        "doc-1:section:6",
    ]
    assert [passage.passage_id for passage in structure.sections[6].passages] == [
        "doc-1:section:6:passage:0",
        "doc-1:section:6:passage:1",
    ]


def test_parse_document_structure_recovers_nested_sections_and_line_spans() -> None:
    structure = parse_document_structure(
        _document(
            "# Title\n"
            "\n"
            "Intro.\n"
            "\n"
            "## Details\n"
            "\n"
            "More.\n"
            "\n"
            "### Deep\n"
            "\n"
            "Deep text.\n"
            "\n"
            "## Sibling\n"
            "\n"
            "Text."
        )
    )

    assert [section.section_path for section in structure.sections] == [
        ("Title",),
        ("Title", "Details"),
        ("Title", "Details", "Deep"),
        ("Title", "Sibling"),
    ]
    assert [(section.start_line, section.end_line) for section in structure.sections] == [
        (1, 4),
        (5, 8),
        (9, 12),
        (13, 15),
    ]
    assert structure.sections[0].passages[0].text == "Intro."
    assert structure.sections[0].passages[0].start_line == 3
    assert structure.sections[0].passages[0].end_line == 3


def test_parse_document_structure_supports_text_immediately_after_headings() -> None:
    structure = parse_document_structure(
        _document(
            "# Title\n"
            "Intro paragraph without a blank line after the heading.\n"
            "## Details\n"
            "Details paragraph without a blank line after the heading.\n"
            "### Deep\n"
            "- first item\n"
            "- second item"
        )
    )

    assert [section.section_path for section in structure.sections] == [
        ("Title",),
        ("Title", "Details"),
        ("Title", "Details", "Deep"),
    ]
    assert [(section.start_line, section.end_line) for section in structure.sections] == [
        (1, 2),
        (3, 4),
        (5, 7),
    ]
    assert [
        (passage.kind, passage.text, passage.start_line, passage.end_line)
        for section in structure.sections
        for passage in section.passages
    ] == [
        (
            DocumentPassageKind.PARAGRAPH,
            "Intro paragraph without a blank line after the heading.",
            2,
            2,
        ),
        (
            DocumentPassageKind.PARAGRAPH,
            "Details paragraph without a blank line after the heading.",
            4,
            4,
        ),
        (DocumentPassageKind.LIST, "- first item\n- second item", 6, 7),
    ]


def test_parse_document_structure_preserves_duplicate_heading_names_without_invention() -> None:
    structure = parse_document_structure(
        _document("# Notes\n\nTop.\n\n## Notes\n\nFirst.\n\n## Notes\n\nSecond.")
    )

    assert [section.section_path for section in structure.sections] == [
        ("Notes",),
        ("Notes", "Notes"),
        ("Notes", "Notes"),
    ]
    assert len({section.section_id for section in structure.sections}) == 3


def test_parse_document_structure_ignores_headings_inside_fenced_code() -> None:
    structure = parse_document_structure(
        _document("# Real\n\n```markdown\n# Not a heading\n```\n\n## After\n\nText.")
    )

    assert [section.section_path for section in structure.sections] == [
        ("Real",),
        ("Real", "After"),
    ]
    assert structure.sections[0].passages[0].kind == DocumentPassageKind.CODE
    assert structure.sections[0].passages[0].text == "```markdown\n# Not a heading\n```"


def test_parse_document_structure_splits_common_markdown_passages() -> None:
    structure = parse_document_structure(
        _document(
            "# Passages\n"
            "\n"
            "Prose paragraph.\n"
            "\n"
            "- first item\n"
            "  continued item\n"
            "- second item\n"
            "\n"
            "> quoted\n"
            "> text\n"
            "\n"
            "```\n"
            "config=true\n"
            "```\n"
            "\n"
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |"
        )
    )

    section = structure.sections[0]

    assert [passage.kind for passage in section.passages] == [
        DocumentPassageKind.PARAGRAPH,
        DocumentPassageKind.LIST,
        DocumentPassageKind.BLOCKQUOTE,
        DocumentPassageKind.CODE,
        DocumentPassageKind.TABLE,
    ]
    assert section.passages[1].text == "- first item\n  continued item\n- second item"
    assert section.passages[4].text == "| A | B |\n|---|---|\n| 1 | 2 |"


def test_parse_document_structure_creates_one_passage_per_paragraph_without_crossing_sections() -> (
    None
):
    structure = parse_document_structure(
        _document("# One\n\none two\n\nthree four\n\nfive six\n\n## Two\n\nseven eight")
    )

    assert [
        (section.section_path, passage.text)
        for section in structure.sections
        for passage in section.passages
    ] == [
        (("One",), "one two"),
        (("One",), "three four"),
        (("One",), "five six"),
        (("One", "Two"), "seven eight"),
    ]


def test_parse_document_structure_can_create_multiple_passages_for_one_section() -> None:
    structure = parse_document_structure(
        _document("# Long Section\n\none two\n\nthree four\n\nfive six")
    )

    assert len(structure.sections) == 1
    assert structure.sections[0].section_path == ("Long Section",)
    assert [passage.section_id for passage in structure.sections[0].passages] == [
        "doc-1:section:0",
        "doc-1:section:0",
        "doc-1:section:0",
    ]
    assert [passage.text for passage in structure.sections[0].passages] == [
        "one two",
        "three four",
        "five six",
    ]
    assert [passage.kind for passage in structure.sections[0].passages] == [
        DocumentPassageKind.PARAGRAPH,
        DocumentPassageKind.PARAGRAPH,
        DocumentPassageKind.PARAGRAPH,
    ]


def test_parse_document_structure_keeps_single_paragraph_intact_as_one_passage() -> None:
    structure = parse_document_structure(_document("# One\n\none two three four five"))

    assert len(structure.sections[0].passages) == 1
    assert structure.sections[0].passages[0].text == "one two three four five"
    assert structure.sections[0].passages[0].token_count == 5


def test_parse_document_structure_preserves_original_markdown_passage_text() -> None:
    structure = parse_document_structure(
        _document("# Formatting\n\nUse **bold** text and `inline code`.")
    )

    assert structure.sections[0].passages[0].text == "Use **bold** text and `inline code`."


def test_parse_document_structure_supports_unheaded_documents() -> None:
    structure = parse_document_structure(_document("Preamble only.\n\nMore text."))

    assert len(structure.sections) == 1
    assert structure.sections[0].section_path == ()
    assert structure.sections[0].heading_title is None
    assert [passage.text for passage in structure.sections[0].passages] == [
        "Preamble only.",
        "More text.",
    ]


def test_parse_document_structure_rejects_non_markdown_records() -> None:
    document = DocumentRecord(
        document_id="doc-1",
        corpus_id="corpus-a",
        filename="notes.pdf",
        status=DocumentStatus.READY,
        document_type=cast(DocumentType, "pdf"),
        body="not markdown",
    )

    try:
        parse_document_structure(document)
    except UnsupportedStructuredDocumentType:
        return

    raise AssertionError("expected unsupported document type")


def _document(body: str) -> DocumentRecord:
    return DocumentRecord(
        document_id="doc-1",
        corpus_id="corpus-a",
        filename="notes.md",
        status=DocumentStatus.READY,
        document_type=DocumentType.MARKDOWN,
        body=body,
    )
