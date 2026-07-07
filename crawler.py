#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import time

# Попытка использовать tldextract для корректного определения зарегистрированного домена
try:
    import tldextract
    def get_registered_domain(url):
        ext = tldextract.extract(url)
        if ext.registered_domain:
            return ext.registered_domain.lower()
        # fallback
        host = urlparse(url).hostname or ""
        return host.lower()
except Exception:
    def get_registered_domain(url):
        host = urlparse(url).hostname or ""
        parts = host.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:]).lower()
        return host.lower()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SimpleCrawler/1.0; +https://rodosnn.ru/)"
}
REQUEST_TIMEOUT = 10.0

def fetch_text(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
        return None, []
    content_type = resp.headers.get("Content-Type", "")
    if "text" not in content_type:
        return None, []
    soup = BeautifulSoup(resp.text, "html.parser")
    # Удалим скрипты и стили
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Соберём ссылки
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href").strip()
        if not href:
            continue
        # Игнорируем почту и javascript
        if href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        full = urljoin(url, href)
        parsed = urlparse(full)
        if parsed.scheme not in ("http", "https"):
            continue
        links.append(full)
    return text, links

def save_text(output_file, url, text):
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"[{url}]\n")
        f.write(text if text else "")
        f.write("\n\n")

def crawl(start_url, max_depth=2, output_file="output.txt", delay=0.5):
    start_domain = get_registered_domain(start_url)
    visited = set()

    # Очистим файл перед началом
    open(output_file, "w", encoding="utf-8").close()

    def _crawl(url, depth):
        if depth > max_depth:
            return
        if url in visited:
            return
        visited.add(url)
        print(f"Crawling (depth {depth}): {url}")
        text, links = fetch_text(url)
        if text is None:
            return
        save_text(output_file, url, text)
        if depth == max_depth:
            return
        for link in links:
            try:
                link_domain = get_registered_domain(link)
            except Exception:
                continue
            if link_domain == start_domain:
                _crawl(link, depth + 1)
                time.sleep(delay)

    _crawl(start_url, 0)
    print(f"Готово. Сохранено в {output_file}. Посещено {len(visited)} страниц.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python crawler.py <start_url> [max_depth] [output_file]")
        sys.exit(1)
    start = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) >= 3 else 2
    out = sys.argv[3] if len(sys.argv) >= 4 else "output.txt"
    crawl(start, max_depth=depth, output_file=out)
