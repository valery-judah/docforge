export function queryElements() {
  return {
    status: document.querySelector("#status"),
    corpusForm: document.querySelector("#corpus-form"),
    corpusId: document.querySelector("#corpus-id"),
    workspaceTabs: document.querySelectorAll(".workspace-tab"),
    workspacePanels: document.querySelectorAll(".workspace-panel"),
    uploadForm: document.querySelector("#upload-form"),
    uploadButton: document.querySelector("#upload-button"),
    file: document.querySelector("#file"),
    uploadFeedback: document.querySelector("#upload-feedback"),
    documentCount: document.querySelector("#document-count"),
    documentList: document.querySelector("#document-list"),
    questionForm: document.querySelector("#question-form"),
    questionInput: document.querySelector("#question-input"),
    askButton: document.querySelector("#ask-button"),
    retrievalStageBadge: document.querySelector("#retrieval-stage-badge"),
    retrievalPanel: document.querySelector("#retrieval-panel"),
    generationStageBadge: document.querySelector("#generation-stage-badge"),
    generationPanel: document.querySelector("#generation-panel"),
    resultStageBadge: document.querySelector("#result-stage-badge"),
    resultPanel: document.querySelector("#result-panel"),
    manageInspector: queryInspector(document.querySelector("#manage-inspector")),
    askInspector: queryInspector(document.querySelector("#ask-inspector")),
  }
}

function queryInspector(root) {
  return {
    root,
    documentTitle: root.querySelector('[data-role="document-title"]'),
    documentMeta: root.querySelector('[data-role="document-meta"]'),
    inspectorFocus: root.querySelector('[data-role="inspector-focus"]'),
    structure: root.querySelector('[data-role="structure"]'),
    rawBody: root.querySelector('[data-role="raw-body"]'),
    tabs: root.querySelectorAll(".tab"),
    views: root.querySelectorAll(".view"),
  }
}

export function syncCorpusInput(els, corpusId) {
  els.corpusId.value = corpusId
}

export function setStatus(els, message, kind = "ok") {
  els.status.textContent = message
  els.status.classList.toggle("error", kind === "error")
}

export function setUploadFeedback(els, message, kind = "ok") {
  els.uploadFeedback.textContent = message
  els.uploadFeedback.classList.toggle("error", kind === "error")
}

export function selectInspectorView(inspectorEls, viewName) {
  inspectorEls.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === viewName)
  })
  inspectorEls.views.forEach((view) => {
    view.classList.toggle("active", view.dataset.viewPanel === viewName)
  })
}

export function setActiveWorkspaceTab(els, activeTab) {
  els.workspaceTabs.forEach((tab) => {
    const isActive = tab.dataset.workspace === activeTab
    tab.classList.toggle("active", isActive)
    tab.setAttribute("aria-selected", isActive ? "true" : "false")
  })

  els.workspacePanels.forEach((panel) => {
    const isActive = panel.dataset.workspacePanel === activeTab
    panel.classList.toggle("active", isActive)
    panel.hidden = !isActive
  })
}
