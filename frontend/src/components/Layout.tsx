import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Activity,
  Briefcase,
  Brain,
  FileText,
  Heart,
  LayoutDashboard,
  Menu,
  Target,
  TrendingUp,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Toaster } from '@/components/ui/sonner'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { cn } from '@/lib/utils'

// 侧边栏导航项配置，使用 Lucide 图标替代 emoji
// favorites 使用独立路径 /favorites，避免与 /jobs 高亮冲突
const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/match', icon: Target, label: '岗位匹配' },
  { to: '/resume-editor', icon: FileText, label: '简历优化' },
  { to: '/jobs', icon: Briefcase, label: '岗位库' },
  { to: '/favorites', icon: Heart, label: '我的收藏' },
  { to: '/skills', icon: Brain, label: '技能图谱' },
  { to: '/trends', icon: TrendingUp, label: '趋势分析' },
  { to: '/config-tests', icon: Activity, label: '配置检测' },
]

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const searchParams = new URLSearchParams(location.search)
  const isFavoritesView = location.pathname === '/jobs' && searchParams.get('favorites') === '1'

  const getIsActive = (to: string) => {
    if (to === '/jobs') {
      return location.pathname === '/jobs' && !isFavoritesView
    }
    if (to === '/favorites') {
      return isFavoritesView || location.pathname === '/favorites'
    }
    return location.pathname === to
  }

  const navContent = (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon
        const isActive = getIsActive(item.to)
        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={() => setMobileOpen(false)}
            className={cn(
              'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
              isActive
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
            )}
          >
            {isActive && (
              <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-primary-foreground/60" />
            )}
            <Icon
              className={cn(
                'h-4 w-4 shrink-0 transition-colors',
                isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground'
              )}
            />
            <span className="truncate">{item.label}</span>
          </Link>
        )
      })}
    </nav>
  )

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* 桌面端侧边栏 */}
      <aside className="hidden h-screen w-sidebar flex-col overflow-y-auto border-r bg-card px-4 py-6 md:flex">
        <h1 className="mb-8 px-3 text-lg font-bold tracking-tight text-foreground">
          TalentMatch
        </h1>
        {navContent}
      </aside>

      {/* 右侧区域：移动端纵向、桌面端横向共用同一份主内容 */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* 移动端顶部栏 */}
        <header className="flex items-center justify-between border-b bg-card px-4 py-3 md:hidden">
          <h1 className="text-base font-bold text-foreground">TalentMatch</h1>
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" aria-label="打开菜单">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-sidebar border-r bg-card p-4">
              <SheetHeader className="mb-6 text-left">
                <SheetTitle className="text-lg font-bold">TalentMatch</SheetTitle>
              </SheetHeader>
              {navContent}
            </SheetContent>
          </Sheet>
        </header>

        {/* 主内容区 */}
        <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
      </div>

      {/* 全局通知容器 */}
      <Toaster />
    </div>
  )
}
