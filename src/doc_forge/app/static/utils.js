export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
}

export function countLabel(count, label) {
  return `${count} ${count === 1 ? label : `${label}s`}`
}

export function stageLabel(status) {
  if (status === "ready") {
    return "Ready"
  }
  if (status === "loading") {
    return "Running"
  }
  if (status === "error") {
    return "Error"
  }
  return "Idle"
}

export function generationStageStatus(answer) {
  if (answer.status !== "ready") {
    return answer.status
  }

  return answer.payload?.state === "insufficient_evidence" ? "skipped" : "ready"
}

export function generationStageLabel(status) {
  if (status === "skipped") {
    return "Skipped"
  }

  return stageLabel(status)
}
