const state = {
  corpusId: window.localStorage.getItem("docforge.corpusId") || "default",
  documents: [],
  selectedDocumentId: null,
  inspection: null,
};

const els = {
  status: document.querySelector("#status"),
  corpusForm: document.querySelector("#corpus-form"),
  corpusId: document.querySelector("#corpus-id"),
  uploadForm: document.querySelector("#upload-form"),
  file: document.querySelector("#file"),
  documentCount: document.querySelector("#document-count"),
  documentList: document.querySelector("#document-list"),
  documentTitle: document.querySelector("#document-title"),
  documentMeta: document.querySelector("#document-meta"),
  structure: document.querySelector("#structure"),
  rawBody: document.querySelector("#raw-body"),
  tabs: document.querySelectorAll(".tab"),
  views: document.querySelectorAll(".view"),
};

els.corpusId.value = state.corpusId;

function setStatus(message, kind = "ok") {
  els.status.textContent = message;
  els.status.classList.toggle("error", kind === "error");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function endpoint(path) {
  return path
    .replace("{corpusId}", encodeURIComponent(state.corpusId))
    .replace("{documentId}", encodeURIComponent(state.selectedDocumentId || ""));
}

async function request(path, options = {}) {
  const response = await fetch(endpoint(path), options);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep the HTTP status text when the server did not return JSON.
    }
    throw new Error(detail);
  }
  return response.json();
}

async function loadDocuments() {
  state.corpusId = els.corpusId.value.trim() || "default";
  window.localStorage.setItem("docforge.corpusId", state.corpusId);
  setStatus("Loading");
  state.documents = await request("/corpora/{corpusId}/documents");
  renderDocumentList();
  if (state.documents.length === 0) {
    state.selectedDocumentId = null;
    state.inspection = null;
    renderInspection();
    setStatus("Ready");
    return;
  }
  const selectedExists = state.documents.some(
    (document) => document.document_id === state.selectedDocumentId,
  );
  state.selectedDocumentId = selectedExists
    ? state.selectedDocumentId
    : state.documents[0].document_id;
  await loadInspection(state.selectedDocumentId);
}

async function loadInspection(documentId) {
  state.selectedDocumentId = documentId;
  setStatus("Loading");
  state.inspection = await request(
    "/corpora/{corpusId}/documents/{documentId}/inspection",
  );
  renderDocumentList();
  renderInspection();
  setStatus("Ready");
}

async function uploadDocument(event) {
  event.preventDefault();
  const file = els.file.files[0];
  if (!file) {
    setStatus("Choose a Markdown file", "error");
    return;
  }

  state.corpusId = els.corpusId.value.trim() || "default";
  window.localStorage.setItem("docforge.corpusId", state.corpusId);
  const formData = new FormData();
  formData.append("file", file);

  setStatus("Uploading");
  const uploaded = await request("/corpora/{corpusId}/documents", {
    method: "POST",
    body: formData,
  });
  els.file.value = "";
  state.selectedDocumentId = uploaded.document_id;
  await loadDocuments();
}

function renderDocumentList() {
  els.documentCount.textContent = String(state.documents.length);
  if (state.documents.length === 0) {
    els.documentList.innerHTML = '<div class="empty">No documents</div>';
    return;
  }

  els.documentList.innerHTML = state.documents
    .map((document) => {
      const active = document.document_id === state.selectedDocumentId ? " active" : "";
      return `
        <button class="document-row${active}" type="button" data-id="${escapeHtml(
          document.document_id,
        )}">
          <strong>${escapeHtml(document.filename)}</strong>
          <span>${escapeHtml(document.document_id)}</span>
        </button>
      `;
    })
    .join("");

  els.documentList.querySelectorAll(".document-row").forEach((button) => {
    button.addEventListener("click", () => {
      loadInspection(button.dataset.id).catch(reportError);
    });
  });
}

function renderInspection() {
  const inspection = state.inspection;
  if (!inspection) {
    els.documentTitle.textContent = "No document selected";
    els.documentMeta.textContent = "";
    els.structure.innerHTML = '<div class="empty">No processed document</div>';
    els.rawBody.textContent = "";
    return;
  }

  els.documentTitle.textContent = inspection.filename;
  els.documentMeta.textContent = `${inspection.document_id} / ${inspection.document_type}`;
  els.rawBody.textContent = inspection.body;
  els.structure.innerHTML = inspection.sections.map(renderSection).join("");
}

function renderSection(section) {
  const title = section.heading_title || "Document root";
  const path = section.section_path.length > 0 ? section.section_path.join(" / ") : "root";
  const passages =
    section.passages.length > 0
      ? section.passages.map(renderPassage).join("")
      : '<div class="passage"><span class="muted">No passages</span></div>';

  return `
    <article class="section">
      <header class="section-title">
        <h3>${escapeHtml(title)}</h3>
        <div class="path">${escapeHtml(path)} / lines ${section.start_line}-${section.end_line}</div>
      </header>
      ${passages}
    </article>
  `;
}

function renderPassage(passage) {
  const embedding = passage.embedding
    ? `${passage.embedding.embedding_id} / dim ${passage.embedding.vector_dimensions}`
    : "missing embedding";

  return `
    <div class="passage">
      <div class="passage-meta">
        <span class="chip">${escapeHtml(passage.kind)}</span>
        <span class="chip">passage ${passage.ordinal}</span>
        <span class="chip">lines ${passage.start_line}-${passage.end_line}</span>
        <span class="chip">${escapeHtml(embedding)}</span>
      </div>
      <pre class="passage-text">${escapeHtml(passage.text)}</pre>
    </div>
  `;
}

function selectView(viewName) {
  els.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === viewName);
  });
  els.views.forEach((view) => {
    view.classList.toggle("active", view.id === `${viewName}-view`);
  });
}

function reportError(error) {
  setStatus(error.message || "Request failed", "error");
}

els.corpusForm.addEventListener("submit", (event) => {
  event.preventDefault();
  loadDocuments().catch(reportError);
});

els.uploadForm.addEventListener("submit", (event) => {
  uploadDocument(event).catch(reportError);
});

els.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    selectView(tab.dataset.view);
  });
});

loadDocuments().catch(reportError);
