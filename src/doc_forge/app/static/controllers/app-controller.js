import {
  createIdleAnswerState,
  createIdleRetrievalState,
  normalizeCorpusId,
  persistCorpusId,
  resetPipelineState,
} from "../state.js"

export function createControllers({ state, els, api, render, setStatus, setUploadFeedback }) {
  function syncCorpusId() {
    const nextCorpusId = normalizeCorpusId(els.corpusId.value)
    const changed = nextCorpusId !== state.corpusId
    state.corpusId = nextCorpusId
    persistCorpusId(state.corpusId)
    return changed
  }

  function findPassage(passageId) {
    const answerPassages = state.answer.payload?.source_passages || []
    const allPassages = [...answerPassages, ...state.retrieval.candidates]
    return allPassages.find((passage) => passage.passage_id === passageId) || null
  }

  async function loadDocuments(options = {}) {
    const preservePipeline = options.preservePipeline ?? true
    const corpusChanged = syncCorpusId()
    setStatus("Loading corpus")
    setUploadFeedback("The active corpus is ready for uploads.")

    if (corpusChanged || !preservePipeline) {
      resetPipelineState(state)
      render()
    }

    state.documents = await api.listDocuments()
    render()

    if (state.documents.length === 0) {
      state.selectedDocumentId = null
      state.inspection = null
      state.selectedPassageId = null
      render()
      setStatus("Ready")
      return
    }

    const selectedExists = state.documents.some(
      (document) => document.document_id === state.selectedDocumentId,
    )
    const nextDocumentId = selectedExists ? state.selectedDocumentId : state.documents[0].document_id
    await loadInspection(nextDocumentId, { preservePassage: true, setStatusMessage: false })
    setStatus("Ready")
  }

  async function loadInspection(documentId, options = {}) {
    const preservePassage = options.preservePassage ?? false
    const setStatusMessage = options.setStatusMessage ?? true

    if (setStatusMessage) {
      setStatus("Loading inspection")
    }

    state.selectedDocumentId = documentId
    if (!preservePassage) {
      state.selectedPassageId = null
    }

    state.inspection = await api.getInspection(documentId)
    render()

    if (setStatusMessage) {
      setStatus("Ready")
    }
  }

  async function uploadDocument(event) {
    event.preventDefault()

    const file = els.file.files[0]
    if (!file) {
      setUploadFeedback("Choose a Markdown file before uploading.", "error")
      setStatus("Choose a Markdown file", "error")
      return
    }

    syncCorpusId()
    els.uploadButton.disabled = true
    setStatus("Uploading document")

    const formData = new FormData()
    formData.append("file", file)

    try {
      const uploaded = await api.uploadDocument(formData)
      els.file.value = ""
      state.selectedDocumentId = uploaded.document_id
      await loadDocuments({ preservePipeline: true })
      setUploadFeedback(`Uploaded ${uploaded.filename || file.name}.`)
      setStatus("Document uploaded")
    } catch (error) {
      setUploadFeedback(error.message || "Upload failed.", "error")
      throw error
    } finally {
      els.uploadButton.disabled = false
    }
  }

  async function runQuestionPipeline(event) {
    event.preventDefault()

    const question = els.questionInput.value.trim()
    if (!question) {
      state.retrieval = {
        ...createIdleRetrievalState(),
        status: "error",
        error: "Question must not be blank.",
      }
      state.answer = createIdleAnswerState()
      render()
      setStatus("Question must not be blank", "error")
      return
    }

    syncCorpusId()
    els.askButton.disabled = true
    state.selectedPassageId = null
    state.retrieval = {
      status: "loading",
      question,
      candidates: [],
      error: "",
    }
    state.answer = createIdleAnswerState()
    render()
    setStatus("Retrieving evidence")

    try {
      const retrievalPayload = await api.retrieveCandidates(question)
      state.retrieval = {
        status: "ready",
        question,
        candidates: retrievalPayload.candidates,
        error: "",
      }
      state.answer = {
        status: "loading",
        payload: null,
        error: "",
      }
      render()
      setStatus("Synthesizing answer")

      const answerPayload = await api.answerQuestion(question)
      state.answer = {
        status: "ready",
        payload: answerPayload,
        error: "",
      }

      if (answerPayload.state === "answered" && answerPayload.source_passages.length > 0) {
        await focusPassage(answerPayload.source_passages[0])
      } else {
        render()
      }

      setStatus("Ready")
    } catch (error) {
      if (state.retrieval.status === "loading") {
        state.retrieval.status = "error"
        state.retrieval.error = error.message || "Retrieval failed."
      } else {
        state.answer.status = "error"
        state.answer.error = error.message || "Answer synthesis failed."
      }
      render()
      setStatus(error.message || "Request failed", "error")
    } finally {
      els.askButton.disabled = false
    }
  }

  async function focusPassageById(passageId) {
    const passage = findPassage(passageId)
    if (!passage) {
      return
    }

    await focusPassage(passage)
  }

  async function focusPassage(passage) {
    state.selectedPassageId = passage.passage_id

    if (state.selectedDocumentId === passage.document_id && state.inspection) {
      render()
      return
    }

    await loadInspection(passage.document_id, {
      preservePassage: true,
      setStatusMessage: false,
    })
  }

  function reportError(error) {
    render()
    setStatus(error.message || "Request failed", "error")
  }

  function selectWorkspaceTab(tabName) {
    state.activeWorkspaceTab = tabName
    render()
  }

  return {
    loadDocuments,
    loadInspection,
    uploadDocument,
    runQuestionPipeline,
    focusPassageById,
    reportError,
    selectWorkspaceTab,
  }
}
