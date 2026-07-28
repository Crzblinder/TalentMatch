import { useState } from 'react'
import { FileDown } from 'lucide-react'
import { jsPDF } from 'jspdf'
import html2canvas from 'html2canvas'

import { Button } from '@/components/ui/button'
import type { Job, MatchResult } from '@/types'
import { getSourceLabel } from '@/lib/utils'

interface ExportPDFButtonProps {
  /** 目标岗位信息 */
  job?: Job | null
  /** 匹配结果（对应后端 MatchResultOut） */
  match: MatchResult
  /** 按钮样式变体 */
  variant?: 'default' | 'outline' | 'secondary' | 'ghost'
}

/**
 * 根据分数返回对应颜色，用于总体匹配分数展示
 */
const scoreColor = (score: number) => {
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#3b82f6'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}

/**
 * 将 0-1 区间的分数转换为百分比字符串
 */
const formatPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '-'
  return `${(value * 100).toFixed(0)}%`
}

/**
 * 创建带样式的 DOM 元素
 */
const createEl = (
  tag: keyof HTMLElementTagNameMap,
  className = '',
  parent?: HTMLElement,
) => {
  const el = document.createElement(tag)
  if (className) el.className = className
  if (parent) parent.appendChild(el)
  return el
}

/**
 * 生成 TalentMatch 匹配报告 PDF
 * 方案：先在前端离屏渲染报告 DOM，再用 html2canvas 截图，最后拼入 jsPDF
 * 这样可以天然支持中文字体，无需额外引入字体文件
 */
export default function ExportPDFButton({
  job,
  match,
  variant = 'outline',
}: ExportPDFButtonProps) {
  const [loading, setLoading] = useState(false)

  const handleExport = async () => {
    if (loading) return
    setLoading(true)

    let container: HTMLDivElement | null = null

    try {
      // 1. 创建离屏容器，用于承载完整报告 DOM
      container = document.createElement('div')
      container.style.position = 'fixed'
      container.style.left = '-9999px'
      container.style.top = '0'
      container.style.width = '800px'
      container.style.fontFamily = "'Inter', 'Noto Sans SC', 'Microsoft YaHei', sans-serif"
      container.style.background = '#ffffff'
      container.style.color = '#111827'
      container.style.zIndex = '-1'
      document.body.appendChild(container)

      const overallScore = match.match_score * 100
      const now = new Date().toLocaleString('zh-CN')

      // 报告外层卡片
      const card = createEl('div', 'p-8 bg-white', container)

      // 标题区域
      const header = createEl('div', 'border-b border-gray-200 pb-4 mb-6', card)
      const title = createEl('h1', 'text-3xl font-bold text-gray-900 m-0 mb-2', header)
      title.textContent = 'TalentMatch 匹配报告'
      const time = createEl('p', 'text-sm text-gray-500 m-0', header)
      time.textContent = `生成时间：${now}`

      // 岗位信息区域
      const jobSection = createEl('div', 'mb-6', card)
      const jobTitle = createEl('h2', 'text-lg font-semibold text-gray-800 mb-3', jobSection)
      jobTitle.textContent = '岗位信息'

      const jobGrid = createEl('div', 'grid grid-cols-2 gap-4 text-sm', jobSection)
      const jobFields: Array<[string, string]> = [
        ['岗位名称', job?.title ?? '未知岗位'],
        ['公司名称', job?.company?.name ?? '-'],
        ['工作城市', job?.city ?? '-'],
        [
          '薪资范围',
          job
            ? `¥${job.salary_min.toLocaleString()} - ¥${job.salary_max.toLocaleString()}`
            : '-',
        ],
        ['经验要求', job?.experience_level ?? '-'],
        ['学历要求', job?.education_level ?? '-'],
        ['信息来源', job?.source ? getSourceLabel(job.source) : '-'],
      ]
      jobFields.forEach(([label, value]) => {
        const item = createEl('div', 'flex flex-col', jobGrid)
        const labelEl = createEl('span', 'text-gray-500 mb-1', item)
        labelEl.textContent = label
        const valueEl = createEl('span', 'font-medium text-gray-900', item)
        valueEl.textContent = value
      })

      // 总体匹配分数
      const scoreBox = createEl(
        'div',
        'flex items-center gap-6 p-6 rounded-xl bg-gray-50 mb-6',
        card,
      )
      const scoreNumber = createEl('div', 'text-6xl font-bold', scoreBox)
      scoreNumber.style.color = scoreColor(overallScore)
      scoreNumber.textContent = `${overallScore.toFixed(0)}%`
      const scoreLabelBox = createEl('div', 'flex flex-col', scoreBox)
      const scoreLabel = createEl('span', 'text-sm text-gray-500', scoreLabelBox)
      scoreLabel.textContent = '总体匹配分数'
      const scoreSub = createEl('span', 'text-xs text-gray-400 mt-1', scoreLabelBox)
      scoreSub.textContent = '基于技能、经验与学历综合评估'

      // 细项分数
      const detailGrid = createEl('div', 'grid grid-cols-3 gap-4 mb-6', card)
      const detailItems: Array<[string, string]> = [
        ['技能分数', formatPercent(match.skill_score)],
        ['经验匹配', formatPercent(match.experience_match)],
        ['学历匹配', formatPercent(match.education_match)],
      ]
      detailItems.forEach(([label, value]) => {
        const item = createEl('div', 'p-4 rounded-lg bg-gray-50 text-center', detailGrid)
        const valueEl = createEl('div', 'text-2xl font-bold text-gray-900 mb-1', item)
        valueEl.textContent = value
        const labelEl = createEl('div', 'text-sm text-gray-500', item)
        labelEl.textContent = label
      })

      // 技能列表区域
      const skillsSection = createEl('div', 'grid grid-cols-2 gap-6 mb-6', card)

      // 已匹配技能
      const matchedBox = createEl('div', '', skillsSection)
      const matchedTitle = createEl(
        'h3',
        'text-base font-semibold text-gray-800 mb-3',
        matchedBox,
      )
      matchedTitle.textContent = `已匹配技能（${match.matched_skills.length} 项）`
      const matchedTags = createEl('div', 'flex flex-wrap gap-2', matchedBox)
      if (match.matched_skills.length) {
        match.matched_skills.forEach((skill) => {
          const tag = createEl(
            'span',
            'inline-block px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800',
            matchedTags,
          )
          tag.textContent = skill
        })
      } else {
        const empty = createEl('span', 'text-sm text-gray-400', matchedTags)
        empty.textContent = '无'
      }

      // 缺失技能
      const missingBox = createEl('div', '', skillsSection)
      const missingTitle = createEl(
        'h3',
        'text-base font-semibold text-gray-800 mb-3',
        missingBox,
      )
      missingTitle.textContent = `缺失技能（${match.missing_skills.length} 项）`
      const missingTags = createEl('div', 'flex flex-wrap gap-2', missingBox)
      if (match.missing_skills.length) {
        match.missing_skills.forEach((skill) => {
          const tag = createEl(
            'span',
            'inline-block px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800',
            missingTags,
          )
          tag.textContent = skill
        })
      } else {
        const empty = createEl('span', 'text-sm text-gray-400', missingTags)
        empty.textContent = '无'
      }

      // 分析摘要
      const summaryBox = createEl('div', 'p-5 rounded-xl bg-gray-50', card)
      const summaryTitle = createEl('h3', 'text-base font-semibold text-gray-800 mb-2', summaryBox)
      summaryTitle.textContent = '分析摘要'
      const summaryText = createEl('p', 'text-sm text-gray-700 leading-relaxed m-0', summaryBox)
      summaryText.textContent = match.analysis_summary ?? '暂无分析摘要'

      // 2. 将 DOM 渲染为高清图片
      const canvas = await html2canvas(container, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false,
      })

      // 3. 使用 jsPDF 拼接单页或多页 PDF
      const pdf = new jsPDF({
        orientation: 'p',
        unit: 'mm',
        format: 'a4',
      })

      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      const margin = 10
      const contentWidth = pageWidth - margin * 2
      const contentHeight = pageHeight - margin * 2
      const scale = contentWidth / canvas.width
      const scaledHeight = canvas.height * scale

      if (scaledHeight <= contentHeight) {
        // 单页可放下，垂直居中
        const x = margin
        const y = margin + (contentHeight - scaledHeight) / 2
        pdf.addImage(canvas.toDataURL('image/png'), 'PNG', x, y, contentWidth, scaledHeight)
      } else {
        // 多页拆分：按 PDF 内容高度逐页截取
        let sourceY = 0
        let pageY = 0
        let isFirstPage = true

        while (pageY < scaledHeight) {
          if (!isFirstPage) {
            pdf.addPage()
          }
          isFirstPage = false

          const remainingSourceHeight = canvas.height - sourceY
          const sourcePageHeight = Math.min(remainingSourceHeight, contentHeight / scale)

          const pageCanvas = document.createElement('canvas')
          pageCanvas.width = canvas.width
          pageCanvas.height = Math.ceil(sourcePageHeight)

          const ctx = pageCanvas.getContext('2d')
          if (ctx) {
            ctx.drawImage(
              canvas,
              0,
              sourceY,
              canvas.width,
              sourcePageHeight,
              0,
              0,
              canvas.width,
              sourcePageHeight,
            )
            pdf.addImage(
              pageCanvas.toDataURL('image/png'),
              'PNG',
              margin,
              margin,
              contentWidth,
              pageCanvas.height * scale,
            )
          }

          sourceY += sourcePageHeight
          pageY += pageCanvas.height * scale
        }
      }

      // 4. 下载 PDF
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
      pdf.save(`talentmatch-report-${match.job_id}-${timestamp}.pdf`)
    } finally {
      setLoading(false)
      if (container && container.parentNode) {
        container.parentNode.removeChild(container)
      }
    }
  }

  return (
    <Button variant={variant} size="sm" onClick={handleExport} disabled={loading}>
      <FileDown className="mr-2 h-4 w-4" />
      {loading ? '生成中...' : '导出 PDF'}
    </Button>
  )
}
