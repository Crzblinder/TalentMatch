#!/usr/bin/env node
/**
 * 简单校验扩展目录结构是否完整
 */

const fs = require('fs')
const path = require('path')

const EXT_DIR = __dirname
const required = [
  'manifest.json',
  'background.js',
  'popup.html',
  'popup.js',
  'sidepanel.html',
  'sidepanel.js',
  'options.html',
  'options.js',
  'content.js',
  'content.css',
  'dist/index.html',
  'icons/icon16.png',
  'icons/icon32.png',
  'icons/icon48.png',
  'icons/icon128.png',
]

let failed = false
for (const f of required) {
  const p = path.join(EXT_DIR, f)
  if (!fs.existsSync(p)) {
    console.error(`[validate] 缺失文件：${f}`)
    failed = true
  }
}

const manifest = JSON.parse(fs.readFileSync(path.join(EXT_DIR, 'manifest.json'), 'utf8'))
if (manifest.manifest_version !== 3) {
  console.error('[validate] manifest_version 必须为 3')
  failed = true
}
if (!manifest.permissions?.includes('sidePanel')) {
  console.error('[validate] 缺少 sidePanel 权限')
  failed = true
}
if (!manifest.content_scripts || manifest.content_scripts.length === 0) {
  console.error('[validate] 缺少 content_scripts 配置')
  failed = true
}

if (failed) {
  console.error('[validate] 扩展校验失败')
  process.exit(1)
}
console.log('[validate] 扩展目录结构校验通过')
