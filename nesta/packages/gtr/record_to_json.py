#!/usr/bin/env python3

import pickle
import json
import sys

from get_gtr_data import TypeDict


in_file = sys.argv[1]

with open(in_file, 'rb') as fp:
    p = pickle.load(fp)
print(json.dumps(p))
