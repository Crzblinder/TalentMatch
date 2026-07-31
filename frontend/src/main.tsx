import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, HashRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// 在 Edge 扩展的 chrome-extension:// 页面中使用 HashRouter，避免刷新/路径问题
interface ChromeRuntime {
  runtime?: { id?: string }
}
const chromeApi = (window as unknown as { chrome?: ChromeRuntime }).chrome
const isExtensionContext =
  typeof chromeApi !== 'undefined' &&
  typeof chromeApi.runtime !== 'undefined' &&
  !!chromeApi.runtime?.id

const Router = isExtensionContext ? HashRouter : BrowserRouter

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>,
)
