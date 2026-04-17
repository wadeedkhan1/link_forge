import json
import os
import csv
import pandas as pd
from storage.db import get_all_pages, get_all_links

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def export_json(filename: str = "pages.json") -> str:
    """
    Exports all crawled pages to a JSON file.
    Returns the path to the saved file.
    """
    pages = get_all_pages()
    data = [
        {
            "id":          p["id"],
            "url":         p["url"],
            "title":       p["title"],
            "text":        p["text"],
            "status_code": p["status_code"],
            "depth":       p["depth"],
            "crawled_at":  p["crawled_at"],
        }
        for p in pages
    ]
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[Export] JSON saved: {path}  ({len(data)} pages)")
    return path


def export_csv(filename: str = "pages.csv") -> str:
    """
    Exports all crawled pages to a CSV file using pandas.
    Returns the path to the saved file.
    """
    pages = get_all_pages()
    rows = [
        {
            "id":          p["id"],
            "url":         p["url"],
            "title":       p["title"],
            "status_code": p["status_code"],
            "depth":       p["depth"],
            "crawled_at":  p["crawled_at"],
            # Truncate text for CSV readability
            "text_preview": (p["text"] or "")[:200],
        }
        for p in pages
    ]
    df = pd.DataFrame(rows)
    path = os.path.join(DATA_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL, escapechar='\\')

    print(f"[Export] CSV saved: {path}  ({len(rows)} pages)")
    return path


def export_links_csv(filename: str = "links.csv") -> str:
    """
    Exports all discovered links (edges) to CSV.
    Useful for importing into graph tools like Gephi or NetworkX.
    """
    links = get_all_links()
    rows = [{"source": l["source_url"], "target": l["target_url"]} for l in links]
    df = pd.DataFrame(rows)
    path = os.path.join(DATA_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL, escapechar='\\')

    print(f"[Export] Links CSV saved: {path}  ({len(rows)} edges)")
    return path
