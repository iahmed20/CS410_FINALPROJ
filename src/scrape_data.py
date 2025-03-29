
import os
import urllib.error
import urllib.request
import io
import base64

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

PAGE_CACHE_DIR = os.path.join(DATA_DIR, "page_cache")
RAW_TEXT_DIR = os.path.join(DATA_DIR, "raw")

os.makedirs(DATA_DIR, exist_ok = True)
os.makedirs(PAGE_CACHE_DIR, exist_ok = True)
os.makedirs(RAW_TEXT_DIR, exist_ok = True)

def get_page(url):
    page_hash = base64.b64encode(url.encode("utf-8")).decode("utf-8")
    cached_page_path = os.path.join(PAGE_CACHE_DIR, f"{page_hash}.html")
    if os.path.exists(cached_page_path):
        with open(cached_page_path, "rb") as f:
            body = f.read()
            return io.BytesIO(body)
    else:
        body = None
        try:
            with urllib.request.urlopen(url) as resp:
                body = resp.read()
        except urllib.error.HTTPError:
            body = b""
        with open(cached_page_path, "wb") as f:
            f.write(body)
        return io.BytesIO(body)     

def get_top_100_authors_gutenberg():
    authors = {}
    resp = get_page("https://gutenberg.org/browse/scores/top")
    line_iter = io.TextIOWrapper(resp, encoding = "utf-8")
    reading = False
    for line in line_iter:
        line = line.strip()
        if line == """<h2 id="authors-last30">Top 100 Authors last 30 days</h2>""":
            next(line_iter)
            next(line_iter)
            reading = True
        elif reading and line == "</ol>":
            reading = False
            break
        elif reading:
            line = line[32:-10]
            i = 0
            author_id = ""
            while line[i] != "\"":
                author_id += line[i]
                i += 1
            i += 2
            author_name = ""
            while line[i] != "(":
                author_name += line[i]
                i += 1
            authors[author_id] = author_name.strip()
    return authors

def get_author_titles_gutenberg(author_id):
    titles = {}
    resp = get_page(f"https://gutenberg.org/ebooks/author/{author_id}")
    line_iter = io.TextIOWrapper(resp, encoding = "utf-8") 
    seen_titles = {}
    for line in line_iter:
        line = line.strip()
        if line == """<li class="booklink">""":
            line = next(line_iter).strip()
            book_id = line[30:-16]
            for _ in range(4):
                next(line_iter)
            book_title = next(line_iter).strip()[20:-7].replace("\"", "")
            if seen_titles.get(book_title) is None:
                seen_titles[book_title] = True
                titles[book_id] = book_title
    return titles

def get_ebook_txt_gutenberg(book_id):
    resp = get_page(f"https://gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt")
    return resp.read().decode("utf-8")

authors = get_top_100_authors_gutenberg()
titles = { id: get_author_titles_gutenberg(id) for id in authors }

with open(os.path.join(DATA_DIR, "records.csv"), "w") as rf:
    rf.write("author_id,id,title\n")
    for id in titles:
        name = authors[id]
        title_ids = titles[id]
        for title_id in title_ids:
            title = title_ids[title_id]
            print(id, name, title_id, title)
            rf.write(f"{id},{title_id},\"{title}\"\n")
            book_path = os.path.join(RAW_TEXT_DIR, f"{id}_{title_id}.txt")
            if not os.path.exists(book_path):
                book_txt = get_ebook_txt_gutenberg(title_id)
                with open(book_path, "w") as bf:
                    bf.write(book_txt)

with open(os.path.join(DATA_DIR, "authors.csv"), "w") as f:
    f.write("id,name\n")
    for id, name in authors.items():
        title_ids = titles[id]
        f.write(f"{id},\"{name}\"\n")

print(f"Loaded {len(authors)} authors, totaling {sum(len(titles[id]) for id in titles)} books.")