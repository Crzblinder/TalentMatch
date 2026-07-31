// 在 iframe 中加载打包后的前端应用，并通过注入的 <script> 设置后端地址
const DEFAULT_BACKEND = 'http://127.0.0.1:8000'
const IFRAME_TIMEOUT_MS = 5000

async function loadApp() {
  const errorEl = document.getElementById('error')
  const iframeEl = document.getElementById('app')
  const retryBtn = document.getElementById('retry')
  const optionsBtn = document.getElementById('open-options')

  retryBtn.addEventListener('click', () => location.reload())
  optionsBtn.addEventListener('click', () => chrome.runtime.openOptionsPage())

  const { backendUrl } = await chrome.storage.sync.get({ backendUrl: DEFAULT_BACKEND })
  const apiBase = `${backendUrl.replace(/\/$/, '')}/api/v1`

  // 先探测后端是否可达
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), IFRAME_TIMEOUT_MS)
    const res = await fetch(`${apiBase}/jobs/health`, { signal: controller.signal })
    clearTimeout(timeout)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
  } catch (err) {
    console.warn('[TalentMatch] 后端探测失败:', err)
    errorEl.style.display = 'block'
    iframeEl.style.display = 'none'
    return
  }

  // 通过 URL 查询参数把后端地址传给前端，避免与 React HashRouter 冲突，
  // 同时保持 dist/index.html 的相对资源路径可直接在 chrome-extension:// 下解析
  try {
    const appUrl = new URL('dist/index.html', location.href)
    appUrl.searchParams.set('apiBase', apiBase)
    iframeEl.src = appUrl.toString()
  } catch (err) {
    console.error('[TalentMatch] 加载前端页面失败:', err)
    errorEl.style.display = 'block'
    iframeEl.style.display = 'none'
  }
}

loadApp()
