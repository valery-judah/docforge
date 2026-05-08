import { escapeHtml } from "../utils.js"

export function renderDocumentList({ state, els, onSelectDocument }) {
  els.documentCount.textContent = String(state.documents.length)

  if (state.documents.length === 0) {
    els.documentList.innerHTML = '<div class="empty">No documents in this corpus yet.</div>'
    return
  }

  els.documentList.innerHTML = state.documents
    .map((document) => {
      const active = document.document_id === state.selectedDocumentId ? " active" : ""
      return `
        <button class="document-row${active}" type="button" data-id="${escapeHtml(
          document.document_id,
        )}">
          <strong>${escapeHtml(document.filename)}</strong>
          <span>${escapeHtml(document.document_id)}</span>
        </button>
      `
    })
    .join("")

  els.documentList.querySelectorAll(".document-row").forEach((button) => {
    button.addEventListener("click", () => {
      onSelectDocument(button.dataset.id)
    })
  })
}
