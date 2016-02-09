'''
Created on 21-Jan-2016

@author: valmik
'''
import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict
import re
import codecs
import json



def count_tags(filename):
        tags = defaultdict(int)
        for event,elem in ET.iterparse(filename):
            tags[elem.tag] += 1

        return tags


        # YOUR CODE HERE

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]



expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Marg", "Highway","Expressway","Chowk","Path","Lane",
            "Crossroad","Road)","Gali","Marg)","1","1)","10","13","16","19","2","22","26","3","4",
            "5","6","7","8","9","Connector","Extension","Lane)","North","West"]

expected_cities = ["Mumbai","Navi Mumbai","Thane"]

mapping_st_names = { "Chauk": "Chowk","JVLR": "Jogeshwari-Vikhroli Link Road","M.G.Road" : "M.G. Road","Marg," : "Marg",
            "ROAD" : "Road","ROad" : "Road","Raod" : "Road","Rd"   : "Road","Rd."  : "Road","lane" : "Lane","marg" : "Marg",
            "path" : "Path","road" : "Road","street" : "Street","Ext"  : "Extension","No.1" : "No. 1","No.2" : "No. 2",
            "chowk" : "Chowk","galli" : "Gali","l.j.road" : "L.J. Road","no.1" : "No. 1","no.13" : "No. 13","no.3" : "No. 3",
            "road)" : "Road) "}

mapping_countries = { "IN": "India"}

mapping_states = { "MAHARASHTRA": "Maharashtra","MAHARASTRA":"Maharashtra"}

mapping_cities = {'Ambernath':"Thane",'Andheri E':"Mumbai",'Andheri West, Mumbai': "Mumbai",'Andhri East':"Mumbai",'Bhiwandi':"Mumbai",
     'CHEMBUR':"Mumbai",'Chembur, Mumbai':"Mumbai",'Dombivli West':"Thane",'Ghatkopar West, Mumbai':"Mumbai",'KURLA':"Mumbai",
     'Kalamboli':"Navi Mumbai",'Kamothe, navi mumbai':"Navi Mumbai",'Kandivali West':"Mumbai",'Kanjur Marg (E)':"Mumbai",
     'Kashele':"Navi Mumbai",'Kharghar':"Navi Mumbai",'Kurla West, Mumbai':"Mumbai",'Lower Parel Mumbai, Maharashtra':"Mumbai",
     'MULUND (WEST)':"Mumbai",'MUMBAI':"Mumbai",'MUMBAI chembur':"Mumbai",'Malad':"Mumbai",'Malad west':"Mumbai",'Mulind (East)':"Mumbai",
     'Mulond (West)':"Mumbai",'Mulund':"Mumbai",'Mulund (East)':"Mumbai",'Mulund (Weat)':"Mumbai",'Mulund (West)':"Mumbai",'Mulund(West)':"Mumbai",
     'Mumabi':"Mumbai",'Mumbai,Dadar(East)':"Mumbai",'Mumbai,Kurla(East)':"Mumbai",'Mumbi':"Mumbai",'NAVI MUMBAI':"Navi Mumbai",'NITIE PO, Powai, Mumbai':"Mumbai",
     'Panvel':"Navi Mumbai",'Panvel, Navi-Mumbai':"Navi Mumbai",'Powai, Mumbai':"Mumbai",'THANE':"Thane",'Taloja MIDC':"Navi Mumbai",
     'Thane (West)':"Thane",'Thane (west)':"Thane",'Thane West':"Thane",'Vasai':"Mumbai",'Vashi':"Navi Mumbai",'Worli, Mumbai':"Mumbai",
     'bhandup':"Mumbai",'bhiwandi':"Mumbai",'cheedanagar, chembur,mumbai':"Mumbai",'cheeta camp, mumbai':"Mumbai",'chembur':"Mumbai",
     'chembur east':"Mumbai",'ghatkopar':"Mumbai",'k\nKharghar':"Navi Mumbai",'kalwa':"Navi Mumbai",'kamothe navi mumbai':"Navi Mumbai",
     'kamothe, navi mumbai':"Navi Mumbai",'kharghar':"Navi Mumbai",'mUMBAI':"Mumbai",'mumabai':"Mumbai",'mumbai':"Mumbai",'mumbai chembur':"Mumbai",
     'mumbai..':"Mumbai",'navi mumbai':"Navi Mumbai",'thane':"Thane","Kalyan":"Thane"}

street_types = defaultdict(set)
unexpected_post_codes = []
unexpected_countries = set()
unexpected_cities = set()
unexpected_states = set()

# Function to create a json element. This follows the criteria set in data.py from Lesson 6
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node["pos"] = [0,0]
        node["type"] = element.tag
        for attrName, attrValue in element.items():
            if attrName in CREATED:
                if "created" not in node:
                    node["created"] = {}
                node["created"][attrName] = attrValue
            elif attrName == "lat":
                node["pos"][0] = float(attrValue)
            elif attrName == "lon":
                node["pos"][1] = float(attrValue)
            else:
                node[attrName] = attrValue


        for child in element.iter():
            if child.tag == "tag":
                attr_k = child.attrib['k']
                value_v = child.attrib['v']

                # The 5 data points cleaned are audited before entering them in the json element
                if is_street_name(child):
                    value_v = audit_street_type(street_types, value_v)
                elif is_post_code(child):
                    value_v = audit_post_code(unexpected_post_codes,value_v)
                elif is_country(child):
                    value_v = audit_countries(unexpected_countries,value_v)
                elif is_city(child):
                    value_v = audit_cities(unexpected_cities,value_v)
                elif is_state(child):
                    value_v = audit_states(unexpected_states,value_v)



                if problemchars.search(attr_k):
                    pass
                elif attr_k.count(':') > 1:
                    pass
                elif attr_k.startswith("addr:"):
                    if "address" not in node:
                        node["address"] = {}
                    node["address"][attr_k[5:]] = value_v
                else:
                    node[attr_k] = value_v

        if element.tag == "way":
            for child in element.iter():
                if child.tag == "nd":
                    if "node_refs" not in node:
                        node["node_refs"] = []
                    node["node_refs"].append(child.attrib['ref'])
        return node
    else:
        return None


# Function to write to json file
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




# Function to audit street name
def audit_street_type(street_types, street_name):

    # Extracting string before comma if comma exists
    try:
        index = street_name.index(',')
    except ValueError:
        index = len(street_name)
    street_name = street_name[:index]
    street_name = update_st_name(street_name,mapping_st_names)

    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            return ""
        else:
            return street_name

# Function to audit postal code
def audit_post_code(unexpected_post_codes, post_code):

    # Extracting string before comma if comma exists
    try:
        index = post_code.index(',')
    except ValueError:
        index = len(post_code)
    post_code = post_code[:index]

    # Extracting string before dot if dot exists
    try:
        index = post_code.index('.')
    except ValueError:
        index = len(post_code)
    post_code = post_code[:index]

    # Removing space from the postal code
    post_code = post_code.replace(' ', '')

    if len(post_code) != 6:
        unexpected_post_codes.append(post_code)
        return ""
    elif post_code[:3] not in ["400","401","410","421"]:
        unexpected_post_codes.append(post_code)
        return ""
    else:
        return post_code

# Function to audit country name
def audit_countries(unexpected_countries, country):

    if country in mapping_countries.keys():
        country = mapping_countries[country]
    if country != "India":
        unexpected_countries.add(country)
        return ""
    else:
        return country

# Function to audit city name
def audit_cities(unexpected_cities, city):
    if city in mapping_cities.keys():
        city = mapping_cities[city]
    if city not in expected_cities:
        unexpected_cities.add(city)
        return ""
    else:
        return city

# Function to audit state name
def audit_states(unexpected_states, state):
    if state in mapping_states.keys():
        state = mapping_states[state]
    if state != "Maharashtra":
        unexpected_states.add(state)
        return ""
    else:
        return state


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_post_code(elem):
    return (elem.attrib['k'] == "addr:postcode")

def is_country(elem):
    return (elem.attrib['k'] == "addr:country")

def is_city(elem):
    return (elem.attrib['k'] == "addr:city")

def is_state(elem):
    return elem.attrib['k'] == "addr:state"


#Function to update the street name to the correct one
def update_st_name(name, mapping):
    m = street_type_re.search(name)
    if m:
        if m.group() in mapping_st_names.keys():
            name = street_type_re.sub(mapping_st_names[m.group()],name)
    return name


def test():

    #tags = count_tags('mumbai_india.osm')
    #pprint.pprint(tags)
    #pprint.pprint(dict(st_types))
    data = process_map('mumbai_india.osm', True)


if __name__ == "__main__":
    test()
