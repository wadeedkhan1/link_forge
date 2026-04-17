# Modular Web Crawler & Analyzer

A Python-based, fully automated web crawler with a beautiful Flask-powered user interface. This crawler leverages Scrapy for high-performance crawling and SQLite for persistence, parsing HTML to generate beautiful search indexing and interactive link-graph topology.

## Quickstart

If you have just cloned this repository, follow these instructions to get the application running on your local machine:

### 1. Prerequisites
Make sure you have Python 3.9+ installed on your system.

### 2. Setup Virtual Environment (Recommended)
It is highly recommended to create an isolated virtual environment so you don't conflict with other Python projects on your system:

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Install all required libraries (Flask, Scrapy, BeautifulSoup, etc.):
```bash
pip install -r requirements.txt
```

### 4. Run the Application
The application is controlled via a unified UI entry point. Start the server using:
```bash
python app.py
```

### 5. Start Crawling
Open your web browser and navigate to `http://127.0.0.1:5000`. From the unified dashboard, enter a seed URL (e.g. `http://books.toscrape.com/`), specify a depth limit, and click **Start Crawl**. 

The UI will provide live progress reporting, allowing you to browse search results and view an interactive visualization of the web graph in real-time!
