import re
def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def loadMap(file_name):
    with open(file_name) as f:
        entities = f.read().split('\n')
    entities = [e.split('\t') for e in entities]
    entities = [e for e in entities if len(e) > 1]
    
    map_ = {}
    for pair in entities:
        map_[cleanhtml(pair[0])] = cleanhtml(pair[1])
        
    return map_
        
el_vi = loadMap('resources/lower_vi_syns.txt')   
el_map_variants = {}
r_vi = {}

for e in el_vi:
    el_map_variants[e] = set([])
    el_map_variants[el_vi[e]] = set([])
    if el_vi[e] not in r_vi:
        r_vi[el_vi[e]] = [e]
    else:
        r_vi[el_vi[e]].append(e)
        
for e in el_vi:
    entity = e
    o_entity = el_vi[e]

    el_map_variants[entity].add(o_entity)
    el_map_variants[o_entity].add(entity)

    if entity in r_vi:
        el_map_variants[entity] = el_map_variants[entity].union(set(r_vi[entity]))
        el_map_variants[o_entity] = el_map_variants[o_entity].union(set(r_vi[entity]))

    if o_entity in r_vi:
        el_map_variants[entity] = el_map_variants[entity].union(set(r_vi[o_entity]))
        el_map_variants[o_entity] = el_map_variants[o_entity].union(set(r_vi[o_entity]))

del r_vi
    
def getVariants(entity):
    try:
        if type(entity) == str:
            entity = entity

        entity = entity.replace('_',' ').lower()

        variants = [entity]

        if entity in el_map_variants:
            variants = list(el_map_variants[entity])

        variants = [v for v in variants]
        return variants
    except:
        return entity
    
def extractEntVariants(entity):
    variants = getVariants(entity)
    variants.append(entity)
    variants = list(set(variants))
    return variants