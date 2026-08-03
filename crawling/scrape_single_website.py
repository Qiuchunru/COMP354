import multiprocessing
import threading
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, urljoin
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time

def crawl_page(url):
    """Fetch the HTML content of a page using an existing browser page instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(2) 
        content = page.content()
        browser.close()
    return content

def get_internal_links(html, base_url):
    """Extract internal links from the HTML content relative to the base URL."""
    # Very simple regex for hrefs (Playwright could also evaluate in page)
    href_pattern = re.compile(r'href=["\'](.*?)["\']', re.IGNORECASE)
    links = href_pattern.findall(html)
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    internal_links = []
    for link in links:
        # Build absolute URL
        absolute = urljoin(base_url, link)
        parsed = urlparse(absolute)

        if parsed.path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.mp4', '.mp3', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.css', '.js', '.ico', '.woff', '.woff2')):
            continue  # Skip common file types

        # Keep only links within the same domain
        if parsed.netloc == base_domain or parsed.netloc == 'www.'+ base_domain or 'www.'+'.'.join(parsed.netloc.split('.')[-2:]) == base_domain or '.'.join(parsed.netloc.split('.')[-2:]) == base_domain:
            # Remove fragments, query params for consistency
            clean_url = parsed.scheme + "://" + parsed.netloc + parsed.path
            if clean_url not in internal_links:
                internal_links.append(clean_url)

    return internal_links[::-1]  # Reverse links because usually site links are at the end of the page (contact, about, etc.)

def bfs_crawl(start_url):
    """Perform BFS starting from start_url."""
    visited = set()
    emails_found = set()
    queue = deque([start_url])
    cpu_count = multiprocessing.cpu_count()
    max_concurrent = min(max(2, cpu_count // 2), 4)  # Between 2-4 workers based on CPU
    pages_crawled = 0
    max_pages = 1000

    lock = threading.Lock()


    while queue and pages_crawled < max_pages:
        batch_size = min(max_concurrent, len(queue), max_pages - pages_crawled)
        batch_urls = []

        with lock:
            for _ in range(batch_size):
                if queue and pages_crawled < max_pages:
                    url = queue.popleft()
                    if url not in visited:
                        visited.add(url)
                        batch_urls.append(url)
                        pages_crawled += 1

        if not batch_urls:
            break

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_url = {executor.submit(crawl_page, url): url for url in batch_urls}

            for future in as_completed(future_to_url, timeout=30):
                url = future_to_url[future]
                try:
                    html = future.result()

                    if html:
                        new_emails = extract_emails(html)
                        unique_emails = []

                        with lock:
                            for email in set(new_emails):
                                if email not in emails_found:
                                    emails_found.add(email)
                                    unique_emails.append(email)
                        
                        if unique_emails:
                            print(f"Found emails on {url}:")
                            for email in unique_emails:
                                print(f" - {email}")

                        new_links = get_internal_links(html, url)
                        with lock:
                            for link in new_links:
                                if link not in visited and link not in queue:
                                    queue.append(link)
                
                except Exception as e:
                    print(f"Failed to crawl {url}")
                    continue

def extract_emails(html):
    # More accurate regex pattern for emails with better validation
    email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', re.IGNORECASE)
    potential_emails = email_pattern.findall(html)
    
    # Filter out false positives (JS/CSS files, common non-email patterns)
    valid_emails = []
    for email in potential_emails:
        # Skip if it looks like a file reference
        if any(ext in email.lower() for ext in ['.js', '.css', '.min.', '.bundle', '.chunk', '.hash']):
            continue
        
        # Skip if it contains version numbers or build artifacts
        if re.search(r'@\d+(\.\d+)*', email):  # matches @8, @8.min, etc.
            continue
            
        # Skip if it's just numbers/symbols around @
        if re.search(r'^[0-9@.-]+$', email):
            continue
            
        # Additional validation: must have at least one letter before and after @
        parts = email.split('@')
        if len(parts) == 2:
            local, domain = parts
            # Local part should have at least one letter
            if re.search(r'[a-zA-Z]', local) and re.search(r'[a-zA-Z]', domain):
                # Domain should look like a real domain (not just numbers)
                if '.' in domain and not domain.startswith('.') and not domain.endswith('.'):
                    valid_emails.append(email)
    
    return valid_emails

if __name__ == "__main__":
    domain_url = input("Enter the domain URL: ").strip()
    
    if not domain_url.startswith("http"):
        domain_url = "http://" + domain_url  # Ensure the URL starts with http or https
    
    print("Starting BFS crawl...\n")
    bfs_crawl(domain_url)
