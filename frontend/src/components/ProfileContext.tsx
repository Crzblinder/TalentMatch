import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '@/api'
import type {
  ProfileCreateRequest,
  ProfileResponse,
  ProfileUpdateRequest,
  UserSkillProfile,
} from '@/types'
import { toast } from 'sonner'

interface ProfileContextValue {
  /** 后端标记的活跃画像（可能为 null） */
  activeProfile: UserSkillProfile | null
  /** 实际生效画像：活跃画像 > 列表第一个 */
  effectiveProfile: UserSkillProfile | null
  profiles: UserSkillProfile[]
  loading: boolean
  error: string
  refreshProfiles: () => Promise<void>
  setActiveProfile: (profileId: number) => Promise<void>
  createProfile: (payload: ProfileCreateRequest) => Promise<ProfileResponse>
  updateProfile: (profileId: number, payload: ProfileUpdateRequest) => Promise<ProfileResponse>
  deleteProfile: (profileId: number) => Promise<void>
}

const ProfileContext = createContext<ProfileContextValue | undefined>(undefined)

export function useProfile() {
  const ctx = useContext(ProfileContext)
  if (!ctx) {
    throw new Error('useProfile 必须在 ProfileProvider 内使用')
  }
  return ctx
}

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profiles, setProfiles] = useState<UserSkillProfile[]>([])
  const [activeProfile, setActiveProfileState] = useState<UserSkillProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [activeRes, listRes] = await Promise.all([
        api.getActiveProfile().catch(() => null),
        api.listProfiles().catch(() => ({ total: 0, items: [] })),
      ])
      setProfiles(listRes.items)
      setActiveProfileState(activeRes)
    } catch (e: any) {
      setError(e.message || '加载画像失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const effectiveProfile = useMemo(
    () => activeProfile || profiles[0] || null,
    [activeProfile, profiles]
  )

  const refreshProfiles = useCallback(async () => {
    await load()
  }, [load])

  const setActiveProfile = useCallback(
    async (profileId: number) => {
      await api.setActiveProfile(profileId)
      toast.success('已切换活跃画像')
      await refreshProfiles()
    },
    [refreshProfiles]
  )

  const createProfile = useCallback(
    async (payload: ProfileCreateRequest) => {
      const created = await api.createProfile(payload)
      await refreshProfiles()
      return created
    },
    [refreshProfiles]
  )

  const updateProfile = useCallback(
    async (profileId: number, payload: ProfileUpdateRequest) => {
      const updated = await api.updateProfile(profileId, payload)
      await refreshProfiles()
      return updated
    },
    [refreshProfiles]
  )

  const deleteProfile = useCallback(
    async (profileId: number) => {
      await api.deleteProfile(profileId)
      toast.success('画像已删除')
      await refreshProfiles()
    },
    [refreshProfiles]
  )

  const value = useMemo(
    () => ({
      activeProfile,
      effectiveProfile,
      profiles,
      loading,
      error,
      refreshProfiles,
      setActiveProfile,
      createProfile,
      updateProfile,
      deleteProfile,
    }),
    [activeProfile, effectiveProfile, profiles, loading, error, refreshProfiles, setActiveProfile, createProfile, updateProfile, deleteProfile]
  )

  return (
    <ProfileContext.Provider value={value}>
      {children}
    </ProfileContext.Provider>
  )
}
