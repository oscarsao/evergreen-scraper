"""
Adapters para diferentes APIs de búsqueda y scraping.
"""
from .base import SearchAdapter, SearchResult
from .firecrawl_adapter import FirecrawlAdapter
from .google_adapter import GoogleSearchAdapter, GooglePlacesAdapter
from .tavily_adapter import TavilyAdapter
from .openai_adapter import OpenAIAdapter

__all__ = [
    "SearchAdapter",
    "SearchResult",
    "FirecrawlAdapter",
    "GoogleSearchAdapter", 
    "GooglePlacesAdapter",
    "TavilyAdapter",
    "OpenAIAdapter",
]
