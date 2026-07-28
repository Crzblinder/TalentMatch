import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * 合并 Tailwind CSS 类名工具函数
 * 先使用 clsx 处理条件类名，再通过 tailwind-merge 去重与合并冲突类名
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 数据源名称映射：将内部 source key 转为易读的中文名称
 */
export const SOURCE_LABELS: Record<string, string> = {
  remoteok: 'RemoteOK',
  hn_jobs: 'Hacker News',
  python_jobs: 'Python.org',
  ruby_china_jobs: 'Ruby China',
  learnku_python_jobs: 'LearnKu Python',
  learnku_laravel_jobs: 'LearnKu Laravel',
  learnku_go_jobs: 'LearnKu Go',
  cnodejs: 'CNode 社区',
  oschina_news: '开源中国',
  segmentfault: '思否',
  infoq_cn: 'InfoQ 中文',
  cnblogs: '博客园',
  seed_jobs: '行业典型',
  boss_zhipin_python_beijing: 'Boss 直聘',
  boss_zhipin_python_shanghai: 'Boss 直聘',
  boss_zhipin_java_beijing: 'Boss 直聘',
  boss_zhipin_frontend_beijing: 'Boss 直聘',
  boss_zhipin_go_beijing: 'Boss 直聘',
  zhilian_python_beijing: '智联招聘',
  zhilian_java_beijing: '智联招聘',
  zhilian_frontend_beijing: '智联招聘',
  v2ex_jobs: 'V2EX',
}

export function getSourceLabel(source: string): string {
  if (!source) return ''
  return SOURCE_LABELS[source] ?? source.replace(/_/g, ' ')
}
