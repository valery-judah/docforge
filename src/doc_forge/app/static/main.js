import { createApi } from "./api.js"
import {
  queryElements,
  selectInspectorView,
  setActiveWorkspaceTab,
  setStatus,
  setUploadFeedback,
  syncCorpusInput,
} from "./dom.js"
import { createInitialState } from "./state.js"
import { createControllers } from "./controllers/app-controller.js"
import { renderDocumentList } from "./views/document-list.js"
import { renderInspection } from "./views/inspector.js"
import { renderPipeline } from "./views/pipeline.js"
import { renderWorkspaceTabs } from "./views/workspace-tabs.js"

const state = createInitialState()
const els = queryElements()

syncCorpusInput(els, state.corpusId)

let controllers

function render() {
  renderWorkspaceTabs({ state, els, setActiveWorkspaceTab })
  renderDocumentList({
    state,
    els,
    onSelectDocument: (documentId) => {
      controllers.loadInspection(documentId).catch(controllers.reportError)
    },
  })
  renderPipeline({
    state,
    els,
    onSelectPassage: (passageId) => {
      controllers.focusPassageById(passageId).catch(controllers.reportError)
    },
  })
  renderInspection({ state, inspectorEls: els.manageInspector })
  renderInspection({ state, inspectorEls: els.askInspector })
}

controllers = createControllers({
  state,
  els,
  api: createApi(state),
  render,
  setStatus: (message, kind) => setStatus(els, message, kind),
  setUploadFeedback: (message, kind) => setUploadFeedback(els, message, kind),
})

els.corpusForm.addEventListener("submit", (event) => {
  event.preventDefault()
  controllers.loadDocuments({ preservePipeline: false }).catch(controllers.reportError)
})

els.workspaceTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    controllers.selectWorkspaceTab(tab.dataset.workspace)
  })
})

els.uploadForm.addEventListener("submit", (event) => {
  controllers.uploadDocument(event).catch(controllers.reportError)
})

els.questionForm.addEventListener("submit", (event) => {
  controllers.runQuestionPipeline(event).catch(controllers.reportError)
})

els.questionInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey) {
    return
  }

  event.preventDefault()
  els.questionForm.requestSubmit()
})

for (const inspectorEls of [els.manageInspector, els.askInspector]) {
  inspectorEls.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      selectInspectorView(inspectorEls, tab.dataset.view)
    })
  })
}

render()
controllers.loadDocuments().catch(controllers.reportError)
