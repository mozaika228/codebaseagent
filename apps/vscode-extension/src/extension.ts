import * as vscode from "vscode"

function getConfig() {
  const cfg = vscode.workspace.getConfiguration("codebaseAgent")
  return {
    apiBase: cfg.get<string>("apiBase", "http://localhost:8000"),
    projectId: cfg.get<string>("projectId", "")
  }
}

async function post<T>(apiBase: string, path: string, body: unknown): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  })
  if (!res.ok) {
    throw new Error(await res.text())
  }
  return res.json() as Promise<T>
}

async function explainSelection() {
  const editor = vscode.window.activeTextEditor
  if (!editor) return
  const selection = editor.selection
  const text = editor.document.getText(selection)
  if (!text.trim()) {
    vscode.window.showWarningMessage("Select code to explain")
    return
  }

  const { apiBase, projectId } = getConfig()
  if (!projectId) {
    vscode.window.showWarningMessage("Configure codebaseAgent.projectId in settings")
    return
  }

  const payload = {
    project_id: projectId,
    message: `Explain this block:\n\n${text}`
  }
  const data = await post<{ answer?: string }>(apiBase, "/chat", payload)
  vscode.window.showInformationMessage(data.answer || "No response")
}

async function refactorSelection() {
  const editor = vscode.window.activeTextEditor
  if (!editor) return
  const selection = editor.selection
  const text = editor.document.getText(selection)
  if (!text.trim()) {
    vscode.window.showWarningMessage("Select a function to refactor")
    return
  }

  const { apiBase, projectId } = getConfig()
  if (!projectId) {
    vscode.window.showWarningMessage("Configure codebaseAgent.projectId in settings")
    return
  }

  const payload = {
    project_id: projectId,
    type: "refactor_pipeline",
    payload: { repo_id: projectId, hint: text }
  }
  const data = await post<{ task_id: number }>(apiBase, "/tasks/enqueue", payload)
  vscode.window.showInformationMessage(`Task queued: ${data.task_id}`)
}

export function activate(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand("codebaseAgent.explainBlock", explainSelection),
    vscode.commands.registerCommand("codebaseAgent.refactorFunction", refactorSelection)
  )
}

export function deactivate() {}
