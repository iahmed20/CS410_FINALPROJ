import os

# probably need to export these as environment variables in a module since I redefine them every script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

RAW_TEXT_DIR = os.path.join(DATA_DIR, "raw")

STAGE_1_PATH = os.path.join(DATA_DIR, "collection_stage_1.csv")
STAGE_2_PATH = os.path.join(DATA_DIR, "collection_stage_2.csv")

# idea is to read each book line by line but never load the entire text into memory at once
# TODO: cleanup + parallelize (python not very good for this because of the global interpreter lock's mutex on io operations iirc)
# TODO: nltk would be more robust likely, but remark we just need function words. (articles, pronouns, conjunctions, aux verbs, particles, etc.)

with open(STAGE_2_PATH, "w") as s2f:
    s2f.write("author,book,sequence\n")
    with open(STAGE_1_PATH) as s1f:
        next(s1f)
        for line in s1f:
            (a_id, t_id) = line.strip().split(",", 1)
            book_path = os.path.join(RAW_TEXT_DIR, f"{a_id}_{t_id}.txt")
            s2f.write(f"{a_id},{t_id},")
            print(book_path)
            with open(book_path, "r") as bf:
                reading = False
                for line in bf:
                    line = line.strip().lower()
                    if "***" in line:
                        reading = not reading
                    elif reading:
                        term = ""
                        for c in line + "\n":
                            if c.isalpha():
                                term += c
                            else:
                                if term != "":
                                    s2f.write(term + " ")
                                term = ""