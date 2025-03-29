
import os
import heapq

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

RAW_TEXT_DIR = os.path.join(DATA_DIR, "raw")

RECORDS_PATH = os.path.join(DATA_DIR, "records.csv")
AUTHORS_PATH = os.path.join(DATA_DIR, "authors.csv")

def load_authors():
    authors = {}
    with open(AUTHORS_PATH, "r") as f:
        next(f)
        for line in f:
            id, name = line.strip().split(",", 1)
            authors[id] = { "name": name[1:-1], "titles": {} }
    with open(RECORDS_PATH, "r") as f:
        next(f)
        for line in f:
            author_id, id, title = line.strip().split(",", 2)
            authors[author_id]["titles"][id] = title[1:-1]
    return authors

# def load_book(author_id, id):
#     with open()

def has_at_least_two_books(info):
    return len(info["titles"]) >= 2

# first pass heuristic before scanning entire collection to minimize memory load of trying to load all book's full text
def is_likely_english_title(title):
    title = title.lower()
    if title == "":
        return False
    # TODO: some english titles have non-ascii characters in them. 
    # if not title.isascii():
    #     return False
    # TODO: some titles may simply be talking about the language with "(language)"
    languages = [
        "hungarian", "french", "german", "finnish",
        "dutch", "portuguese", "russian", "latin",
        "spanish", "esperanto", "polish", "italian",
        "tagalog", "czech"
    ]
    for lang in languages:
        if f"({lang})" in title:
            return False
    return True

# gutenberg appends "Language: ..." to top of many books
# TODO: look at frequency of english stop words in text. might be slow?
def is_likely_english_book(text):
    return "Language: English" in text

# TODO: nltk
# strips first 500 characters
# avg english word is 5 letters, should be 1 space between each word, so expect 1000*(5+1) characters
# TODO: we can check how many bytes the file is with os.path.getsize, so we need to do some analysis to find the avg character(or word) to byte ratio
def is_likely_long_text(raw_book_text):
    return len(raw_book_text) >= 1000 * (5 + 1) 

def load_book_head(author_id, id):
    book_path = os.path.join(RAW_TEXT_DIR, f"{author_id}_{id}.txt")
    with open(book_path, "r") as f:
        return f.read(5 * 2_000)
    

# TODO: nltk would provide more robust word id'ing and provide stemming + more lexical features, just be mindful of the time complexity
def top_n_terms_by_freq(text, n):
    tf = {}
    term = ""
    for c in text.lower() + "\n":
        if c.isalpha():
            term += c
        else:
            if term != "":
                tf[term] = tf.get(term, 0) + 1
            term = ""
    # https://docs.python.org/3/library/heapq.html#basic-examples
    return heapq.nlargest(n, tf.items(), key = lambda x: x[1])

# 1. title fails if it is not likely english (TODO: )
# 2. title fails if raw text likely does not have 1000 words (TODO: ntlk for more robust approach)
# 3. TODO: check other titles from author to see if dataset has same book under another title (SLOW...)
def filter_titles(author_id, titles):
    ok_titles = {}
    for id, name in titles.items():
        if not is_likely_english_title(name):
            continue
        text = load_book_head(author_id, id)
        if not is_likely_english_book(text):
            continue
        if not is_likely_long_text(text):
            continue
        top = [ t for (t, f) in top_n_terms_by_freq(text, 10) ]
        if not "the" in top: # most common word in english
            continue
        ok_titles[id] = { "name": name, "head": text}#, "top": top_n_terms_by_freq(text, 100) }
    # TODO: create doc similarity index /w number of shared top_n terms weighted by inverse of absolute difference of freq of each top term  
    return ok_titles

# 1. remove books with likely non english title
# 2. remove books with likely non english body
# TODO: 3. remove books with high content similarity to other books, but keep one
# 4. remove authors with less than two books left
# TODO: 5. remove authors with less than 1000 total words left
def filter_authors_by_heuristics():
    ok_authors = {}
    authors = load_authors()
    for id, info in authors.items():
        info["titles"] = filter_titles(id, info["titles"])

        if not has_at_least_two_books(info):
            continue
        ok_authors[id] = info


        # print(id, info["name"])
    return ok_authors

# tf = top_n_term_freq(". At first\nhe sits there in the dust, with his little chubby hands reaching at\nnothing, and his little solemn eyes staring into space. As soon as he\ncan toddle, he moves, by the queer instinct we call the love of life,\nstraight along this road, looking neither to the right nor left, so\npleased is he to walk. And he is charmed with everything--with the nice\nflat road, all broad and white, with his own feet, and with the prospect\nhe can see on either hand. The sun shines, and he finds the road a\nlittle hot and dusty", 10)
# print(tf)

# TODO: i anticipate the preprocessing of the data is best broke up into several "stage" files to make exploration easier.

# author_id, book_id
with open(os.path.join(DATA_DIR, "collection_stage_1.csv"), "w") as f:
    f.write("author,book\n")
    ok_authors = filter_authors_by_heuristics()
    for id, info in ok_authors.items():
        # titles = ",".join(list(info["titles"].keys()))
        for t_id in info["titles"]:
            f.write(f"{id},{t_id}\n")

# TODO: stage 2 involves actually cleaning up the raw data to be parsed
# 1. remove gutenberg text header
# 2. more robust search for non-english books

# TODO: stage 3 involves feature extraction = selecting stopwords/function words since (hypothetically) represent they author's style.


# # print(ok_authors)