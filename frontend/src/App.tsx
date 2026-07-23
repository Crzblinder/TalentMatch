import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import OnboardingDialog from './components/OnboardingDialog'
import { ProfileProvider } from './components/ProfileContext'
import ConfigTests from './pages/ConfigTests'
import JobLibrary from './pages/JobLibrary'
import JobMatch from './pages/JobMatch'
import ProfileManager from './pages/ProfileManager'
import ResumeEditor from './pages/ResumeEditor'
import SkillDashboard from './pages/SkillDashboard'
import SkillGraph from './pages/SkillGraph'
import TrendAnalysis from './pages/TrendAnalysis'

// localStorage 键名，用于判断是否需要展示新手引导
const STORAGE_KEY_COMPLETED = 'onboarding_completed'
const STORAGE_KEY_PROFILE_ID = 'last_profile_id'

// 应用根组件：使用 shadcn/ui 重构的布局包裹现有路由，并管理新手引导弹窗
export default function App() {
  const [showOnboarding, setShowOnboarding] = useState(false)

  // 首次加载时检查是否已完成引导且没有已保存画像
  useEffect(() => {
    const completed = localStorage.getItem(STORAGE_KEY_COMPLETED) === 'true'
    const hasProfile = Boolean(localStorage.getItem(STORAGE_KEY_PROFILE_ID))
    if (!completed && !hasProfile) {
      setShowOnboarding(true)
    }
  }, [])

  return (
    <ProfileProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<SkillDashboard />} />
          <Route path="/match" element={<JobMatch />} />
          <Route path="/jobs" element={<JobLibrary />} />
          <Route path="/favorites" element={<Navigate to="/jobs?favorites=1" replace />} />
          <Route path="/skills" element={<SkillGraph />} />
          <Route path="/trends" element={<TrendAnalysis />} />
          <Route path="/resume-editor" element={<ResumeEditor />} />
          <Route path="/profiles" element={<ProfileManager />} />
          <Route path="/config-tests" element={<ConfigTests />} />
        </Routes>
        {showOnboarding && (
          <OnboardingDialog onComplete={() => setShowOnboarding(false)} />
        )}
      </Layout>
    </ProfileProvider>
  )
}
