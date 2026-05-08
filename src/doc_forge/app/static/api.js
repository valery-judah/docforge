const RETRIEVAL_TOP_K = 5

function endpoint(state, path, params = {}) {
  const finalParams = {
    corpusId: state.corpusId,
    documentId: state.selectedDocumentId || "",
    ...params,
  }

  return path.replace(/\{(\w+)\}/g, (_, key) => encodeURIComponent(finalParams[key] || ""))
}

async function requestJson(state, path, options = {}, params = {}) {
  const response = await fetch(endpoint(state, path, params), options)
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const payload = await response.json()
      detail = payload.detail || detail
    } catch {
      // Keep the HTTP status text when the server did not return JSON.
    }

    const error = new Error(detail)
    error.status = response.status
    throw error
  }

  return response.json()
}

export function createApi(state) {
  return {
    listDocuments() {
      return requestJson(state, "/corpora/{corpusId}/documents")
    },
    getInspection(documentId) {
      return requestJson(
        state,
        "/corpora/{corpusId}/documents/{documentId}/inspection",
        {},
        { documentId },
      )
    },
    uploadDocument(formData) {
      return requestJson(state, "/corpora/{corpusId}/documents", {
        method: "POST",
        body: formData,
      })
    },
    retrieveCandidates(question) {
      return requestJson(state, "/corpora/{corpusId}/retrieval/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: RETRIEVAL_TOP_K }),
      })
    },
    answerQuestion(question) {
      return requestJson(state, "/corpora/{corpusId}/answers/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      })
    },
  }
}
