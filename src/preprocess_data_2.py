import os
import concurrent.futures
import timeit

# probably need to export these as environment variables in a module since I redefine them every script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

RAW_TEXT_DIR = os.path.join(DATA_DIR, "raw")

STAGE_1_PATH = os.path.join(DATA_DIR, "collection_stage_1.csv")
STAGE_2_PATH = os.path.join(DATA_DIR, "collection_stage_2.csv")

# NOTE: parallelizing naturally required books to have their full text loaded into memory as a given time.
# TODO: nltk would be more robust likely, but remark we just need function words. (articles, pronouns, conjunctions, aux verbs, particles, etc.)

def parse_line(line):
    subseq = bytearray()
    term = bytearray()
    for c in line + "\n":
        if c.isascii():
            term.append(ord(c))
        else:
            if term:
                subseq.extend(term)
                subseq.append(32)
                term.clear()
    return subseq

def parse_book(record):
    a_id, t_id = record
    seq = bytearray()
    book_path = os.path.join(RAW_TEXT_DIR, f"{a_id}_{t_id}.txt")
    with open(book_path, "r") as bf:
        reading = False
        for line in bf:
            line = line.strip().lower()
            if "***" in line:
                reading = not reading
            elif reading:
                subseq = parse_line(line)
                seq.extend(subseq)
    return seq.decode("ascii")

def write_stage_2():
    with open(STAGE_2_PATH, "w") as s2f:
        s2f.write("author,book,sequence\n")
        pool = []
        with open(STAGE_1_PATH) as s1f:
            next(s1f)
            for line in s1f:
                info = line.strip().split(",", 1)
                pool.append(info)
        # https://docs.python.org/3/library/concurrent.futures.html
        with concurrent.futures.ProcessPoolExecutor() as exec:
            for (a_id, t_id), seq in zip(pool, exec.map(parse_book, pool)):
                if len(seq) > 1_000: # 1000 character minimum
                    s2f.write(f"{a_id},{t_id},{seq}\n")

def main():
    write_stage_2()
    # test display since opening the file in your IDE will crash it...
    # with open(STAGE_2_PATH, "r") as f:
    #     for l in f:
    #         l = l.strip()
    #         print(l[:200])

# need this guard for ProcessPoolExecutor
if __name__ == "__main__":
    main()