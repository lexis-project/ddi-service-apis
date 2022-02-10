import pdb
import re

def checkAgainstList (query, meta):
    for e in meta:
          if checkCustom(query, e):
                 return True
    return False         

def checkCustom (query, meta):
    #pdb.set_trace()
    if isinstance(meta, list) and not isinstance(query, list): 
       return checkAgainstList (query, meta)

    if type(query) is str:
        if type(meta) is dict:
           return False
        return re.search (query, str(meta), re.IGNORECASE)

    if type(query) is dict: #check all fields
      if type(meta) is not dict:
         return False
      allmatch = True
      for k in query.keys():
        sq = query[k]
        try:
           sm = meta[k]
        except KeyError: 
           return False
        if not checkCustom (sq, sm):
           allmatch=False
      return allmatch
    
    if isinstance(query, list):
       for e in query:
           if not checkCustom (e, meta):
              return False
       return True
    # some other type such as int, transform into string aond continue
    return checkCustom (str(query), meta)

""" 
#pdb.set_trace()
print (True==checkCustom({"a":"b"},  
      {"a":["b", "c"]})    
)
print (True==checkCustom({"a":"b"},
      {"a":"b"})
)
print (True==checkCustom({"a":["b", "c"]},
      {"a":["b", "c"]})
)
print (True==checkCustom({"a":["b", "c"]},
      {"a":["b", "c", "d"]})
)
print (False==checkCustom({"a":[{"b":"c"}]},
      {"a":["b", "c", "d"]})
)
print (True==checkCustom({"a":[{"b":"c"}]},
      {"a":[{"b": "c"}, "d"]})
)
print (True==checkCustom([1,2], 
        [[1,3], [2,4]])
)
print (True==checkCustom([1,2], 
        [[1,2,3], [4,5]])
) 
"""
