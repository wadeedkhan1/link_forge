"""
ui/app.py
─────────
Flask web application. Routes:
  GET  /           → home page (crawl form)
  POST /crawl      → starts the Scrapy spider in a subprocess
  GET  /results    → table of all crawled pages
  GET  /search     → keyword search results
  GET  /graph      → link graph visualization page
  GET  /api/graph  → returns graph JSON for vis.js
  GET  /export/json → download pages.json
  GET  /export/csv  → download pages.csv
"""

import os
import sys
import subprocess
import threading

import datetime

# Add project root to path so we can import storage/analysis modules
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import requests

from storage.db import init_db, get_all_pages, get_page_count, search_pages, get_latest_session
from analysis.keyword_search import count_keyword_frequency, top_words
from analysis.link_graph import build_graph, get_most_linked
from analysis.export import export_json, export_csv

app = Flask(__name__, template_folder='ui/templates', static_folder='ui/static')

# Global crawl state
crawl_status = {"running": False, "message": "Idle", "session_id": None}
current_process = None

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Home page — shows crawl form and quick stats."""
    # Ensure our status has the latest session if not crawling right now
    if not crawl_status["running"] and not crawl_status.get("session_id"):
        crawl_status["session_id"] = get_latest_session()

    sid = crawl_status.get("session_id")
    stats = {
        "page_count": get_page_count(session_id=sid),
        "top_words":  top_words(8, session_id=sid),      # Requires modifying top_words optionally
        "most_linked": get_most_linked(5, session_id=sid), # Requires modifying most_linked optionally
    }
    return render_template("index.html", stats=stats, crawl_status=crawl_status)


@app.route("/crawl", methods=["POST"])
def start_crawl():
    """
    Starts the Scrapy spider in a background subprocess.
    Using subprocess allows Scrapy (which has its own async event loop)
    to run independently without blocking Flask.
    """
    global crawl_status

    if crawl_status["running"]:
        return jsonify({"error": "A crawl is already running"}), 400

    prompt = request.form.get("prompt", "").strip()
    depth    = request.form.get("depth", "1").strip()

    # Validate depth
    try:
        depth = max(1, min(int(depth), 3))   # clamp between 1 and 3
    except ValueError:
        depth = 1

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # Call Serper API
    api_url = "https://google.serper.dev/search"
    payload = {"q": prompt}
    headers = {
        'X-API-KEY': 'a14bc17a7aa382b5686185eb12245822341b0d15',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        organic_results = data.get("organic", [])
        
        # Extract up to 5 links from the search results
        seed_urls = [result["link"] for result in organic_results if "link" in result][:5]
        if not seed_urls:
             return jsonify({"error": "No links found for the prompt"}), 400
             
        seed_url_arg = ",".join(seed_urls)
        
    except Exception as e:
        return jsonify({"error": f"Failed to get links from Serper: {str(e)}"}), 500

    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    crawl_status["session_id"] = session_id

    def run_crawl():
        global crawl_status, current_process
        crawl_status = {"running": True, "message": f"Crawling results for '{prompt}' (depth={depth})...", "session_id": session_id}

        project_root = os.path.dirname(__file__)

        cmd = [
            sys.executable, "-m", "scrapy", "crawl", "web_spider",
            "-a", f"seed_url={seed_url_arg}",
            "-a", f"depth={depth}",
            "-a", f"session_id={session_id}",
            "-a", f"prompt={prompt}",
            "-s", "SCRAPY_SETTINGS_MODULE=spiders.settings",
            "-s", f"DEPTH_LIMIT={depth}",
            "--nolog",
        ]

        try:
            current_process = subprocess.Popen(cmd, cwd=project_root)
            current_process.wait()
            
            if current_process.returncode == 0:
                crawl_status = {"running": False, "message": f"Done! Indexed {get_page_count(session_id=session_id)} pages.", "session_id": session_id}
            else:
                # If stopped forcefully, the return code is non-zero
                if crawl_status.get("message") != "Crawl stopped.":
                    crawl_status = {"running": False, "message": f"Crawl stopped or failed (code {current_process.returncode})", "session_id": session_id}
        except Exception as e:
            crawl_status = {"running": False, "message": f"Crawl error: {e}", "session_id": session_id}
        finally:
            current_process = None

    thread = threading.Thread(target=run_crawl, daemon=True)
    thread.start()

    return redirect(url_for("index"))

@app.route("/stop", methods=["POST"])
def stop_crawl():
    global current_process, crawl_status
    if current_process:
        try:
            current_process.terminate()
            crawl_status["running"] = False
            crawl_status["message"] = "Crawl stopped."
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "No crawl running"}), 400


@app.route("/status")
def crawl_status_api():
    """Returns current crawl status as JSON. Used by the UI to poll progress."""
    sid = crawl_status.get("session_id")
    return jsonify({
        **crawl_status,
        "page_count": get_page_count(session_id=sid)
    })

@app.route("/api/recent")
def api_recent():
    """Returns the last N crawled pages of the active session."""
    n = int(request.args.get("n", 12))
    sid = crawl_status.get("session_id")
    all_pages = get_all_pages(session_id=sid)
    recent = all_pages[-n:][::-1]   # last N, newest first
    return jsonify([
        {
            "url":   p["url"],
            "title": p["title"] or "No Title",
            "depth": p["depth"],
            "status_code": p["status_code"],
        }
        for p in recent
    ])


@app.route("/results")
def results():
    """Shows all crawled pages in a paginated table."""
    page_num  = int(request.args.get("page", 1))
    per_page  = 20

    all_pages = get_all_pages()
    all_pages.reverse()  
    total     = len(all_pages)
    start     = (page_num - 1) * per_page
    end       = start + per_page
    pages     = all_pages[start:end]
    total_pages = (total + per_page - 1) // per_page

    page_start = max(1, page_num - 2)
    page_end   = min(total_pages + 1, page_num + 3)
    page_range = list(range(page_start, page_end))

    return render_template(
        "results.html",
        pages       = pages,
        page_num    = page_num,
        total_pages = total_pages,
        total       = total,
        page_range  = page_range,
    )


@app.route("/search")
def search():
    """Keyword search across all crawled page text."""
    keyword = request.args.get("q", "").strip()
    results_data = []
    if keyword:
        results_data = count_keyword_frequency(keyword)
    return render_template("search.html", keyword=keyword, results=results_data)


@app.route("/graph")
def graph():
    """Link graph visualisation page (uses vis.js)."""
    most_linked = get_most_linked(10)
    return render_template("graph.html", most_linked=most_linked)


@app.route("/api/graph")
def api_graph():
    """Returns graph data as JSON for vis.js to render."""
    max_nodes = int(request.args.get("max_nodes", 80))
    data = build_graph(max_nodes=max_nodes)
    return jsonify(data)


@app.route("/export/json")
def export_json_route():
    sid = crawl_status.get("session_id")
    path = export_json(session_id=sid)
    return send_file(os.path.abspath(path), as_attachment=True, download_name="pages.json")


@app.route("/export/csv")
def export_csv_route():
    sid = crawl_status.get("session_id")
    path = export_csv(session_id=sid)
    return send_file(os.path.abspath(path), as_attachment=True, download_name="pages.csv")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("[Flask] Starting Web Crawler UI at http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)
