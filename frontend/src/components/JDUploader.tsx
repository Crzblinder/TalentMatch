import { useState, useRef } from 'react'
import { Upload, FileText, Sparkles, Search, AlertCircle } from 'lucide-react'
import { api } from '../api'
import type { JDUploadOut, ParsedJD, SearchOut } from '../types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'

interface JDUploaderProps {
  onParseComplete?: (result: JDUploadOut) => void
  initialJD?: ParsedJD
}

const SEARCH_INTENTS = [
  { value: 'company', label: '公司评价' },
  { value: 'interview', label: '面经' },
  { value: 'salary', label: '薪资' },
  { value: 'fresh_graduate', label: '校招' },
]

export default function JDUploader({ onParseComplete, initialJD }: JDUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<JDUploadOut | null>(null)
  const [preview, setPreview] = useState<string>('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResult, setSearchResult] = useState<SearchOut | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchIntent, setSearchIntent] = useState('company')

  const currentParsed = result?.parsed || initialJD

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    setError('')
    setPreview('')

    const ext = file.name.split('.').pop()?.toLowerCase()
    if (ext === 'pdf' || ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext || '')) {
      setPreview(URL.createObjectURL(file))
    }

    try {
      const res = await api.uploadJD(file)
      setResult(res)
      onParseComplete?.(res)
      if (res.parsed?.title) {
        setSearchQuery(`${res.parsed.title} ${res.parsed.company || ''}`)
      }
    } catch (err: any) {
      setError(err.message || '上传失败')
    } finally {
      setLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearchLoading(true)
    try {
      const res = await api.search({
        query: searchQuery.trim(),
        intent: searchIntent,
        top_n: 5,
        summarize: true,
      })
      setSearchResult(res)
    } catch (err: any) {
      setError(err.message || '搜索失败')
    } finally {
      setSearchLoading(false)
    }
  }

  const barriers = currentParsed?.barriers_for_fresh_graduates || []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          上传岗位描述（JD）
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          className="flex h-32 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-input bg-muted/30 transition-colors hover:border-primary/50 hover:bg-muted/50"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.webp,.gif"
            className="hidden"
            onChange={handleFileChange}
          />
          <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
          <div className="text-sm font-medium">点击上传 JD 文件</div>
          <div className="text-xs text-muted-foreground">支持 PDF、DOCX、图片（PNG/JPG）</div>
        </div>

        {preview && (
          <div className="rounded-lg border overflow-hidden">
            <img src={preview} alt="JD Preview" className="w-full max-h-64 object-contain" />
          </div>
        )}

        {loading && (
          <div className="space-y-3">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {currentParsed && !loading && (
          <div className="space-y-4 rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="font-medium">解析结果</span>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <div className="text-xs text-muted-foreground">岗位名称</div>
                <div className="font-medium">{currentParsed.title || '-'}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">公司名称</div>
                <div className="font-medium">{currentParsed.company || '-'}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">经验要求</div>
                <Badge variant="outline">{currentParsed.experience_level || '不限'}</Badge>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">学历要求</div>
                <Badge variant="outline">{currentParsed.education_level || '不限'}</Badge>
              </div>
            </div>

            {currentParsed.fresh_graduate_friendly !== undefined && (
              <div className="flex items-center gap-2">
                <Badge variant={currentParsed.fresh_graduate_friendly ? 'default' : 'destructive'}>
                  {currentParsed.fresh_graduate_friendly ? '应届生友好' : '应届生需谨慎'}
                </Badge>
              </div>
            )}

            <div>
              <div className="text-xs text-muted-foreground mb-2">核心技能要求</div>
              <div className="flex flex-wrap gap-2">
                {currentParsed.required_skills.length > 0 ? (
                  currentParsed.required_skills.map((skill, idx) => (
                    <Badge key={idx} variant="secondary" className="gap-1">
                      {skill}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">未识别到技能要求</span>
                )}
              </div>
            </div>

            {currentParsed.implicit_needs.length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">潜在需求</div>
                <ul className="list-inside list-disc text-sm text-muted-foreground">
                  {currentParsed.implicit_needs.map((need, idx) => (
                    <li key={idx}>{need}</li>
                  ))}
                </ul>
              </div>
            )}

            {barriers.length > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                <div className="flex items-center gap-2 text-sm font-medium text-amber-800 mb-2">
                  <AlertCircle className="h-4 w-4" />
                  应届生潜在门槛
                </div>
                <ul className="list-inside list-disc text-sm text-amber-700 space-y-1">
                  {barriers.map((barrier, idx) => (
                    <li key={idx}>{barrier}</li>
                  ))}
                </ul>
              </div>
            )}

            {result?.raw_text && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">原始文本</div>
                <pre className="max-h-32 overflow-auto rounded-md border bg-muted/50 p-3 text-xs">
                  {result.raw_text}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* 联网搜索 */}
        {currentParsed && (
          <div className="space-y-3 rounded-lg border p-4">
            <div className="flex items-center gap-2 font-medium">
              <Search className="h-4 w-4 text-primary" />
              联网求职情报
            </div>
            <div className="flex flex-wrap gap-2">
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="输入公司/岗位关键词搜索"
                className="h-11 min-w-0 flex-1"
              />
              <select
                value={searchIntent}
                onChange={(e) => setSearchIntent(e.target.value)}
                className="h-11 min-w-[6rem] rounded-md border bg-background px-2 text-sm"
              >
                {SEARCH_INTENTS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
              <Button
                onClick={handleSearch}
                disabled={searchLoading || !searchQuery.trim()}
                className="h-11"
              >
                {searchLoading ? '搜索中...' : '搜索'}
              </Button>
            </div>

            {searchResult && (
              <div className="space-y-3">
                {searchResult.summary && (
                  <div className="rounded-md bg-muted/50 p-3 text-sm">
                    {searchResult.summary}
                  </div>
                )}
                <div className="space-y-2">
                  {searchResult.results.map((item, idx) => (
                    <a
                      key={idx}
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-md border p-3 text-sm hover:bg-muted/50"
                    >
                      <div className="font-medium text-primary">{item.title}</div>
                      <div className="mt-1 text-xs text-muted-foreground line-clamp-2">
                        {item.snippet}
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
