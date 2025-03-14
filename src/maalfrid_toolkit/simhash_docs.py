import numpy as np
import re
import sys
from simhash import Simhash, SimhashIndex
import logging

# FROM: https://leons.im/posts/a-python-implementation-of-simhash-algorithm/
def get_features(s):
    """ Create char trigrams of lowercased, word-like characters """
    width = 3
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

def create_bitstring(n):
    byte_string = n.to_bytes(8, 'big')
    bit_array = list(np.unpackbits(np.frombuffer(byte_string, dtype='>B')))
    bit_string = [str(x) for x in bit_array]
    bit_string = ''.join(bit_string)
    return bit_string

def compute_simhash(fulltext_id, doc):
    try:
        simhash_value = Simhash(get_features(doc)).value
        simhash_value_bit = create_bitstring(simhash_value)
    except:
        simhash_value = None
        simhash_value_bit = None

    return (fulltext_id, simhash_value, simhash_value_bit)

def serialize_simhashes(simhashes):
    """ Serialize simhashes for use with SimhashIndex """
    return [(str(int(item["fulltext_id"])), Simhash(int(item["simhash"]))) for item in simhashes]

def build_index(serialized_simhashes):
    """ Build a simhash index of a set of serialized simhashes """
    # omit warning messages
    logger = logging.getLogger("custom_logger")
    logger.setLevel(logging.ERROR)

    # build Simhash index
    index = SimhashIndex(serialized_simhashes, k=3, log=logger)
    return index

def compare(index, simhash):
    """ Compare a single simhash from the new set with the index based on the old set: If a match is found, return the text id, if not, returning nothing """
    i=index.get_near_dups(simhash[1])
    if i:
        return [simhash[0]]
    else:
        return []

def main():
    with sys.stdin as line:
        text = line.read()
    
    print(compute_simhash("test", text))

if __name__ == "__main__":
    main()
