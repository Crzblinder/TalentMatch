import type { Job } from '../types'
import { ExternalLink } from 'lucide-react'
import { getSourceLabel } from '@/lib/utils'

interface JobCardProps {
  job: Job
  onClick?: (job: Job) => void
  onMatchClick?: (job: Job) => void
}

export default function JobCard({ job, onClick, onMatchClick }: JobCardProps) {
  const handleClick = () => {
    onClick?.(job)
  }

  const handleMatchClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation()
    onMatchClick?.(job)
  }

  return (
    <tr className="clickable-row" onClick={handleClick}>
      <td>{job.title}</td>
      <td>{job.company.name}</td>
      <td>{job.city}</td>
      <td>¥{job.salary_min.toLocaleString()}-{job.salary_max.toLocaleString()}</td>
      <td>{job.experience_level}</td>
      <td>{job.education_level}</td>
      <td>
        <div className="tag-list">
          {job.required_skills.slice(0, 3).map((skill, i) => (
            <span key={i} className="tag-chip">{skill}</span>
          ))}
          {job.required_skills.length > 3 && (
            <span className="tag-chip">+{job.required_skills.length - 3}</span>
          )}
        </div>
      </td>
      <td>
        {job.source ? (
          <span className="inline-flex items-center gap-1">
            {getSourceLabel(job.source)}
            {job.source_url && (
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center"
                onClick={(e) => e.stopPropagation()}
                title="跳转到原始页面"
              >
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </span>
        ) : (
          '-'
        )}
      </td>
      {onMatchClick && (
        <td>
          <button
            className="btn btn-sm btn-outline"
            onClick={handleMatchClick}
          >
            匹配
          </button>
        </td>
      )}
    </tr>
  )
}
