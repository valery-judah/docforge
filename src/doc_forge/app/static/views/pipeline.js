import {
  countLabel,
  escapeHtml,
  generationStageLabel,
  generationStageStatus,
  stageLabel,
} from "../utils.js"

export function renderPipeline({ state, els, onSelectPassage }) {
  renderRetrievalPanel({ state, els, onSelectPassage })
  renderGenerationPanel({ state, els })
  renderResultPanel({ state, els, onSelectPassage })
}

function renderRetrievalPanel({ state, els, onSelectPassage }) {
  setStageBadge(
    els.retrievalStageBadge,
    stageLabel(state.retrieval.status),
    state.retrieval.status,
  )

  if (state.retrieval.status === "idle") {
    els.retrievalPanel.innerHTML =
      '<div class="empty">Run the pipeline to see ranked retrieval candidates.</div>'
    return
  }

  if (state.retrieval.status === "loading") {
    els.retrievalPanel.innerHTML = `
      <div class="callout loading">
        <strong>Searching corpus</strong>
        <p>Ranking the most relevant passages for the current question.</p>
      </div>
    `
    return
  }

  if (state.retrieval.status === "error") {
    els.retrievalPanel.innerHTML = `
      <div class="callout error">
        <strong>Retrieval failed</strong>
        <p>${escapeHtml(state.retrieval.error)}</p>
      </div>
    `
    return
  }

  if (state.retrieval.candidates.length === 0) {
    els.retrievalPanel.innerHTML = `
      <div class="callout quiet">
        <strong>No candidates returned</strong>
        <p>The corpus had no passages to rank for this question.</p>
      </div>
    `
    return
  }

  els.retrievalPanel.innerHTML = `
    <div class="stage-stack">
      <div class="stage-summary">
        <strong>${escapeHtml(state.retrieval.question)}</strong>
        <span>${countLabel(state.retrieval.candidates.length, "candidate")}</span>
      </div>
      <div class="passage-list">
        ${state.retrieval.candidates.map((passage) => renderEvidenceCard(state, passage, "candidate")).join("")}
      </div>
    </div>
  `

  bindPassageButtons(els.retrievalPanel, onSelectPassage)
}

function renderGenerationPanel({ state, els }) {
  const status = generationStageStatus(state.answer)
  setStageBadge(els.generationStageBadge, generationStageLabel(status), status)

  if (status === "idle") {
    els.generationPanel.innerHTML =
      '<div class="empty">Generated answer text will appear here after evidence is checked.</div>'
    return
  }

  if (status === "loading") {
    els.generationPanel.innerHTML = `
      <div class="callout loading">
        <strong>Generating answer</strong>
        <p>Calling the configured answer backend with the retrieved evidence.</p>
      </div>
    `
    return
  }

  if (status === "error") {
    els.generationPanel.innerHTML = `
      <div class="callout error">
        <strong>Answer backend unavailable</strong>
        <p>${escapeHtml(state.answer.error)}</p>
      </div>
    `
    return
  }

  const payload = state.answer.payload
  if (payload.state === "insufficient_evidence") {
    els.generationPanel.innerHTML = `
      <div class="callout quiet">
        <strong>Generation skipped</strong>
        <p>The answer backend was not called because no source passages cleared the support threshold.</p>
      </div>
    `
    return
  }

  els.generationPanel.innerHTML = `
    <div class="stage-stack">
      <div class="answer-state-card answered">
        <span class="state-pill answered">generated_answer</span>
        <p class="answer-text">${escapeHtml(payload.answer)}</p>
      </div>
    </div>
  `
}

function renderResultPanel({ state, els, onSelectPassage }) {
  setStageBadge(els.resultStageBadge, stageLabel(state.answer.status), state.answer.status)

  if (state.answer.status === "idle") {
    els.resultPanel.innerHTML =
      '<div class="empty">The final answer state will appear here after generation finishes.</div>'
    return
  }

  if (state.answer.status === "loading") {
    els.resultPanel.innerHTML = `
      <div class="callout loading">
        <strong>Waiting for answer service</strong>
        <p>Resolving the final answer state and supported source passages.</p>
      </div>
    `
    return
  }

  if (state.answer.status === "error") {
    els.resultPanel.innerHTML = `
      <div class="callout error">
        <strong>Answer backend unavailable</strong>
        <p>${escapeHtml(state.answer.error)}</p>
      </div>
    `
    return
  }

  const payload = state.answer.payload
  if (payload.state === "insufficient_evidence") {
    els.resultPanel.innerHTML = `
      <div class="stage-stack">
        <div class="answer-state-card insufficient">
          <span class="state-pill insufficient">insufficient_evidence</span>
          <p>The retrieval candidates did not clear the support threshold, so no answer was returned.</p>
        </div>
      </div>
    `
    return
  }

  els.resultPanel.innerHTML = `
    <div class="stage-stack">
      <div class="answer-state-card answered">
        <span class="state-pill answered">answered</span>
        <p>Answer returned with the supported source passages listed below.</p>
      </div>
      <div class="stage-summary">
        <strong>Supported source passages</strong>
        <span>${countLabel(payload.source_passages.length, "passage")}</span>
      </div>
      <div class="passage-list">
        ${payload.source_passages.map((passage) => renderEvidenceCard(state, passage, "source")).join("")}
      </div>
    </div>
  `

  bindPassageButtons(els.resultPanel, onSelectPassage)
}

function renderEvidenceCard(state, passage, kind) {
  const active = passage.passage_id === state.selectedPassageId ? " active" : ""
  const score = typeof passage.score === "number" ? passage.score.toFixed(3) : "n/a"

  if (kind === "candidate") {
    return `
      <button
        class="evidence-card evidence-card-candidate${active}"
        type="button"
        data-passage-id="${escapeHtml(passage.passage_id)}"
        data-kind="${escapeHtml(kind)}"
      >
        <div class="evidence-card-head">
          <span class="evidence-score">score ${escapeHtml(score)}</span>
          <span class="evidence-rank">rank ${escapeHtml(passage.rank)}</span>
        </div>
        <p class="evidence-text">${escapeHtml(passage.text)}</p>
      </button>
    `
  }

  const headingPath =
    passage.heading_path.length > 0 ? passage.heading_path.join(" / ") : "Document root"

  return `
    <button
      class="evidence-card${active}"
      type="button"
      data-passage-id="${escapeHtml(passage.passage_id)}"
      data-kind="${escapeHtml(kind)}"
    >
      <div class="evidence-card-head">
        <span class="evidence-kind">${escapeHtml(kind)}</span>
        <span class="evidence-rank">rank ${escapeHtml(passage.rank)}</span>
        <span class="evidence-score">score ${escapeHtml(score)}</span>
      </div>
      <strong>${escapeHtml(headingPath)}</strong>
      <span class="evidence-meta">
        ${escapeHtml(passage.document_id)} / lines ${escapeHtml(passage.start_line)}-${escapeHtml(
          passage.end_line,
        )}
      </span>
      <p>${escapeHtml(passage.text)}</p>
    </button>
  `
}

function bindPassageButtons(container, onSelectPassage) {
  container.querySelectorAll(".evidence-card").forEach((button) => {
    button.addEventListener("click", () => {
      onSelectPassage(button.dataset.passageId)
    })
  })
}

function setStageBadge(element, text, status) {
  element.textContent = text
  element.className = `stage-badge ${status}`
}
