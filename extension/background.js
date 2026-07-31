const DEFAULT_BACKEND = 'http://127.0.0.1:8000'

// Service Worker：点击工具栏图标时打开侧边栏
chrome.action.onClicked.addListener(async (tab) => {
  try {
    await chrome.sidePanel.open({ windowId: tab.windowId })
  } catch (err) {
    console.error('[TalentMatch] 打开侧边栏失败:', err)
  }
})

// 处理来自 popup / content script 的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  ;(async () => {
    try {
      if (message.action === 'getBackendUrl') {
        const { backendUrl } = await chrome.storage.sync.get({ backendUrl: DEFAULT_BACKEND })
        sendResponse({ backendUrl })
        return
      }

      if (message.action === 'getActiveProfile') {
        const { backendUrl } = await chrome.storage.sync.get({ backendUrl: DEFAULT_BACKEND })
        const profile = await fetchActiveProfile(backendUrl)
        sendResponse(profile)
        return
      }

      sendResponse({ error: '未知操作' })
    } catch (err) {
      console.error('[TalentMatch] 消息处理失败:', err)
      sendResponse({ error: err.message })
    }
  })()
  return true
})

async function fetchActiveProfile(backendUrl) {
  const apiBase = `${backendUrl.replace(/\/$/, '')}/api/v1`
  try {
    const res = await fetch(`${apiBase}/profiles/active/resume`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }
    const data = await res.json()
    if (data.code !== 0) {
      throw new Error(data.message || '获取简历失败')
    }
    return data.data
  } catch (err) {
    console.warn('[TalentMatch] 获取活跃简历失败:', err)
    return null
  }
}
