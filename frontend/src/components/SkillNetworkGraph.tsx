import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import * as d3 from 'd3'

// 节点数据模型，继承 D3 仿真节点以便保存坐标信息
export interface SkillNetworkNode extends d3.SimulationNodeDatum {
  id: string
  name: string
  r: number
  isCenter?: boolean
  definition?: string
}

// 边数据模型，source/target 初始为字符串，仿真过程中会解析为节点对象
export interface SkillNetworkLink extends d3.SimulationLinkDatum<SkillNetworkNode> {
  source: string | SkillNetworkNode
  target: string | SkillNetworkNode
  relation_type: string
  weight: number
}

// 通过 ref 暴露的缩放控制方法
export interface SkillNetworkGraphRef {
  zoomIn: () => void
  zoomOut: () => void
  resetZoom: () => void
}

interface SkillNetworkGraphProps {
  nodes: SkillNetworkNode[]
  links: SkillNetworkLink[]
  onNodeClick?: (node: SkillNetworkNode) => void
  width?: number
  height?: number
  relationColors?: Record<string, string>
}

const DEFAULT_RELATION_COLORS: Record<string, string> = {
  prerequisite: '#ef4444',
  similar: '#3b82f6',
  cooccurrence: '#22c55e',
}

function SkillNetworkGraph(
  {
    nodes,
    links,
    onNodeClick,
    width = 600,
    height = 480,
    relationColors = DEFAULT_RELATION_COLORS,
  }: SkillNetworkGraphProps,
  ref: React.Ref<SkillNetworkGraphRef>,
) {
  const svgRef = useRef<SVGSVGElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const zoomAttachedRef = useRef(false)

  // 向父组件暴露缩放控制接口
  useImperativeHandle(ref, () => ({
    zoomIn: () => {
      if (svgRef.current && zoomRef.current) {
        d3.select(svgRef.current)
          .transition()
          .duration(250)
          .call(zoomRef.current.scaleBy as any, 1.2)
      }
    },
    zoomOut: () => {
      if (svgRef.current && zoomRef.current) {
        d3.select(svgRef.current)
          .transition()
          .duration(250)
          .call(zoomRef.current.scaleBy as any, 0.8)
      }
    },
    resetZoom: () => {
      if (svgRef.current && zoomRef.current) {
        d3.select(svgRef.current)
          .transition()
          .duration(250)
          .call(zoomRef.current.transform as any, d3.zoomIdentity)
      }
    },
  }))

  useEffect(() => {
    if (!svgRef.current) return

    const svg = d3.select(svgRef.current)
    const tooltip = d3.select(tooltipRef.current)

    // 初始化或复用缩放根节点，避免重复渲染时丢失缩放状态
    let rootG = svg.select<SVGGElement>('g.zoom-root')
    if (rootG.empty()) {
      rootG = svg.append('g').attr('class', 'zoom-root')
    }

    // 配置缩放/平移行为，仅在首次渲染时绑定到 SVG，避免重复监听
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 4])
      .on('zoom', (event) => {
        rootG.attr('transform', event.transform.toString())
      })
    zoomRef.current = zoom
    if (!zoomAttachedRef.current) {
      svg.call(zoom as any)
      zoomAttachedRef.current = true
    }

    // 深拷贝节点与边，防止 D3 修改外部 props
    const simNodes: SkillNetworkNode[] = nodes.map((n) => ({ ...n }))
    const simLinks: SkillNetworkLink[] = links.map((l) => ({ ...l }))

    // 中心节点固定在画布中央
    simNodes.forEach((n) => {
      if (n.isCenter) {
        n.fx = width / 2
        n.fy = height / 2
      }
    })

    // 力导向模拟：连接力、电荷斥力、中心引力、碰撞检测
    const simulation = d3
      .forceSimulation<SkillNetworkNode>(simNodes)
      .force(
        'link',
        d3
          .forceLink<SkillNetworkNode, SkillNetworkLink>(simLinks)
          .id((d) => d.id)
          .distance(120),
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide<SkillNetworkNode>().radius((d) => d.r + 5))

    // 节点拖拽行为
    const drag = d3
      .drag<SVGGElement, SkillNetworkNode>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        if (!d.isCenter) {
          d.fx = undefined
          d.fy = undefined
        }
      })

    // 边的唯一标识
    const linkKey = (d: SkillNetworkLink) => {
      const s = typeof d.source === 'string' ? d.source : d.source.id
      const t = typeof d.target === 'string' ? d.target : d.target.id
      return `${s}-${t}`
    }

    // 绑定并绘制边
    const linkSel = rootG
      .selectAll<SVGLineElement, SkillNetworkLink>('line.skill-link')
      .data(simLinks, linkKey as any)

    linkSel.exit().remove()
    const linkEnter = linkSel
      .enter()
      .append('line')
      .attr('class', 'skill-link')
      .attr('stroke', (d) => relationColors[d.relation_type] || '#94a3b8')
      .attr('stroke-width', (d) => 1 + d.weight * 2)
      .attr('stroke-opacity', 0.7)

    const linkMerge = linkEnter.merge(linkSel as any)

    // 绑定并绘制节点
    const nodeSel = rootG
      .selectAll<SVGGElement, SkillNetworkNode>('g.skill-node')
      .data(simNodes, (d: any) => d.id)

    nodeSel.exit().remove()
    const nodeEnter = nodeSel
      .enter()
      .append('g')
      .attr('class', 'skill-node')
      .style('cursor', onNodeClick ? 'pointer' : 'default')
      .call(drag as any)
      .on('click', (event, d) => {
        event.stopPropagation()
        onNodeClick?.(d)
      })
      .on('mouseover', (_event, d) => {
        tooltip
          .style('opacity', '1')
          .html(
            `<div class="font-medium">${d.name}</div>` +
            (d.definition ? `<div class="mt-1 text-xs" style="color:#64748b">${d.definition}</div>` : ''),
          )
      })
      .on('mousemove', (event) => {
        tooltip.style('left', `${event.pageX + 12}px`).style('top', `${event.pageY + 12}px`)
      })
      .on('mouseout', () => {
        tooltip.style('opacity', '0')
      })

    nodeEnter
      .append('circle')
      .attr('r', (d) => d.r)
      .attr('fill', (d) => (d.isCenter ? '#3b82f6' : '#f1f5f9'))
      .attr('stroke', (d) => (d.isCenter ? '#2563eb' : '#cbd5e1'))
      .attr('stroke-width', 2)

    nodeEnter
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', (d) => (d.isCenter ? 13 : 11))
      .attr('font-weight', (d) => (d.isCenter ? 600 : 400))
      .attr('fill', (d) => (d.isCenter ? '#fff' : '#334155'))
      .attr('pointer-events', 'none')
      .text((d) => (d.name.length > 6 ? `${d.name.slice(0, 5)}...` : d.name))

    const nodeMerge = nodeEnter.merge(nodeSel as any)

    // 每帧同步 DOM 坐标
    simulation.on('tick', () => {
      linkMerge
        .attr('x1', (d) => (typeof d.source === 'object' ? d.source.x! : 0))
        .attr('y1', (d) => (typeof d.source === 'object' ? d.source.y! : 0))
        .attr('x2', (d) => (typeof d.target === 'object' ? d.target.x! : 0))
        .attr('y2', (d) => (typeof d.target === 'object' ? d.target.y! : 0))

      nodeMerge.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    return () => {
      simulation.stop()
    }
  }, [nodes, links, width, height, onNodeClick, relationColors])

  return (
    <div className="relative">
      <svg ref={svgRef} width={width} height={height} className="mx-auto block" />
      <div
        ref={tooltipRef}
        className="pointer-events-none fixed z-50 rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md opacity-0 transition-opacity"
      />
    </div>
  )
}

export default forwardRef(SkillNetworkGraph)
