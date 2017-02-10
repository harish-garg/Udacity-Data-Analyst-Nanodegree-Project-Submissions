#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
"""
Your task is to explore the data a bit more.
The first task is a fun one - find out how many unique users
have contributed to the map in this particular area!

The function process_map should return a set of unique user IDs ("uid")
"""
full_data = "/home/harish/datasets/bengaluru_india.osm" 
sample_medium = "/home/harish/datasets/sampleK10.osm"
sample_small = "sampleK100.osm"
south = "/home/harish/datasets/ex_hz6cRB8dF5qcLXwsWPkDFp4KQKf28.osm"
OSMFILE = sample_medium

def get_user(element):
    return


def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        try:
            users.add(element.attrib['uid'])
        except KeyError: # for when there is no uid
            continue

    return users


def test():

    users = process_map(OSMFILE)
    pprint.pprint(users)
    pprint.pprint(len(users))
    #assert len(users) == 6



if __name__ == "__main__":
    test()
