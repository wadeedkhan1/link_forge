"""
analysis/link_graph.py
──────────────────────
Returns data in a format ready for vis.js (the graph library we'll use in the UI):
  nodes: [{ id, label }, ...]
  edges: [{ from, to }, ...]
Directed graph
"""

from storage.db import get_all_links, get_all_pages
from urllib.parse import urlparse
from collections import deque


def _short_label(url: str, max_len: int = 40) -> str:
    """Shortens a URL to a readable label for graph nodes."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    label = parsed.netloc + path
    return label[:max_len] + "..." if len(label) > max_len else label


def build_graph(max_nodes: int = 100, session_id=None) -> dict:
    """
    Args:
        max_nodes : Limit nodes for UI rendering performance (default 100)
    Returns:
        { "nodes": [...], "edges": [...] }
        
    Uses BFS to trace the graph strictly from the seed URL, 
    ensuring no nodes are disconnected or floating.
    """
    all_pages  = get_all_pages(session_id)
    all_links  = get_all_links(session_id)
    
    if not all_pages:
        return {"nodes": [], "edges": []}
        
    # Use all seed URLs (depth=0) to ensure we map components for ALL sessions
    seeds = [p["url"] for p in all_pages if p.get("depth", 0) == 0]
    # Reversing seeds to prioritize newer sessions if we hit max_nodes limit
    seeds.reverse()
    if not seeds:
        seeds = [all_pages[-1]["url"]]  # fallback to newest page
    
    seeds = seeds[:max_nodes]
    
    # Build adjacency list
    adj = {}
    for link in all_links:
        src = link["source_url"]
        dst = link["target_url"]
        if src not in adj:
            adj[src] = []
        adj[src].append(dst)
        
    # BFS traversal starting from all seeds to collect at most max_nodes
    queue = deque(seeds)
    visited_nodes = set(seeds)
    visited_edges = []
    
    while queue and len(visited_nodes) < max_nodes:
        current = queue.popleft()
        
        for neighbor in adj.get(current, []):
            visited_edges.append({"from": current, "to": neighbor})
            if neighbor not in visited_nodes:
                visited_nodes.add(neighbor)
                if len(visited_nodes) >= max_nodes:
                    break
                queue.append(neighbor)
                
    nodes = [
        {"id": url, "label": _short_label(url)}
        for url in visited_nodes
    ]

    return {"nodes": nodes, "edges": visited_edges}


def get_most_linked(n: int = 10, session_id=None) -> list[dict]:
    """
    Returns: [{ "url": ..., "in_degree": 42 }, ...]
    """
    from collections import Counter
    all_links = get_all_links(session_id)

    # Count how many times each URL appears as a target
    in_degree = Counter(link["target_url"] for link in all_links)

    return [
        {"url": url, "in_degree": count}
        for url, count in in_degree.most_common(n)
    ]
