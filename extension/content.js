(() => {
  'use strict'

  const PANEL_ID = 'talentmatch-app-panel'
  let panel = null
  let badge = null
  let currentFields = []
  let currentMatches = []
  let backendUrl = 'http://127.0.0.1:8000'

  // 判断当前页面是否可能是网申页面
  function looksLikeApplicationPage() {
    const url = location.href.toLowerCase()
    const keywords = ['apply', 'application', 'jobs', 'careers', 'position', 'recruit', 'campus', 'join']
    const hasKeyword = keywords.some(k => url.includes(k))
    const hasForm = document.querySelectorAll('form input, form textarea, form select').length > 3
    return hasKeyword || hasForm
  }

  // 提取页面表单字段
  function extractFormFields() {
    const inputs = Array.from(document.querySelectorAll('input, textarea, select'))
    const fields = []
    let idCounter = 0

    inputs.forEach(el => {
      const type = el.type || el.tagName.toLowerCase()
      if (['submit', 'button', 'reset', 'hidden', 'image'].includes(type)) return
      if (el.disabled) return

      const fieldId = el.id || `tm_field_${idCounter++}`
      // 保存原始 id 供后续填充使用
      if (!el.id) el.id = fieldId

      const label = findLabelText(el)
      const field = {
        id: fieldId,
        tag: el.tagName.toLowerCase(),
        type,
        name: el.name || '',
        placeholder: el.placeholder || '',
        label,
        aria_label: el.getAttribute('aria-label') || '',
        required: el.required || false,
        selector: getUniqueSelector(el),
      }
      fields.push(field)
    })

    return fields
  }

  function findLabelText(el) {
    if (el.labels && el.labels.length > 0) return el.labels[0].innerText.trim()
    if (el.id) {
      const label = document.querySelector(`label[for="${el.id}"]`)
      if (label) return label.innerText.trim()
    }
    // 查找相邻文本或父节点文本
    let parent = el.parentElement
    for (let i = 0; i < 3 && parent; i++) {
      const text = parent.innerText?.trim().split('\n')[0]
      if (text && text.length < 100) return text
      parent = parent.parentElement
    }
    return ''
  }

  function getUniqueSelector(el) {
    if (el.id) return `#${el.id}`
    const tag = el.tagName.toLowerCase()
    const name = el.name ? `[name="${el.name}"]` : ''
    const type = el.type ? `[type="${el.type}"]` : ''
    return `${tag}${name}${type}`
  }

  // 与 background service worker 通信
  function sendMessage(message) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message))
          return
        }
        resolve(response)
      })
    })
  }

  async function fetchBackend(path, options = {}) {
    const url = `${backendUrl.replace(/\/$/, '')}/api/v1${path}`
    const res = await fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
      },
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`HTTP ${res.status}: ${text}`)
    }
    const data = await res.json()
    if (data.code !== 0) throw new Error(data.message || '请求失败')
    return data.data
  }

  // 创建浮动面板
  function createPanel() {
    if (panel) return panel

    panel = document.createElement('div')
    panel.id = PANEL_ID
    panel.innerHTML = `
      <div class="talentmatch-header">
        <div class="talentmatch-title">TalentMatch 网申助手</div>
        <div class="talentmatch-actions">
          <button id="tm-minimize" title="最小化">−</button>
          <button id="tm-close" title="关闭">×</button>
        </div>
      </div>
      <div class="talentmatch-body">
        <div class="talentmatch-tabs">
          <button class="talentmatch-tab active" data-tab="fill">自动填充</button>
          <button class="talentmatch-tab" data-tab="optimize">JD 优化</button>
          <button class="talentmatch-tab" data-tab="advice">求职建议</button>
        </div>
        <div class="talentmatch-tab-content active" id="tab-fill">
          <div class="talentmatch-status">
            <span class="dot" id="tm-status-dot"></span>
            <span id="tm-status-text">检测表单中…</span>
          </div>
          <button class="talentmatch-btn" id="tm-scan">重新识别表单</button>
          <button class="talentmatch-btn" id="tm-match" disabled>智能匹配简历</button>
          <button class="talentmatch-btn secondary" id="tm-fill" disabled>一键填入表单</button>
          <div id="tm-fields"></div>
        </div>
        <div class="talentmatch-tab-content" id="tab-optimize">
          <div class="talentmatch-section">
            <div class="talentmatch-section-title">上传岗位 JD</div>
            <input type="file" class="talentmatch-input" id="tm-jd-file" accept="image/*,.pdf,.docx,.doc,.txt" />
          </div>
          <div class="talentmatch-section">
            <div class="talentmatch-section-title">或粘贴 JD 文本</div>
            <textarea class="talentmatch-input" id="tm-jd-text" placeholder="粘贴岗位描述、任职要求…"></textarea>
          </div>
          <button class="talentmatch-btn" id="tm-optimize">智能优化简历</button>
          <div id="tm-optimize-result"></div>
        </div>
        <div class="talentmatch-tab-content" id="tab-advice">
          <div class="talentmatch-section">
            <input type="text" class="talentmatch-input" id="tm-advice-company" placeholder="公司（可选）" />
          </div>
          <div class="talentmatch-section">
            <input type="text" class="talentmatch-input" id="tm-advice-position" placeholder="岗位（可选）" />
          </div>
          <button class="talentmatch-btn" id="tm-advice-btn">搜索经验建议</button>
          <div id="tm-advice-result"></div>
        </div>
      </div>
    `
    document.body.appendChild(panel)
    setupPanelEvents()
    makeDraggable(panel.querySelector('.talentmatch-header'), panel)
    return panel
  }

  function setupPanelEvents() {
    panel.querySelector('#tm-close').addEventListener('click', () => {
      panel.style.display = 'none'
      showBadge()
    })
    panel.querySelector('#tm-minimize').addEventListener('click', () => {
      panel.style.display = 'none'
      showBadge()
    })

    panel.querySelectorAll('.talentmatch-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        panel.querySelectorAll('.talentmatch-tab').forEach(t => t.classList.remove('active'))
        panel.querySelectorAll('.talentmatch-tab-content').forEach(c => c.classList.remove('active'))
        tab.classList.add('active')
        panel.querySelector(`#tab-${tab.dataset.tab}`).classList.add('active')
      })
    })

    panel.querySelector('#tm-scan').addEventListener('click', () => {
      scanAndRenderFields()
    })

    panel.querySelector('#tm-match').addEventListener('click', () => {
      matchFieldsWithBackend()
    })

    panel.querySelector('#tm-fill').addEventListener('click', () => {
      fillFormFields()
    })

    panel.querySelector('#tm-optimize').addEventListener('click', () => {
      optimizeResume()
    })

    panel.querySelector('#tm-advice-btn').addEventListener('click', () => {
      searchAdvice()
    })
  }

  function makeDraggable(handle, target) {
    let isDragging = false
    let startX = 0
    let startY = 0
    let startLeft = 0
    let startTop = 0

    handle.addEventListener('mousedown', (e) => {
      isDragging = true
      startX = e.clientX
      startY = e.clientY
      const rect = target.getBoundingClientRect()
      startLeft = rect.left
      startTop = rect.top
      document.body.style.userSelect = 'none'
    })

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return
      const dx = e.clientX - startX
      const dy = e.clientY - startY
      target.style.left = `${Math.max(0, startLeft + dx)}px`
      target.style.top = `${Math.max(0, startTop + dy)}px`
      target.style.right = 'auto'
    })

    document.addEventListener('mouseup', () => {
      isDragging = false
      document.body.style.userSelect = ''
    })
  }

  function showBadge() {
    if (badge) {
      badge.style.display = 'flex'
      return
    }
    badge = document.createElement('button')
    badge.className = 'talentmatch-float-badge'
    badge.title = '打开 TalentMatch 网申助手'
    badge.textContent = 'T'
    badge.addEventListener('click', () => {
      panel.style.display = 'flex'
      badge.style.display = 'none'
    })
    document.body.appendChild(badge)
  }

  function updateStatus(ok, text) {
    const dot = panel.querySelector('#tm-status-dot')
    const label = panel.querySelector('#tm-status-text')
    dot.className = 'dot ' + (ok ? 'ok' : 'err')
    label.textContent = text
  }

  function scanAndRenderFields() {
    currentFields = extractFormFields()
    const container = panel.querySelector('#tm-fields')
    if (currentFields.length === 0) {
      container.innerHTML = '<div class="talentmatch-empty">未检测到可填写字段</div>'
      updateStatus(false, '未检测到表单字段')
      panel.querySelector('#tm-match').disabled = true
      return
    }

    container.innerHTML = `
      <div class="talentmatch-section">
        <div class="talentmatch-section-title">已识别 ${currentFields.length} 个字段</div>
        <div class="talentmatch-field-list">
          ${currentFields.map(f => `
            <div class="talentmatch-field-item" data-id="${f.id}">
              <div class="talentmatch-field-label">${escapeHtml(f.label || f.name || f.placeholder || '未命名字段')}</div>
              <div class="talentmatch-field-value">等待匹配…</div>
            </div>
          `).join('')}
        </div>
      </div>
    `
    updateStatus(true, `已识别 ${currentFields.length} 个字段`)
    panel.querySelector('#tm-match').disabled = false
    panel.querySelector('#tm-fill').disabled = true
  }

  async function matchFieldsWithBackend() {
    const matchBtn = panel.querySelector('#tm-match')
    matchBtn.disabled = true
    matchBtn.textContent = '正在智能匹配…'

    try {
      // 获取后端地址和简历数据
      const storage = await sendMessage({ action: 'getBackendUrl' })
      backendUrl = storage.backendUrl || backendUrl
      const profile = await sendMessage({ action: 'getActiveProfile' })

      if (!profile) {
        updateStatus(false, '未设置活跃简历画像，请先完善简历')
        return
      }

      const result = await fetchBackend('/applications/form-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: currentFields, profile, jd_text: null }),
      })

      currentMatches = result.matches || []
      renderMatches(result)
      updateStatus(true, `匹配完成：${currentMatches.length} 个字段`)
      panel.querySelector('#tm-fill').disabled = currentMatches.length === 0
    } catch (err) {
      console.error('[TalentMatch] 匹配失败:', err)
      updateStatus(false, '匹配失败：' + err.message)
    } finally {
      matchBtn.disabled = false
      matchBtn.textContent = '智能匹配简历'
    }
  }

  function renderMatches(result) {
    const container = panel.querySelector('#tm-fields')
    const matches = result.matches || []
    const unmatched = result.unmatched || []

    if (matches.length === 0 && unmatched.length === 0) {
      container.innerHTML = '<div class="talentmatch-empty">无匹配结果</div>'
      return
    }

    container.innerHTML = `
      <div class="talentmatch-section">
        <div class="talentmatch-section-title">匹配结果</div>
        <div class="talentmatch-field-list">
          ${matches.map(m => `
            <div class="talentmatch-field-item" data-id="${m.field_id}">
              <div class="talentmatch-field-label">${escapeHtml(getFieldLabel(m.field_id))}</div>
              <div class="talentmatch-field-value">${escapeHtml(m.value)}</div>
              <div class="talentmatch-field-meta">
                <span class="talentmatch-confidence ${m.confidence}">${m.confidence}</span>
                <span class="talentmatch-reason">${escapeHtml(m.reason)}</span>
              </div>
            </div>
          `).join('')}
          ${unmatched.map(u => `
            <div class="talentmatch-field-item" data-id="${u.field_id}">
              <div class="talentmatch-field-label">${escapeHtml(u.label || u.name || '未命名字段')}</div>
              <div class="talentmatch-field-value" style="color:#9ca3af">未匹配</div>
            </div>
          `).join('')}
        </div>
      </div>
    `
  }

  function getFieldLabel(fieldId) {
    const f = currentFields.find(x => x.id === fieldId)
    return f ? (f.label || f.name || f.placeholder || fieldId) : fieldId
  }

  function fillFormFields() {
    let filled = 0
    for (const m of currentMatches) {
      if (!m.value) continue
      const el = document.querySelector(`#${m.field_id}`)
      if (!el) continue
      setFieldValue(el, m.value)
      filled++
    }
    updateStatus(true, `已填入 ${filled} 个字段`)
  }

  function setFieldValue(el, value) {
    const tag = el.tagName.toLowerCase()
    const type = el.type

    if (tag === 'select') {
      // 尝试匹配选项文本或 value
      const options = Array.from(el.options)
      const match = options.find(o => o.text.includes(value) || o.value.includes(value))
      if (match) {
        el.value = match.value
      } else if (options.length > 0) {
        // 默认选择第一个非空选项
        const firstValid = options.find(o => o.value)
        if (firstValid) el.value = firstValid.value
      }
    } else if (type === 'radio') {
      const radios = document.querySelectorAll(`[name="${el.name}"]`)
      radios.forEach(r => {
        if (r.value.includes(value) || r.nextElementSibling?.innerText.includes(value)) {
          r.checked = true
        }
      })
    } else if (type === 'checkbox') {
      el.checked = ['true', '是', 'yes', '1'].includes(value.toLowerCase())
    } else if (type === 'date' && value) {
      el.value = normalizeDate(value)
    } else {
      el.value = value
    }

    // 触发 input/change 事件，让页面监听到
    el.dispatchEvent(new Event('input', { bubbles: true }))
    el.dispatchEvent(new Event('change', { bubbles: true }))
    el.dispatchEvent(new Event('blur', { bubbles: true }))
  }

  function normalizeDate(value) {
    const m = value.match(/(\d{4})[\.\-/年](\d{1,2})/)
    if (m) return `${m[1]}-${m[2].padStart(2, '0')}-01`
    return value
  }

  async function optimizeResume() {
    const fileInput = panel.querySelector('#tm-jd-file')
    const jdText = panel.querySelector('#tm-jd-text').value.trim()
    const resultEl = panel.querySelector('#tm-optimize-result')
    const btn = panel.querySelector('#tm-optimize')

    if (!fileInput.files[0] && !jdText) {
      resultEl.innerHTML = '<div class="talentmatch-empty">请先上传 JD 或粘贴文本</div>'
      return
    }

    btn.disabled = true
    btn.textContent = '正在优化…'
    resultEl.innerHTML = '<div class="talentmatch-loading">正在解析 JD 并优化简历…</div>'

    try {
      const storage = await sendMessage({ action: 'getBackendUrl' })
      backendUrl = storage.backendUrl || backendUrl
      const profile = await sendMessage({ action: 'getActiveProfile' })

      if (!profile) {
        resultEl.innerHTML = '<div class="talentmatch-empty">未设置活跃简历画像</div>'
        return
      }

      // 先解析 JD
      let jdResult
      if (fileInput.files[0]) {
        const formData = new FormData()
        formData.append('file', fileInput.files[0])
        if (jdText) formData.append('jd_text', jdText)
        jdResult = await fetchBackend('/applications/parse-jd', {
          method: 'POST',
          body: formData,
        })
      } else {
        jdResult = await fetchBackend('/jobs/parse', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ jd_text: jdText }),
        })
      }

      const fullJdText = jdResult.raw_text || jdText

      // 再优化简历
      const optimized = await fetchBackend('/applications/optimize-for-jd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_data: profile,
          jd_text: fullJdText,
        }),
      })

      renderOptimizeResult(optimized, resultEl)
    } catch (err) {
      console.error('[TalentMatch] 优化失败:', err)
      resultEl.innerHTML = `<div class="talentmatch-empty">优化失败：${escapeHtml(err.message)}</div>`
    } finally {
      btn.disabled = false
      btn.textContent = '智能优化简历'
    }
  }

  function renderOptimizeResult(data, container) {
    const projects = data.optimized_project_experience || []
    const works = data.optimized_work_experience || []
    const selfEval = data.optimized_self_evaluation || ''
    const notes = data.optimization_notes || ''

    container.innerHTML = `
      <div class="talentmatch-section">
        <div class="talentmatch-section-title">优化说明</div>
        <div class="talentmatch-summary">${escapeHtml(notes)}</div>
      </div>
      ${works.length ? `
        <div class="talentmatch-section">
          <div class="talentmatch-section-title">实习/工作经历</div>
          ${works.map(w => `
            <div class="talentmatch-field-item">
              <div class="talentmatch-field-label">${escapeHtml(w.company || '')} ${escapeHtml(w.position || '')}</div>
              <div class="talentmatch-field-value">${escapeHtml(w.description || '')}</div>
            </div>
          `).join('')}
        </div>
      ` : ''}
      ${projects.length ? `
        <div class="talentmatch-section">
          <div class="talentmatch-section-title">项目经历</div>
          ${projects.map(p => `
            <div class="talentmatch-field-item">
              <div class="talentmatch-field-label">${escapeHtml(p.name || '')} ${escapeHtml(p.role || '')}</div>
              <div class="talentmatch-field-value">${escapeHtml(p.description || '')}</div>
            </div>
          `).join('')}
        </div>
      ` : ''}
      ${selfEval ? `
        <div class="talentmatch-section">
          <div class="talentmatch-section-title">个人优势</div>
          <div class="talentmatch-field-item">
            <div class="talentmatch-field-value">${escapeHtml(selfEval)}</div>
          </div>
        </div>
      ` : ''}
    `
  }

  async function searchAdvice() {
    const company = panel.querySelector('#tm-advice-company').value.trim()
    const position = panel.querySelector('#tm-advice-position').value.trim()
    const container = panel.querySelector('#tm-advice-result')
    const btn = panel.querySelector('#tm-advice-btn')

    btn.disabled = true
    btn.textContent = '搜索中…'
    container.innerHTML = '<div class="talentmatch-loading">正在联网搜索经验建议…</div>'

    try {
      const storage = await sendMessage({ action: 'getBackendUrl' })
      backendUrl = storage.backendUrl || backendUrl
      const result = await fetchBackend('/applications/advice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company, position, scene: '网申' }),
      })

      renderAdviceResult(result, container)
    } catch (err) {
      console.error('[TalentMatch] 建议搜索失败:', err)
      container.innerHTML = `<div class="talentmatch-empty">搜索失败：${escapeHtml(err.message)}</div>`
    } finally {
      btn.disabled = false
      btn.textContent = '搜索经验建议'
    }
  }

  function renderAdviceResult(data, container) {
    const results = data.results || []
    const summary = data.summary || ''

    container.innerHTML = `
      ${summary ? `<div class="talentmatch-section"><div class="talentmatch-summary">${escapeHtml(summary)}</div></div>` : ''}
      <div class="talentmatch-section">
        <div class="talentmatch-section-title">相关经验</div>
        ${results.length ? `
          <ul class="talentmatch-advice-list">
            ${results.map(r => `
              <li>
                <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener">${escapeHtml(r.title)}</a>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">${escapeHtml(r.snippet || '')}</div>
              </li>
            `).join('')}
          </ul>
        ` : '<div class="talentmatch-empty">未找到相关建议</div>'}
      </div>
    `
  }

  function escapeHtml(text) {
    if (text == null) return ''
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }

  // 初始化
  async function init() {
    if (!looksLikeApplicationPage()) return

    const storage = await sendMessage({ action: 'getBackendUrl' })
    backendUrl = storage.backendUrl || backendUrl

    createPanel()
    scanAndRenderFields()
  }

  // 等待页面加载完成后再初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }
})()
