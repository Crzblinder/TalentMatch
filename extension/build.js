#!/usr/bin/env node
/**
 * TalentMatch Edge 扩展打包脚本
 *
 * 1. 以扩展模式构建前端（相对路径资源 + hash 注入后端地址）
 * 2. 将产物复制到 extension/dist
 *
 * 用法：
 *   node extension/build.js
 *   node extension/build.js --skip-build   # 仅复制现有 frontend/dist
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

const ROOT = path.resolve(__dirname, '..')
const FRONTEND_DIR = path.join(ROOT, 'frontend')
const EXTENSION_DIR = __dirname
const SOURCE_DIST = path.join(FRONTEND_DIR, 'dist')
const TARGET_DIST = path.join(EXTENSION_DIR, 'dist')

function rimraf(dir) {
  if (!fs.existsSync(dir)) return
  fs.rmSync(dir, { recursive: true, force: true })
}

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true })
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name)
    const dstPath = path.join(dst, entry.name)
    if (entry.isDirectory()) {
      copyDir(srcPath, dstPath)
    } else {
      fs.copyFileSync(srcPath, dstPath)
    }
  }
}

function runFrontendBuild() {
  console.log('[build-extension] 正在构建前端（扩展模式）...')
  try {
    execSync('npm run build', {
      cwd: FRONTEND_DIR,
      stdio: 'inherit',
      env: { ...process.env, VITE_EXTENSION_BUILD: 'true' },
    })
  } catch (err) {
    console.error('[build-extension] 前端构建失败')
    if (err instanceof Error) console.error(err.message)
    process.exit(1)
  }
}

function main() {
  const skipBuild = process.argv.includes('--skip-build')

  if (!skipBuild) {
    runFrontendBuild()
  } else {
    console.log('[build-extension] 跳过前端构建，使用现有 frontend/dist')
  }

  if (!fs.existsSync(SOURCE_DIST)) {
    console.error(`[build-extension] 未找到前端构建产物：${SOURCE_DIST}`)
    process.exit(1)
  }

  console.log('[build-extension] 清理并复制产物到 extension/dist ...')
  rimraf(TARGET_DIST)
  copyDir(SOURCE_DIST, TARGET_DIST)

  console.log('[build-extension] 扩展打包完成')
  console.log(`[build-extension] 产物目录：${TARGET_DIST}`)
  console.log('[build-extension] 下一步：在 Edge 中打开 edge://extensions/，启用“开发人员模式”，点击“加载解压缩的扩展”，选择 extension 文件夹')
}

main()
