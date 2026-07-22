import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * 合并 Tailwind CSS 类名工具函数
 * 先使用 clsx 处理条件类名，再通过 tailwind-merge 去重与合并冲突类名
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
