#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
from collections import defaultdict
"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if the second level tag "k" value contains problematic characters, it should be ignored
- if the second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if the second level tag "k" value does not start with "addr:", but contains ":", you can
  process it in a way that you feel is best. For example, you might split it into a two-level
  dictionary like with "addr:", or otherwise convert the ":" to create a valid key.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""
# data file
full_data = "/home/harish/datasets/bengaluru_india.osm" 
sample_medium = "/home/harish/datasets/sampleK10.osm"
sample_small = "sampleK100.osm"
south = "/home/harish/datasets/ex_hz6cRB8dF5qcLXwsWPkDFp4KQKf28.osm"
OSMFILE = south

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
postal_codes = re.compile(r'^56[0-9][0-9][0-9][0-9]')
street_types_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
ATTRIB = ["id", "visible", "amenity", "cuisine", "name", "phone"]

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square",
            "Lane", "Road", "Trail", "Parkway", "Commons", "Colony", "Homes", 
            "Circle", "Layout", "Nagar", "Stage", "Town"]

street_mapping = { "ROad": "Road",
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

building_mapping = {
            u"гэр": "hut",
            "ger": "hut",
            "tent": "hut",
            "yurt": "hut",
            "ger.": "hut",
            "baishin": "house",
            }

postal_code_range = [560000,560099]
postal_code_default = 560000

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def audit_postal_code(invalid_postal_codes, postal_code):
    try:
        if not (postal_code_range[0] <= int(postal_code) <= postal_code_range[1]):
            raise ValueError
    except ValueError:
        invalid_postal_codes[postal_code] += 1

def audit_phone_number(invalid_phone_numbers, phone_number):
    try:
        if len(phone_number) != 12 or phone_number[:3] != '+976':
            raise ValueError
    except ValueError:
        invalid_phone_numbers[phone_number] += 1

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_postal_code(elem):
    return (elem.attrib['k'] == "addr:postcode")

def is_phone_number(elem):
    return (elem.attrib['k'] == "phone")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    invalid_postal_codes = defaultdict(int)
    invalid_phone_numbers = defaultdict(int)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                elif is_postal_code(tag):
                    audit_postal_code(invalid_postal_codes, tag.attrib['v'])
                elif is_phone_number(tag):
                    audit_phone_number(invalid_phone_numbers, tag.attrib['v'])

    return [invalid_postal_codes, invalid_phone_numbers, street_types]

#standardizes street types with a replacement map
def update_name(name, mapping):
    name = name.split(' ')
    type = name[-1]
    if type in mapping:
        name[-1] = mapping[type]
    
    name = ' '.join(name)
    name = name.title()

    return name

#checks if postal code within valid range, if not replaces with 11000 default
def update_postal_code(postal_code):
    try:
        if not (postal_code_range[0] <= int(postal_code) <= postal_code_range[1]):
            raise ValueError
        else:
            return int(postal_code)
    except ValueError:
        return postal_code_default

#standardizes phone number formatting
def update_phone_number(phone_number):
    phone_number = phone_number.translate(None, ' ()-')
    phone_number = '+976 11 ' + phone_number[-6:]
    return phone_number

#converts building types to lowercase, standardizes with a replacement map
def update_building_type(building_type, mapping):
    building_type = building_type.lower()

    if building_type in mapping:
        building_type = mapping[building_type]

    return building_type

def shape_element(e):
    node = {}
    node['created'] = {}
    node['pos'] = [0,0]
    if e.tag == "way":
        node['node_refs'] = []
    if e.tag == "node" or e.tag == "way" :
        node['type'] = e.tag
        #attributes
        for k, v in e.attrib.iteritems():
            #latitude
            if k == 'lat':
                try:
                    lat = float(v)
                    node['pos'][0] = lat
                except ValueError:
                    pass
            #longitude
            elif k == 'lon':
                try:
                    lon = float(v)
                    node['pos'][1] = lon
                except ValueError:
                    pass
            #creation metadata
            elif k in CREATED:
                node['created'][k] = v
            else:
                node[k] = v
        #children
        for tag in e.iter('tag'):
            k = tag.attrib['k']
            v = tag.attrib['v']
            if problemchars.match(k):
                continue
            elif lower_colon.match(k):
                k_split = k.split(':')
                #address fields
                if k_split[0] == 'addr':
                    k_item = k_split[1]
                    if 'address' not in node:
                        node['address'] = {}
                    #streets
                    if k_item == 'street':
                        v = update_name(v, street_mapping)                    
                    #postal codes
                    if k_item == 'postcode':
                        v = update_postal_code(v)
                    node['address'][k_item] = v
                    continue
            else:                
                #phone numbers
                #if(is_phone_number(tag)):
                #    v = update_phone_number(v)
                #buildings
                #if k == 'building':
                #    v = update_building_type(v, building_mapping)
            node[k] = v
        #way children
        if e.tag == "way":
            for n in e.iter('nd'):
                ref = n.attrib['ref']
                node['node_refs'].append(ref);
        return node
    else:
        return None

def process_map(file_in, pretty = False):
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def audit_report():
    audit_data = audit(OSMFILE)
    pprint.pprint(audit_data[0])
    pprint.pprint(audit_data[1])
    pprint.pprint(dict(audit_data[2]))

'''
PRINT OUT AUDIT REPORT
'''
#audit_report()

'''
PROCESS DATA AND OUTPUT JSON
'''
process_map(OSMFILE, False)
