import ExportPDFButton from './ExportPDFButton'
import { Badge } from './ui/badge'
import { ExternalLink } from 'lucide-react'
import type { Job, MatchResult } from '../types'
import { getSourceLabel } from '@/lib/utils'

interface MatchResultCardProps {
  matchResult: MatchResult
  jobTitle?: string
  job?: Job | null
}

const scoreColor = (score: number) => {
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#3b82f6'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}

export default function MatchResultCard({ matchResult, jobTitle, job }: MatchResultCardProps) {
  return (
    <>
      <div className="step-card">
        <div className="step-header">
          <div className="flex items-center gap-3">
            <span className="step-badge">匹配结果</span>
            <span>{jobTitle || '岗位匹配'}</span>
            {job?.source && (
              <span className="flex items-center gap-1 text-sm text-muted-foreground">
                <Badge variant="outline" className="text-xs">
                  {getSourceLabel(job.source)}
                </Badge>
                {job.source_url && (
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center hover:text-foreground"
                    title="跳转到原始页面"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </span>
            )}
          </div>
          {job && <ExportPDFButton job={job} match={matchResult} variant="outline" />}
        </div>
        <div className="step-body">
          <div className="prediction-main">
            <div className="match-score-big" style={{ color: scoreColor(matchResult.match_score * 100) }}>
              {(matchResult.match_score * 100).toFixed(0)}%
            </div>
            <div className="prediction-details">
              <div>
                <span className="step-label">匹配分数</span>
                <span className="step-val">{matchResult.match_score.toFixed(2)}</span>
              </div>
              <div>
                <span className="step-label">匹配技能</span>
                <span className="step-val">{matchResult.matched_skills.length} 项</span>
              </div>
              <div>
                <span className="step-label">缺失技能</span>
                <span className="step-val">{matchResult.missing_skills.length} 项</span>
              </div>
              <div>
                <span className="step-label">可迁移技能</span>
                <span className="step-val">{matchResult.transferable_skills.length} 项</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="step-card">
        <div className="step-header">
          <span className="step-badge">分析摘要</span>
          <span>AI 匹配洞察</span>
        </div>
        <div className="step-body">
          <p style={{ margin: 0, lineHeight: 1.7 }}>{matchResult.analysis_summary || '暂无分析摘要'}</p>
        </div>
      </div>

      <div className="skill-gap-grid">
        <div className="gov-section">
          <h4 className="gov-title gov-immediate">匹配技能</h4>
          <div className="tag-list">
            {matchResult.matched_skills.map((skill, i) => (
              <Badge key={i} variant="secondary" className="bg-green-100 text-green-800 hover:bg-green-100">
                {skill}
              </Badge>
            ))}
            {!matchResult.matched_skills.length && <span className="muted-text">无</span>}
          </div>
        </div>
        <div className="gov-section">
          <h4 className="gov-title gov-short">缺失技能</h4>
          <div className="tag-list">
            {matchResult.missing_skills.map((skill, i) => (
              <Badge key={i} variant="secondary" className="bg-red-100 text-red-800 hover:bg-red-100">
                {skill}
              </Badge>
            ))}
            {!matchResult.missing_skills.length && <span className="muted-text">无</span>}
          </div>
        </div>
        <div className="gov-section">
          <h4 className="gov-title gov-long">可迁移技能</h4>
          <div className="tag-list">
            {matchResult.transferable_skills.map((skill, i) => (
              <Badge key={i} variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100">
                {skill}
              </Badge>
            ))}
            {!matchResult.transferable_skills.length && <span className="muted-text">无</span>}
          </div>
        </div>
      </div>
    </>
  )
}
