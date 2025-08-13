import random
import os

def generate_unique_id(file, limit=10000, lowerlimit=1):
    """
    Generates unique misperids saving them to a text file and ensuring uniqueness from previously
    generated numbers.
    """
    filename =f"utils/ids/{file}.txt"
    existing_misperids = set()

    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                try:
                    existing_misperids.add(int(line.strip()))
                except ValueError:
                    raise NameError("Something wrong with the misperids file.")
    err_count = 0
    while True:
        misperid = random.randint(lowerlimit, limit)
        if misperid not in existing_misperids:
            existing_misperids.add(misperid)
            with open(filename, "a") as f:
                f.write(str(misperid) + "\n")
            # print(f"Generated unique misperid: {misperid}. Saved to {filename}")
            return misperid
        else:
            
            err_count +=1
            if err_count ==20:
                raise ValueError(f"Timeout in {file}")
            if len(existing_misperids) == limit:
                raise ValueError(f"All possible ids used in {file}")
                print("All possible unique misperids (1-959) have been generated.")
                return None
            print(f"{file} {misperid} already exists. Generating another...")
