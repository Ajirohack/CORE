"""
Apify Adapter for The Archivist
- Integration with Apify's web scraping and automation capabilities
- Data extraction, transformation, and enrichment
- Scheduled web monitoring and updates

References:
- Apify: https://github.com/apify/apify-client-python
"""
import logging
import time
from typing import Dict, Any, List, Optional, Union


class ApifyActorStub:
    """Stub for Apify actor if the real package isn't available"""
    
    def __init__(self, client, actor_id: str):
        self.client = client
        self.actor_id = actor_id
        self.run_count = 0
        
    def call(self, run_input: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Simulate calling an Apify actor"""
        self.run_count += 1
        run_id = f"{self.actor_id}_run_{self.run_count}"
        
        # Simulate processing time
        time.sleep(0.5)
        
        # Example response structure based on actor type
        if "crawler" in self.actor_id.lower():
            return self._simulate_crawler_result(run_input, run_id)
        elif "scraper" in self.actor_id.lower():
            return self._simulate_scraper_result(run_input, run_id)
        else:
            return {
                "id": run_id,
                "actorId": self.actor_id,
                "status": "SUCCEEDED",
                "output": {
                    "message": f"Simulated result for {self.actor_id}",
                    "runInput": run_input
                }
            }
    
    def _simulate_crawler_result(self, run_input: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Simulate a web crawler result"""
        urls = run_input.get("startUrls", [{"url": "https://example.com"}])
        results = []
        
        for url_obj in urls:
            url = url_obj.get("url", "https://example.com")
            results.append({
                "url": url,
                "title": f"Page title for {url}",
                "links": [f"{url}/page1", f"{url}/page2"],
                "text": f"Simulated content for {url}..."
            })
            
        return {
            "id": run_id,
            "actorId": self.actor_id,
            "status": "SUCCEEDED",
            "output": {
                "crawledPages": len(results),
                "results": results
            }
        }
    
    def _simulate_scraper_result(self, run_input: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Simulate a web scraper result"""
        urls = run_input.get("startUrls", [{"url": "https://example.com"}])
        results = []
        
        for url_obj in urls:
            url = url_obj.get("url", "https://example.com")
            results.append({
                "url": url,
                "data": {
                    "title": f"Scraped title for {url}",
                    "description": f"Scraped description for {url}",
                    "items": [
                        {"name": "Item 1", "price": "€10.00"},
                        {"name": "Item 2", "price": "€20.00"}
                    ]
                }
            })
            
        return {
            "id": run_id,
            "actorId": self.actor_id,
            "status": "SUCCEEDED",
            "output": {
                "scrapedPages": len(results),
                "results": results
            }
        }


class ApifyClientStub:
    """Stub for Apify client if the real package isn't available"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.actors = {}
        
    def actor(self, actor_id: str) -> ApifyActorStub:
        """Get an actor by ID"""
        if actor_id not in self.actors:
            self.actors[actor_id] = ApifyActorStub(self, actor_id)
        return self.actors[actor_id]


# Try to load the real Apify client or fall back to stub
try:
    from apify_client import ApifyClient
    logging.info("Loaded real Apify client")
except ImportError:
    ApifyClient = ApifyClientStub
    logging.warning("Using Apify client stub - for real functionality, install apify-client")


class ApifyAdapter:
    """Adapter for Apify functionality in The Archivist"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the Apify adapter"""
        self.client = ApifyClient(token=token)
        self.recent_runs = []
        self.max_recent = 50
        
        # Define commonly used actors
        self.actors = {
            "web_crawler": "apify/web-crawler",
            "cheerio_scraper": "apify/cheerio-scraper",
            "puppeteer_scraper": "apify/puppeteer-scraper",
            "url_list": "apify/url-list-crawler",
            "google_serp": "apify/google-search-scraper"
        }
        
    def crawl_website(self, start_urls: List[str], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Crawl a website using Apify's web crawler"""
        options = options or {}
        
        # Prepare input
        run_input = {
            "startUrls": [{"url": url} for url in start_urls],
            "maxCrawlDepth": options.get("max_depth", 1),
            "maxCrawlPages": options.get("max_pages", 10)
        }
        
        # Add other options if provided
        if "pseudo_urls" in options:
            run_input["pseudoUrls"] = [{"purl": url} for url in options["pseudo_urls"]]
        
        result = self.client.actor(self.actors["web_crawler"]).call(run_input=run_input)
        
        # Track recent runs
        self.recent_runs.append({
            "actor": self.actors["web_crawler"],
            "input": run_input,
            "result_summary": {
                "crawled_pages": result.get("output", {}).get("crawledPages", 0),
                "status": result.get("status")
            },
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.recent_runs) > self.max_recent:
            self.recent_runs.pop(0)
            
        return result
        
    def scrape_data(self, urls: List[str], selectors: Dict[str, str], use_browser: bool = False) -> Dict[str, Any]:
        """Scrape data from websites using selectors"""
        # Choose appropriate scraper based on needs
        actor_key = "puppeteer_scraper" if use_browser else "cheerio_scraper"
        
        # Prepare input
        run_input = {
            "startUrls": [{"url": url} for url in urls],
            "pageFunction": f"""async function pageFunction(context) {{
                const {{ request, log, jQuery }} = context;
                const $ = jQuery;
                const result = {{
                    url: request.url,
                    data: {{}}
                }};
                
                // Extract data using the provided selectors
                {self._generate_selector_code(selectors)}
                
                return result;
            }}"""
        }
        
        result = self.client.actor(self.actors[actor_key]).call(run_input=run_input)
        
        # Track recent runs
        self.recent_runs.append({
            "actor": self.actors[actor_key],
            "input": {
                "urls": urls,
                "selectors": selectors
            },
            "result_summary": {
                "scraped_pages": result.get("output", {}).get("scrapedPages", 0),
                "status": result.get("status")
            },
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.recent_runs) > self.max_recent:
            self.recent_runs.pop(0)
            
        return result
        
    def search_google(self, query: str, max_pages: int = 1) -> Dict[str, Any]:
        """Search Google and extract results"""
        # Prepare input
        run_input = {
            "queries": query,
            "maxPagesPerQuery": max_pages,
            "resultsPerPage": 10,
            "languageCode": "en"
        }
        
        result = self.client.actor(self.actors["google_serp"]).call(run_input=run_input)
        
        # Track recent runs
        self.recent_runs.append({
            "actor": self.actors["google_serp"],
            "input": run_input,
            "result_summary": {
                "pages": max_pages,
                "query": query,
                "status": result.get("status")
            },
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.recent_runs) > self.max_recent:
            self.recent_runs.pop(0)
            
        return result
        
    def run_actor(self, actor_id: str, run_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run a custom Apify actor"""
        result = self.client.actor(actor_id).call(run_input=run_input)
        
        # Track recent runs
        self.recent_runs.append({
            "actor": actor_id,
            "input": run_input,
            "result_summary": {
                "status": result.get("status")
            },
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.recent_runs) > self.max_recent:
            self.recent_runs.pop(0)
            
        return result
        
    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent actor runs"""
        return sorted(self.recent_runs, key=lambda x: x["timestamp"], reverse=True)[:limit]
        
    def _generate_selector_code(self, selectors: Dict[str, str]) -> str:
        """Generate JavaScript code to extract data using selectors"""
        code_lines = []
        
        for field, selector in selectors.items():
            code_lines.append(f"""
                try {{
                    result.data['{field}'] = $('{selector}').text().trim();
                }} catch (e) {{
                    log.error(`Error extracting {field}: ${{e}}`);
                    result.data['{field}'] = null;
                }}
            """)
            
        return "\n".join(code_lines)
