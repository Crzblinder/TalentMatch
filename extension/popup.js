const DEFAULT_BACKEND = 'http://127.0.0.1:8000'

async function checkBackend(url) {
  try {
    const res = await fetch(`${url.replace(/\/$/, '')}/api/v1/jobs/health`, { signal: AbortSignal.timeout(3000) })
    return res.ok
  } catch {
    return false
  }
}

async function init() {
  const { backendUrl } = await chrome.storage.sync.get({ backendUrl: DEFAULT_BACKEND })
  const ok = await checkBackend(backendUrl)

  const dot = document.getElementById('status-dot')
  const text = document.getElementById('status-text')
  dot.classList.toggle('ok', ok)
  dot.classList.toggle('err', !ok)
  text.textContent = ok ? `已连接 ${backendUrl}` : `未连接 ${backendUrl}`

  document.getElementById('open-sidepanel').addEventListener('click', async () => {
    await chrome.sidePanel.open({ windowId: chrome.windows.WINDOW_ID_CURRENT })
    window.close()
  })

  document.getElementById('open-options').addEventListener('click', () => {
    chrome.runtime.openOptionsPage()
    window.close()
  })
}

init()
