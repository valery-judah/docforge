const STORAGE_KEY = "docforge.corpusId"

export function createInitialState() {
  return {
    corpusId: window.localStorage.getItem(STORAGE_KEY) || "default",
    activeWorkspaceTab: "ask",
    documents: [],
    selectedDocumentId: null,
    inspection: null,
    selectedPassageId: null,
    retrieval: createIdleRetrievalState(),
    answer: createIdleAnswerState(),
  }
}

export function createIdleRetrievalState() {
  return {
    status: "idle",
    question: "",
    candidates: [],
    error: "",
  }
}

export function createIdleAnswerState() {
  return {
    status: "idle",
    payload: null,
    error: "",
  }
}

export function resetPipelineState(state) {
  state.selectedPassageId = null
  state.retrieval = createIdleRetrievalState()
  state.answer = createIdleAnswerState()
}

export function persistCorpusId(corpusId) {
  window.localStorage.setItem(STORAGE_KEY, corpusId)
}

export function normalizeCorpusId(value) {
  return value.trim() || "default"
}
