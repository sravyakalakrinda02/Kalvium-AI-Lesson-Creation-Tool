"""Public-source research helpers for websites, books and YouTube."""
import requests
from urllib.parse import quote_plus

TIMEOUT = 15
HEADERS = {"User-Agent": "LessonCraftAI/1.0 (educational research prototype)"}

def _get_json(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def search_web(query, limit=6):
    """Use DDGS text search; retain an explicit search fallback if unavailable."""
    results = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=limit):
                results.append({"title": item.get("title", "Web result"), "url": item.get("href", ""), "snippet": item.get("body", ""), "source": "DuckDuckGo web search"})
    except Exception:
        pass
    if not results:
        results.append({"title": f"Search the web for: {query}", "url": "https://duckduckgo.com/?q=" + quote_plus(query), "snippet": "Automated search results were unavailable. Open this search link and review suitable sources manually.", "source": "DuckDuckGo search fallback"})
    return results[:limit]

def search_books(query, limit=5):
    data = _get_json("https://openlibrary.org/search.json", {"q": query, "limit": limit}) or {}
    out = []
    for d in data.get("docs", [])[:limit]:
        title = d.get("title", "Untitled")
        authors = ", ".join(d.get("author_name", [])[:3]) or "Author not listed"
        key = d.get("key")
        out.append({"title": title, "url": ("https://openlibrary.org" + key) if key else "https://openlibrary.org/search?q=" + quote_plus(query), "snippet": f"Author(s): {authors}; first published: {d.get('first_publish_year', 'not listed')}", "source": "Open Library catalogue"})
    if not out:
        out.append({"title": f"Book catalogue search: {query}", "url": "https://openlibrary.org/search?q=" + quote_plus(query), "snippet": "Search the Open Library catalogue for relevant books.", "source": "Open Library"})
    return out

def search_youtube(query, limit=5):
    """Retrieve actual video results with yt-dlp's YouTube search extractor."""
    out = []
    try:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query} educational tutorial", download=False)
        for item in (info or {}).get("entries", [])[:limit]:
            video_id = item.get("id")
            if video_id:
                out.append({"title": item.get("title", "YouTube video"), "url": f"https://www.youtube.com/watch?v={video_id}", "snippet": f"Channel: {item.get('channel') or item.get('uploader') or 'Not listed'}; duration: {item.get('duration') or 'not listed'} seconds", "source": "YouTube search"})
    except Exception:
        pass
    if not out:
        out.append({"title": f"YouTube learning videos: {query}", "url": "https://www.youtube.com/results?search_query=" + quote_plus(query + " tutorial"), "snippet": "Automated video lookup was unavailable. Open this search and select a relevant educational video.", "source": "YouTube search fallback"})
    return out

def run_research(title, objective):
    query = f"{title}: {objective}"
    return {"query": query, "web": search_web(query), "books": search_books(title), "youtube": search_youtube(title)}
