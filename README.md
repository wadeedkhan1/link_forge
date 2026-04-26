# Modular Web Crawler & Analyzer

A Python-based, fully automated web crawler with a beautiful Flask-powered user interface. This crawler leverages Scrapy for high-performance crawling and SQLite for persistence, parsing HTML to generate beautiful search indexing and an interactive link-graph topology. 

### ✨ Features
- **Prompt-Based Crawling:** Powered by the [Serper API](https://serper.dev/), simply enter a topic like "Best games of 2026", and the crawler will automatically fetch relevant Google search results as seed URLs.
- **Smart Social Media Limits:** Automatically stops deep, recursive crawling into infinite-scrolling platforms like Reddit, Instagram, Facebook, and YouTube to prevent endless loops.
- **Session-Based Exports:** Easily export your scraped data to JSON or CSV for the *current* session rather than dealing with massive datasets from past crawls.
- **Interactive UI & Controls:** Clean Google-like search interface with dynamic Shallow/Medium/Deep crawl options and a force-stop button to halt the crawler at any time.

---

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
Install all required libraries (Flask, Scrapy, BeautifulSoup, Requests, pandas, etc.):
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
The application uses Serper API to convert search prompts into crawler starting points. 
- The project is currently configured with a default demo key in `app.py`. 
- If you run into rate limits, get a free API key from [serper.dev](https://serper.dev/), open `app.py`, and replace the `X-API-KEY` value with your own.

### 5. Run the Application
The application is controlled via a unified UI entry point. Start the server using:
```bash
python app.py
```

### 6. Start Crawling
Open your web browser and navigate to `http://127.0.0.1:5000`. 
1. Enter a search prompt (e.g. `Latest AI advancements`).
2. Select your crawl depth:
   - **Shallow:** Minimal depth.
   - **Medium:** Explores links found on the main pages.
   - **Deep:** Explores links within the subpages.
3. Click **Search** to begin crawling. You can click **Stop** at any point to halt the process.
4. View the interactive link graph, or export your session data to JSON/CSV directly from the dashboard!
