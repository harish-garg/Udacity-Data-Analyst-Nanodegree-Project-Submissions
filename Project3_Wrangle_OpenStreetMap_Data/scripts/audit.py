"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
    You have to add mappings only for the actual problems you find in this OSMFILE,
    not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
    We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

# data file
full_data = "/home/harish/datasets/bengaluru_india.osm" 
sample_medium = "/home/harish/datasets/sampleK10.osm"
sample_small = "sampleK100.osm"
south = "/home/harish/datasets/ex_hz6cRB8dF5qcLXwsWPkDFp4KQKf28.osm"
OSMFILE = south


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square",
            "Lane", "Road", "Trail", "Parkway", "Commons", "Colony", "Homes", 
            "Circle", "Layout", "Nagar", "Stage", "Town", "Zone", "Cross", "Main", "East", "Village", "Whitefield", "Vijayanagar", "18th", "Bangalore", "Mall", "Labs", "Indiranagar", "Karnataka", "Malleswaram"]

# UPDATE THIS VARIABLE
mapping = { "ROad": "Road",
            "road": "Road",
            "stage": "Stage",
            "cross": "Cross",
            "main": "Main",
            "street": "Street",
            "vijayanagar": "Vijayanagar",
            "road\)": "Road",
            "Colony\)": "Colony",
            "Road\)": "Road"
            }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


postal_codes = re.compile(r'^56[0-9][0-9][0-9][0-9]')
bad_postal_codes = []

def audit_postal_code(postal_code):
    if postal_codes.match(postal_code):
        return postal_code

    bad_postal_codes.append(postal_code)
    return postal_code


def is_postal_code(address_key):
    return address_key == 'addr:postcode'

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


def update_name(name, mapping):

    # YOUR CODE HERE
    for key in mapping.iterkeys():
        if re.search(key, name):
            name = re.sub(key, mapping[key], name)

    return name
    




def test():
    st_types = audit(OSMFILE)
    #assert len(st_types) == 3
    pprint.pprint(dict(st_types))

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping)
            print name, "=>", better_name
            """
            if name == "West Lexington St.":
                assert better_name == "West Lexington Street"
            if name == "Baldwin Rd.":
                assert better_name == "Baldwin Road"
            """

if __name__ == '__main__':
    test()
