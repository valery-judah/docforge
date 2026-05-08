import { countLabel, escapeHtml } from "../utils.js"

export function renderInspection({ state, inspectorEls }) {
  const inspection = state.inspection
  if (!inspection) {
    inspectorEls.documentTitle.textContent = "No document selected"
    inspectorEls.documentMeta.textContent = ""
    inspectorEls.inspectorFocus.textContent = "Browse a document or select evidence."
    inspectorEls.inspectorFocus.className = "focus-chip muted"
    inspectorEls.structure.innerHTML =
      '<div class="empty">Select a document to inspect its structure.</div>'
    inspectorEls.rawBody.textContent = ""
    return
  }

  inspectorEls.documentTitle.textContent = inspection.filename
  inspectorEls.documentMeta.textContent = `${inspection.document_id} / ${inspection.document_type}`
  inspectorEls.rawBody.textContent = inspection.body

  const selectedPassage = findInspectionPassage(inspection, state.selectedPassageId)
  if (selectedPassage) {
    inspectorEls.inspectorFocus.textContent =
      `Focused on lines ${selectedPassage.start_line}-${selectedPassage.end_line}`
    inspectorEls.inspectorFocus.className = "focus-chip active"
  } else {
    inspectorEls.inspectorFocus.textContent = "Browsing document structure"
    inspectorEls.inspectorFocus.className = "focus-chip muted"
  }

  inspectorEls.structure.innerHTML = inspection.sections
    .map((section) => renderSection(state, section))
    .join("")
}

function findInspectionPassage(inspection, passageId) {
  if (!passageId) {
    return null
  }

  for (const section of inspection.sections) {
    for (const passage of section.passages) {
      if (passage.passage_id === passageId) {
        return passage
      }
    }
  }

  return null
}

function renderSection(state, section) {
  const title = section.heading_title || "Document root"
  const path = section.section_path.length > 0 ? section.section_path.join(" / ") : "root"
  const embeddingSummary = sectionEmbeddingSummary(section.passages)
  const passages =
    section.passages.length > 0
      ? section.passages.map((passage) => renderPassage(state, passage)).join("")
      : '<div class="passage"><span class="muted">No passages</span></div>'

  return `
    <article class="section">
      <header class="section-title">
        <h3>${escapeHtml(title)}</h3>
        <div class="path">${escapeHtml(path)} / lines ${section.start_line}-${section.end_line}</div>
        <div class="embedding-summary">${escapeHtml(embeddingSummary)}</div>
      </header>
      ${passages}
    </article>
  `
}

function sectionEmbeddingSummary(passages) {
  if (passages.length === 0) {
    return "No passage embeddings in this section"
  }

  const embeddedPassages = passages.filter((passage) => passage.embedding)
  if (embeddedPassages.length === 0) {
    return `${countLabel(passages.length, "passage")} / no embeddings`
  }

  const dimensions = [
    ...new Set(
      embeddedPassages.map((passage) => passage.embedding.vector_dimensions),
    ),
  ].sort((left, right) => left - right)
  const dimensionText =
    dimensions.length === 1 ? `dim ${dimensions[0]}` : `dims ${dimensions.join(", ")}`

  return `${countLabel(passages.length, "passage")} / ${countLabel(
    embeddedPassages.length,
    "vector",
  )} / ${dimensionText}`
}

function renderPassage(state, passage) {
  const embedding = passage.embedding
    ? `${passage.embedding.embedding_id} / dim ${passage.embedding.vector_dimensions}`
    : "missing embedding"
  const active = passage.passage_id === state.selectedPassageId ? " active" : ""

  return `
    <div class="passage${active}">
      <div class="passage-meta">
        <span class="chip">${escapeHtml(passage.kind)}</span>
        <span class="chip">passage ${passage.ordinal}</span>
        <span class="chip">lines ${passage.start_line}-${passage.end_line}</span>
        <span class="chip">${escapeHtml(embedding)}</span>
      </div>
      <pre class="passage-text">${escapeHtml(passage.text)}</pre>
    </div>
  `
}
