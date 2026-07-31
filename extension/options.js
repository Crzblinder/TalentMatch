const DEFAULT_BACKEND = 'http://127.0.0.1:8000'

async function init() {
  const input = document.getElementById('backend-url')
  const saveBtn = document.getElementById('save')
  const statusEl = document.getElementById('status')

  const saved = await chrome.storage.sync.get({ backendUrl: DEFAULT_BACKEND })
  input.value = saved.backendUrl

  saveBtn.addEventListener('click', async () => {
    let url = input.value.trim()
    if (!url) url = DEFAULT_BACKEND
    await chrome.storage.sync.set({ backendUrl: url })
    statusEl.textContent = '已保存'
    setTimeout(() => { statusEl.textContent = '' }, 2000)
  })
}

init()
