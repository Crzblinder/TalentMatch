import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'

export interface RadarSkill {
  name: string
  userScore: number
  requiredScore: number
}

interface SkillRadarChartProps {
  skills: RadarSkill[]
  width?: number | `${number}%`
  height?: number | `${number}%`
}

export default function SkillRadarChart({ skills, width = '100%', height = 320 }: SkillRadarChartProps) {
  return (
    <ResponsiveContainer width={width} height={height}>
      <RadarChart data={skills}>
        <PolarGrid />
        <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
        <Radar
          name="我的技能"
          dataKey="userScore"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.35}
        />
        <Radar
          name="岗位要求"
          dataKey="requiredScore"
          stroke="#ef4444"
          fill="#ef4444"
          fillOpacity={0.25}
        />
        <Tooltip />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  )
}
