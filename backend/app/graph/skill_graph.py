import logging
from typing import Any

from sqlalchemy.orm import Session

try:
    import networkx as nx
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "NetworkX is required for skill_graph. "
        "Install it with: pip install networkx"
    ) from exc

from app.models import Skill, SkillRelation

logger = logging.getLogger(__name__)

# 模块级技能图谱缓存：以 relation_types 元组为 key
_graph_cache: dict[tuple[str, ...] | None, nx.MultiDiGraph] = {}


def get_cached_graph(
    session: Session,
    relation_types: list[str] | None = None,
) -> nx.MultiDiGraph:
    """获取缓存的技能图谱；未命中时从数据库构建并缓存。"""
    # 将关系类型列表排序后转为元组，保证 key 稳定且可哈希
    if relation_types is None:
        cache_key: tuple[str, ...] | None = None
    else:
        cache_key = tuple(sorted(relation_types))

    graph = _graph_cache.get(cache_key)
    if graph is not None:
        logger.debug("Skill graph cache hit for key %s", cache_key)
        return graph

    graph = build_graph_from_db(session, relation_types=relation_types)
    _graph_cache[cache_key] = graph
    logger.info("Skill graph cached for key %s", cache_key)
    return graph


def invalidate_graph_cache() -> None:
    """清空技能图谱模块缓存。"""
    _graph_cache.clear()
    logger.info("Skill graph cache invalidated")


def build_graph_from_db(
    session: Session, relation_types: list[str] | None = None
) -> nx.MultiDiGraph:
    """从数据库构建技能多重有向图。

    节点为技能名称；同一起止节点可存在多条不同类型的边。
    """
    graph = nx.MultiDiGraph()

    skills = session.query(Skill).all()
    for skill in skills:
        graph.add_node(
            skill.name,
            id=skill.id,
            category=skill.category,
            definition=skill.definition,
        )

    query = session.query(SkillRelation)
    if relation_types:
        query = query.filter(SkillRelation.relation_type.in_(relation_types))

    relation_rows = query.all()
    skill_name_map = {s.id: s.name for s in skills}

    for relation in relation_rows:
        source_name = skill_name_map.get(relation.source_skill_id)
        target_name = skill_name_map.get(relation.target_skill_id)
        if source_name is None or target_name is None:
            continue
        graph.add_edge(
            source_name,
            target_name,
            relation_type=relation.relation_type,
            weight=relation.weight,
        )

    logger.info(
        "Built skill graph with %s nodes and %s edges",
        graph.number_of_nodes(),
        graph.number_of_edges(),
    )
    return graph


def get_related_skills(
    graph: nx.MultiDiGraph,
    skill_name: str,
    relation_type: str | None = None,
    min_weight: float = 0.0,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """查询与指定技能相关的技能列表（每种关系类型返回一条）。"""
    if skill_name not in graph:
        return []

    results = []
    seen: set[tuple[str, str]] = set()
    for _, neighbor, _key, edge_data in graph.out_edges(skill_name, keys=True, data=True):
        rel_type = edge_data.get("relation_type")
        if relation_type and rel_type != relation_type:
            continue
        weight = edge_data.get("weight", 0.0)
        if weight < min_weight:
            continue
        key_pair = (neighbor, rel_type)
        if key_pair in seen:
            continue
        seen.add(key_pair)
        results.append(
            {
                "skill": neighbor,
                "relation_type": rel_type,
                "weight": weight,
            }
        )

    results.sort(key=lambda x: x["weight"], reverse=True)
    return results[:limit]


def get_learning_path(
    graph: nx.MultiDiGraph,
    start_skill: str,
    target_skill: str,
    weight_attr: str = "weight",
) -> dict[str, Any]:
    """基于依赖/相似/共现权重寻找从 start_skill 到 target_skill 的学习路径。

    使用 Dijkstra 算法在边权重上寻找最大权重路径（将权重取负后求最短）。
    """
    if start_skill not in graph or target_skill not in graph:
        return {
            "start": start_skill,
            "target": target_skill,
            "path": [],
            "found": False,
            "message": "起点或目标技能不在图谱中",
        }

    try:
        # 在 MultiDiGraph 上，NetworkX 会自动为每对节点选择权重最小的边；
        # weight 函数签名为 (u, v, data)。
        # 转换为最小化问题：权重越大越好 -> 使用 1 - weight 作为距离
        path = nx.shortest_path(
            graph,
            source=start_skill,
            target=target_skill,
            weight=lambda u, v, d: max(0.001, 1.0 - d.get(weight_attr, 0.0)),
            method="dijkstra",
        )
    except nx.NetworkXNoPath:
        return {
            "start": start_skill,
            "target": target_skill,
            "path": [],
            "found": False,
            "message": "未找到连通路径",
        }

    edges = []
    for i in range(len(path) - 1):
        # 在多重图中，选择权重最大的边作为展示
        best_weight = -1.0
        best_data: dict[str, Any] = {}
        for _key, data in graph[path[i]][path[i + 1]].items():
            weight = data.get(weight_attr, 0.0)
            if weight > best_weight:
                best_weight = weight
                best_data = data
        edges.append(
            {
                "from": path[i],
                "to": path[i + 1],
                "relation_type": best_data.get("relation_type"),
                "weight": best_data.get("weight", 0.0),
            }
        )

    return {
        "start": start_skill,
        "target": target_skill,
        "path": path,
        "found": True,
        "edges": edges,
        "message": f"找到包含 {len(path)} 个技能的学习路径",
    }
