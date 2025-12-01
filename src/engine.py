import json
from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests
import tldextract
from urllib.parse import urljoin
from collections import deque
import logging
import webbrowser
from threading import Timer

# --- IMPORTS TO HANDLE SSL WARNINGS ---
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# --- Suppress only the InsecureRequestWarning ---
urllib3.disable_warnings(InsecureRequestWarning)


# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Python Backend (Flask Server) ---
app = Flask(__name__, 
            template_folder='components', 
            static_folder='components')

# --- Frontend Route ---
@app.route('/')
def index():
    """Serves the main index.html file from the 'components' folder."""
    return render_template('index.html')

# --- API Route ---
def get_page_title(soup):
    """Extracts the page title from the parsed HTML (soup)."""
    try:
        title = soup.title.string
        if title:
            return title.strip()
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        return "[No Title Found]"
    except Exception:
        return "[Title Parse Error]"

# --- NEW: Advanced Fingerprinting Function ---
def fingerprint_response(response, soup):
    """
    Analyzes an HTTP response to identify CDN & WAF services.
    Returns a dictionary of all info.
    """
    headers = {k.lower(): v.lower() for k, v in response.headers.items()}
    title = soup.title.string.lower() if soup.title else ""
    body_text = soup.get_text().lower()
    
    status_code = response.status_code
    services = {"cdn": None, "waf": None}
    
    # --- 1. Detect CDN/WAF/Security based on headers ---
    server = headers.get('server', '')
    
    # --- Hybrids (CDN + WAF) ---
    # Cloudflare
    if 'cloudflare' in server or soup.find("form", id="cf-challenge-form"):
        services["cdn"] = "Cloudflare"
        services["waf"] = "Cloudflare"
    
    # Akamai
    if 'akamai' in server or 'x-akamai-transformed' in headers:
        services["cdn"] = "Akamai"
        if "AkamaiGHost" in server or "akamai-bot-manager" in body_text:
             services["waf"] = "Akamai (Bot Manager)"

    # Imperva / Incapsula
    if 'x-iinfo' in headers or 'incapsula' in server:
        services["cdn"] = "Imperva"
        services["waf"] = "Imperva (Incapsula)"

    # Sucuri
    if 'x-sucuri-id' in headers or 'sucuri/cloudproxy' in server:
        services["cdn"] = "Sucuri"
        services["waf"] = "Sucuri"

    # --- CDN-Only (or CDN with separate WAF) ---
    if not services["cdn"]: # Only check if not already found by a hybrid
        if 'cloudfront' in server or 'x-amz-cf-id' in headers:
            services["cdn"] = "AWS CloudFront"
        elif 'fastly' in server or ('x-served-by' in headers and 'x-cache' in headers):
            services["cdn"] = "Fastly"
        elif 'bunnycdn' in server:
            services["cdn"] = "BunnyCDN"
        elif 'keycdn' in headers.get('x-cache', ''):
            services["cdn"] = "KeyCDN"
            
    # --- WAF-Only (or WAF with separate CDN) ---
    if not services["waf"]: # Only check if not already found by a hybrid
        if headers.get('x-amz-waf-action'): # AWS WAF
            services["waf"] = "AWS WAF"
        if "datadome" in str(response.cookies) or "pardon our interruption" in title:
            services["waf"] = "DataDome"
        if "f5-w" in headers or "BIG-IP" in server:
            services["waf"] = "F5 BIG-IP"

    # --- Set Defaults (This is your "No CDN" logic) ---
    if not services["cdn"]:
        services["cdn"] = "N/A (Direct Host)"
    if not services["waf"]:
        services["waf"] = "N/A"

    # --- 2. Determine Status Type based on response ---
    
    # Check for Bot Blocker Pages (This is your "poke" logic)
    if (any(s in title for s in ["just a moment", "checking your browser", "access denied"]) or
        any(s in body_text for s in ["human verification", "are you a robot", "captcha"])):
        
        # If we weren't sure what WAF it was, mark it as "Generic"
        if services["waf"] == "N/A":
            services["waf"] = "Generic Bot-Block"
            
        return {
            "type": "Blocked", "note": f"Anti-Bot page detected",
            "status": status_code, "services": services, "title": get_page_title(soup)
        }
        
    # 2xx: Success
    if 200 <= status_code < 300:
        if 'text/html' in headers.get('content-type', ''):
            return {
                "type": "Page", "note": "OK",
                "status": status_code, "services": services, "title": get_page_title(soup)
            }
        else:
            return {
                "type": "File", "note": headers.get('content-type', 'N/A'),
                "status": status_code, "services": services, "title": "[Non-HTML File]"
            }
    
    # 3xx: Redirect
    if 300 <= status_code < 400:
        return {
            "type": "Redirect", "note": f"Redirects to: {headers.get('location', 'N/A')}",
            "status": status_code, "services": services, "title": get_page_title(soup)
        }

    # 4xx: Client Error (e.g., 404 Not Found)
    if 400 <= status_code < 500:
        return {
            "type": "Error", "note": f"Client Error: {response.reason}",
            "status": status_code, "services": services, "title": get_page_title(soup)
        }
        
    # 5xx: Server Error
    if 500 <= status_code < 600:
        return {
            "type": "Error", "note": f"Server Error: {response.reason}",
            "status": status_code, "services": services, "title": get_page_title(soup)
        }

    # Default fallback
    return {
        "type": "Error", "note": f"Unknown Status",
        "status": status_code, "services": services, "title": get_page_title(soup)
    }

@app.route('/crawl', methods=['POST'])
def crawl():
    """The main spider/crawler API endpoint (upgraded)."""
    data = request.get_json()
    start_url = data.get('url')

    if not start_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        start_info = tldextract.extract(start_url)
        base_domain = f"{start_info.domain}.{start_info.suffix}"
        
        if not base_domain:
             return jsonify({"error": "Could not parse a valid domain from the URL"}), 400

        log.info(f"Starting crawl for base domain: {base_domain}")

        urls_to_crawl = deque([start_url])
        visited_urls = set()
        results = [] 
        headers = {
            # Using a common browser user-agent
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        crawl_limit = 100 

        while urls_to_crawl and len(visited_urls) < crawl_limit:
            current_url = urls_to_crawl.popleft()
            if current_url in visited_urls:
                continue
            
            current_url = current_url.split('#')[0]
            visited_urls.add(current_url)
            log.info(f"Visiting: {current_url}")
            
            result_obj = {"url": current_url} # Start building the result

            try:
                # We add allow_redirects=True so we can analyze the *final* page
                response = requests.get(current_url, headers=headers, timeout=5, verify=False, allow_redirects=True)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # --- Call the new analyzer ---
                analysis = fingerprint_response(response, soup)
                
                result_obj.update({
                    "title": analysis["title"],
                    "status": analysis["status"],
                    "type": analysis["type"],
                    "note": analysis["note"],
                    "services": analysis["services"] # This is the new services object
                })

                # --- Only crawl links from successful pages ---
                if analysis["type"] == "Page":
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        new_url = urljoin(current_url, href).split('#')[0]
                        
                        new_info = tldextract.extract(new_url)
                        new_base_domain = f"{new_info.domain}.{new_info.suffix}"

                        if new_base_domain == base_domain and new_url not in visited_urls and new_url.startswith('http'):
                            urls_to_crawl.append(new_url)

            except requests.RequestException as e:
                # --- Handle Connection Errors (SSL, DNS, Timeout, etc.) ---
                log.warning(f"Could not crawl {current_url}: {e}")
                result_obj.update({
                    "title": "[No Response]", "status": "N/A",
                    "type": "Error", "note": "Connection failed (e.g., SSL error or timeout)", "services": {"cdn": "N/A", "waf": "N/A"}
                })
            except Exception as e:
                # --- Handle local errors ---
                log.error(f"An unexpected error occurred at {current_url}: {e}")
                result_obj.update({
                    "title": "[Parsing Error]", "status": "N/A",
                    "type": "Error", "note": f"Local error: {str(e)}", "services": {"cdn": "N/A", "waf": "N/A"}
                })
            
            results.append(result_obj)

        log.info(f"Crawl finished. Processed {len(visited_urls)} URLs.")
        return jsonify(results)

    except Exception as e:
        log.error(f"Crawl failed entirely: {e}")
        return jsonify({"error": str(e)}), 500

# --- Main execution functions ---
def open_browser(url):
    """Opens the web browser to the specified URL."""
    webbrowser.open_new_tab(url)

# This function is called by zorah.py
def start_server():
    from waitress import serve
    host = '127.0.0.1'
    port = 8080
    
    # Run the server
    serve(app, host=host, port=port)

if __name__ == '__main__':

    start_server()
