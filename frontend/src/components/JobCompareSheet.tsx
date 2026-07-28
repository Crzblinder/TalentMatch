import type { ReactNode } from 'react'
import type { Job } from '../types'

// shadcn/ui 组件导入
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { ExternalLink } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn, getSourceLabel } from '@/lib/utils'

// 高亮背景色池：不同值使用不同背景色
const HIGHLIGHT_COLORS = [
  'bg-blue-50/80 dark:bg-blue-950/30',
  'bg-amber-50/80 dark:bg-amber-950/30',
  'bg-green-50/80 dark:bg-green-950/30',
]

interface JobCompareSheetProps {
  // 已选中的岗位列表，最多 3 个
  jobs: Job[]
  // 关闭回调
  onClose: () => void
  // 是否强制打开（受控）
  open?: boolean
}

// 计算单元格高亮类名：同一行中相同值共享颜色，不同值使用不同颜色
function getCellHighlight(values: string[], index: number): string {
  const unique = Array.from(new Set(values))
  if (unique.length <= 1) return ''
  const pos = unique.indexOf(values[index])
  return HIGHLIGHT_COLORS[pos % HIGHLIGHT_COLORS.length]
}

// 将薪资格式化为可读字符串
function formatSalary(job: Job): string {
  return `¥${job.salary_min.toLocaleString()}-${job.salary_max.toLocaleString()}`
}

// 将岗位描述截断为摘要
function formatDescription(job: Job): string {
  const text = job.description || ''
  if (text.length <= 120) return text
  return `${text.slice(0, 120)}...`
}

// 将技能数组标准化为可比较的字符串
function skillSetKey(skills: string[]): string {
  return JSON.stringify([...skills].sort())
}

export default function JobCompareSheet({ jobs, onClose, open }: JobCompareSheetProps) {
  // 最多取前 3 个岗位
  const compareJobs = jobs.slice(0, 3)

  // 构造每一行的原始值数组与渲染函数
  const rows: {
    label: string
    values: string[]
    render: (job: Job, index: number) => ReactNode
    align?: 'top' | 'middle'
  }[] = [
    {
      label: '岗位名称',
      values: compareJobs.map((j) => j.title),
      render: (j) => <span className="font-medium">{j.title}</span>,
    },
    {
      label: '公司名称',
      values: compareJobs.map((j) => j.company.name),
      render: (j) => j.company.name,
    },
    {
      label: '城市',
      values: compareJobs.map((j) => j.city),
      render: (j) => j.city,
    },
    {
      label: '薪资范围',
      values: compareJobs.map((j) => formatSalary(j)),
      render: (j) => formatSalary(j),
    },
    {
      label: '经验要求',
      values: compareJobs.map((j) => j.experience_level),
      render: (j) => j.experience_level,
    },
    {
      label: '学历要求',
      values: compareJobs.map((j) => j.education_level),
      render: (j) => j.education_level,
    },
    {
      label: '来源信息',
      values: compareJobs.map((j) => getSourceLabel(j.source || '')),
      render: (j) =>
        j.source ? (
          <div className="flex items-center gap-1">
            <Badge variant="outline">{getSourceLabel(j.source)}</Badge>
            {j.source_url && (
              <a
                href={j.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-muted-foreground hover:text-foreground"
                title="跳转到原始页面"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>
        ) : (
          '-'
        ),
    },
    {
      label: '技能要求',
      values: compareJobs.map((j) => skillSetKey(j.required_skills)),
      render: (j) => (
        <div className="flex flex-wrap gap-1">
          {j.required_skills.map((skill) => (
            <Badge key={skill} variant="secondary">
              {skill}
            </Badge>
          ))}
          {j.required_skills.length === 0 && (
            <span className="text-sm text-muted-foreground">无</span>
          )}
        </div>
      ),
      align: 'top',
    },
    {
      label: '岗位描述摘要',
      values: compareJobs.map((j) => j.description || ''),
      render: (j) => (
        <p className="max-w-[280px] whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
          {formatDescription(j)}
        </p>
      ),
      align: 'top',
    },
  ]

  return (
    <Sheet open={open ?? compareJobs.length > 0} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <SheetContent className="w-[95%] p-0 sm:max-w-5xl">
        <SheetHeader className="px-6 pt-6 text-left">
          <SheetTitle>岗位对比</SheetTitle>
          <SheetDescription>
            最多可同时对比 3 个岗位，不同值将以不同背景色高亮显示
          </SheetDescription>
        </SheetHeader>

        {/* 移动端横向滚动容器 */}
        <ScrollArea className="mt-6 h-[calc(100vh-120px)] w-full">
          <div className="overflow-x-auto px-6 pb-6">
            <Table className="min-w-[600px]">
              <TableHeader>
                <TableRow>
                  {/* 第一列固定，方便横向滚动时查看维度标签 */}
                  <TableHead className="sticky left-0 z-10 w-32 bg-background font-semibold">
                    对比项
                  </TableHead>
                  {compareJobs.map((job) => (
                    <TableHead key={job.id} className="min-w-[200px]">
                      {job.title}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow key={row.label}>
                    <TableCell
                      className={cn(
                        'sticky left-0 z-10 bg-background font-medium',
                        row.align === 'top' && 'align-top'
                      )}
                    >
                      {row.label}
                    </TableCell>
                    {compareJobs.map((job, index) => (
                      <TableCell
                        key={job.id}
                        className={cn(
                          'transition-colors',
                          getCellHighlight(row.values, index),
                          row.align === 'top' && 'align-top'
                        )}
                      >
                        {row.render(job, index)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
