import json
import argparse

# -- GET SCHEMA INFO: PREVIOUS DB INFO --

# get added/deleted/renamed models
f = open("db1/drfields/drmodels.txt", "r")
lines = []
for x in f:
    lines.append(x[:-1])
f.close()

drmodels1 = {}
c=0
while c < len(lines)-1:
    drmodel = lines[c]
    func = lines[c+1]
    drmodels1[drmodel] = func
    c+=2

f = open("db1/drfields/models.txt", "r")
models1 = []
for x in f:
    models1.append(x[:-1])
f.close()

# get current existing fields (queries referring to these fields are not errors)
f = open("db1/drfields/fields.txt", "r")
fields1 = []
for x in f:
    fields1.append(x[:-1])
f.close()

# get fields that have been deleted or renamed (fields that have been affected by deleted/renamed models also included)
f = open("db1/drfields/drfields.txt", "r")
lines = []
for x in f:
    lines.append(x[:-1])
f.close()

drfields1 = {}
c=0
while c < len(lines)-1:
    drfield = lines[c]
    func = lines[c+1]
    if "delete model" in func or "rename model" in func:
        if drfield[:drfield.index(" ")] in models1:
            func = "remove field remove {}".format(drfield[drfield.index(" ")+1:])
    drfields1[drfield] = func
    c+=2

# -- ASSOC RELATIONSHIPS -- 

# get association relationships
f = open("db1/assoc/assoc.txt", "r")
assocs_lines = []
for x in f:
    assocs_lines.append(x[:-1])
f.close()

assocs = {}
c=0
while c < (len(assocs_lines)):
    a = assocs_lines[c]
    if a not in assocs:
        assocs[a] = {"ar": [],
                     "ih": []}
    if a[:3] != "-- " and a[:3] != "--ih ":
        c2 = c+1
        while c2 < len(assocs_lines) and (assocs_lines[c2][:3] == "-- " or assocs_lines[c2][:5] == "--ih "):
            if assocs_lines[c2][:3] == "-- ":
                assocs[a]["ar"].append(assocs_lines[c2][3:])
            elif assocs_lines[c2][:5] == "--ih ":
                assocs[a]["ih"].append(assocs_lines[c2][5:])
            c2+=1
    c=c2

# get queries from assoc rels that should be deleted as result of deleted/renamed fields
for assoc in assocs:
    a = assocs[assoc]["ar"][-1]
    if assoc not in fields1 and assoc in drfields1:
        if "remove field" in drfields1[assoc] or "delete model" in drfields1[assoc]:
            for i in assocs[assoc]["ih"]:
                if "delete model" in drfields1[assoc]:
                    drfields1[i] = drfields1[assoc]
                else:
                    drfields1[i] = "remove field remove {}".format(i[i.index(" ")+1:])
            drfields1[a] = "remove field remove {}".format(a[a.index(" ")+1:])
        elif "rename model" in drfields1[assoc]:
            for i in assocs[assoc]["ih"]:
                drfields1[i] = drfields1[assoc]
    elif a[:(a.index(" "))] in drmodels1:
        drfields1[a] = drmodels1[a[:(a.index(" "))]]
        if "delete" in drmodels1[a[:(a.index(" "))]]:
            for i in assocs[assoc]["ih"]:
                drfields1[i] = "remove field remove {}".format(i[i.index(" ")+1:])
            drfields1[assoc] = "remove field remove {}".format(assoc[assoc.index(" ")+1:])
    else:
        fields1.append(a)
        for i in assocs[assoc]["ih"]:
            fields1.append(i)

# when assoc relationship changes --> AlterField or Remove Field then Add Field situation
for assoc in assocs:
    ars = assocs[assoc]["ar"]
    if len(ars) > 2:
        curr = ars[-2]
        new = ars[-1]
        change_assoc_1 = curr[:curr.index(" ")]
        change_assoc_2  = new[:new.index(" ")]
        rename_rel_1 = curr[curr.index(" ")+1:]
        rename_rel_2 = new[new.index(" ")+1:]
        if change_assoc_1 == change_assoc_2 and rename_rel_1 != rename_rel_2:
            drfields1[curr] = "rename field {} to {}".format(rename_rel_1, rename_rel_2)
        elif change_assoc_1 != change_assoc_2:
            drfields1[curr] = "remove field remove {}".format(curr[len(change_assoc_1)+1:])

# check for del fields with somefield_id that were replaced with foreign keys
for f in drfields1:
    model_name = f[:f.index(" ")]
    field = f[f.index(" ")+1:]
    if "_id" in field:
        for a in assocs:
            if "{} {}".format(model_name, field[:field.index("_")]) == a:
                fields1.append(f)

# -- GET TYPE CHANGE -- 
f = open("db1/type/output.txt", "r")
lines = []
for x in f:
    lines.append(x[:-1])
f.close()

types1 = {}
c=0
while c < len(lines)-1:
    field = lines[c]
    notation = lines[c+1]
    types1[field] = notation
    c+=2

#--- GET INDEXES ---

f = open("db1/drfields/indexes.txt", "r")
lines = []
for x in f:
    if "-" in x:
        lines.append(x.replace('-', '')[:-1])
    else:
        lines.append(x[:-1])
f.close()

indexes1 = {}
c=0
while c < len(lines)-1:
    index = lines[c]
    notation = lines[c+1]
    indexes1[index] = notation
    c+=2

# -- ASSOCIATION TYPE CHANGE --
f = open("db1/assoc/assoc-type.txt", "r")
lines = []
for x in f:
    lines.append(x[:-1])
f.close()

assoctypes_buffer = {}
c=0
while c < len(lines)-1:
    if lines[c] in assoctypes_buffer:
        assoctypes_buffer[lines[c]].append(lines[c+1])
    else:
        assoctypes_buffer[lines[c]] = [lines[c+1]]
    c+=2
assoctypes1 = {}
for assoctype in assoctypes_buffer:
    rel = assoctypes_buffer[assoctype]
    if len(rel) > 2 and rel[-2] != rel[-1]:
        # can change
        if rel[-2] == "ManyToManyField":
            assoctypes1[assoctype] = "assoc change association relationship changed from {} to {}: array to single value".format(rel[-2], rel[-1])
        elif rel[-1] == "ManyToManyField":
            assoctypes1[assoctype] = "assoc change association relationship changed from {} to {}: single value to array".format(rel[-2], rel[-1])
        else:
            assoctypes1[assoctype] = "assoc change association relationship changed from {} to {}".format(rel[-2], rel[-1])

# -- GET SCHEMA INFO: CURRENT DB INFO --

# get added/deleted/renamed models
f = open("db2/drfields/drmodels.txt", "r")
lines = []
for x in f:
    lines.append(x[:-1])
f.close()

drmodels2 = {}
c=0
while c < len(lines)-1:
    drmodel = lines[c]
    func = lines[c+1]
    drmodels2[drmodel] = func
    c+=2

f = open("db2/drfields/models.txt", "r")
models2 = []
for x in f:
    models2.append(x[:-1])
f.close()

# get current existing fields (queries referring to these fields are not errors)
f = open("db2/drfields/fields.txt", "r")
fields2 = []
for x in f:
    fields2.append(x[:-1])
f.close()

# get fields that have been deleted or renamed (fields that have been affected by deleted/renamed models also included)
f = open("db2/drfields/drfields.txt", "r")
lines = []
for x in f:
    lines.append(x[:-1])
f.close()

drfields2 = {}
c=0
while c < len(lines)-1:
    drfield = lines[c]
    func = lines[c+1]
    if "delete model" in func or "rename model" in func:
        if drfield[:drfield.index(" ")] in models2:
            func = "remove field remove {}".format(drfield[drfield.index(" ")+1:])
    drfields2[drfield] = func
    c+=2

# -- ASSOC RELATIONSHIPS -- 

# get association relationships
f = open("db2/assoc/assoc.txt", "r")
assocs_lines = []
for x in f:
    assocs_lines.append(x[:-1])
f.close()

assocs = {}
c=0
while c < (len(assocs_lines)):
    a = assocs_lines[c]
    if a not in assocs:
        assocs[a] = {"ar": [],
                     "ih": []}
    if a[:3] != "-- ":
        c2 = c+1
        while c2 < len(assocs_lines) and (assocs_lines[c2][:3] == "-- " or assocs_lines[c2][:5] == "--ih "):
            if assocs_lines[c2][:3] == "-- ":
                assocs[a]["ar"].append(assocs_lines[c2][3:])
            elif assocs_lines[c2][:5] == "--ih ":
                assocs[a]["ih"].append(assocs_lines[c2][5:])
            c2+=1
    c=c2

# get queries from assoc rels that should be deleted as result of deleted/renamed fields
for assoc in assocs:
    a = assocs[assoc]["ar"][-1]
    if assoc not in fields2 and assoc in drfields2:
        if "remove field" in drfields2[assoc] or "delete model" in drfields2[assoc]:
            for i in assocs[assoc]["ih"]:
                if "delete model" in drfields2[assoc]:
                    drfields2[i] = drfields2[assoc]
                else:
                    drfields2[i] = "remove field remove {}".format(i[i.index(" ")+1:])
            drfields2[a] = "remove field remove {}".format(a[a.index(" ")+1:])
        elif "rename model" in drfields2[assoc]:
            for i in assocs[assoc]["ih"]:
                drfields2[i] = drfields2[assoc]
    elif a[:(a.index(" "))] in drmodels2:
        drfields2[a] = drmodels2[a[:(a.index(" "))]]
        if "delete" in drmodels2[a[:(a.index(" "))]]:
            for i in assocs[assoc]["ih"]:
                drfields2[i] = "remove field remove {}".format(i[i.index(" ")+1:])
            drfields2[assoc] = "remove field remove {}".format(assoc[assoc.index(" ")+1:])
    else:
        fields2.append(a)
        for i in assocs[assoc]["ih"]:
            fields2.append(i)

# when assoc relationship changes --> AlterField or Remove Field then Add Field situation
for assoc in assocs:
    ars = assocs[assoc]["ar"]
    if len(ars) > 2:
        curr = ars[-2]
        new = ars[-1]
        change_assoc_1 = curr[:curr.index(" ")]
        change_assoc_2  = new[:new.index(" ")]
        rename_rel_1 = curr[curr.index(" ")+1:]
        rename_rel_2 = new[new.index(" ")+1:]
        if change_assoc_1 == change_assoc_2 and rename_rel_1 != rename_rel_2:
            drfields2[curr] = "rename field {} to {}".format(rename_rel_1, rename_rel_2)
        elif change_assoc_1 != change_assoc_2:
            drfields2[curr] = "remove field remove {}".format(curr[len(change_assoc_1)+1:])

# check for del fields with somefield_id that were replaced with foreign keys
# check onlinejudge _id issue
for f in drfields2:
    model_name = f[:f.index(" ")]
    field = f[f.index(" ")+1:]
    if "_id" in field:
        for a in assocs:
            if "{} {}".format(model_name, field[:field.index("_")]) == a:
                fields2.append(f)

# -- GET TYPE CHANGE -- 
f = open("db2/type/output.txt", "r")
lines = []
for x in f:
    lines.append(x[:-1])
f.close()

types2 = {}
c=0
while c < len(lines)-1:
    field = lines[c]
    notation = lines[c+1]
    types2[field] = notation
    c+=2

#--- GET INDEXES ---

f = open("db2/drfields/indexes.txt", "r")
lines = []
for x in f:
    if "-" in x:
        lines.append(x.replace('-', '')[:-1])
    else:
        lines.append(x[:-1])
f.close()

indexes2 = {}
c=0
while c < len(lines)-1:
    index = lines[c]
    notation = lines[c+1]
    indexes2[index] = notation
    c+=2

# -- ASSOCIATION TYPE CHANGE --
f = open("db2/assoc/assoc-type.txt", "r")
lines = []
for x in f:
    lines.append(x[:-1])
f.close()

assoctypes_buffer = {}
c=0
while c < len(lines)-1:
    if lines[c] in assoctypes_buffer:
        assoctypes_buffer[lines[c]].append(lines[c+1])
    else:
        assoctypes_buffer[lines[c]] = [lines[c+1]]
    c+=2
assoctypes2 = {}
for assoctype in assoctypes_buffer:
    rel = assoctypes_buffer[assoctype]
    if len(rel) > 2 and rel[-2] != rel[-1]:
        # can change
        if rel[-2] == "ManyToManyField":
            assoctypes2[assoctype] = "assoc change association relationship changed from {} to {}: array to single value".format(rel[-2], rel[-1])
        elif rel[-1] == "ManyToManyField":
            assoctypes2[assoctype] = "assoc change association relationship changed from {} to {}: single value to array".format(rel[-2], rel[-1])
        else:
            assoctypes2[assoctype] = "assoc change association relationship changed from {} to {}".format(rel[-2], rel[-1])

# -- PROPERTY DECORATOR --
f = open("queries/property.txt", "r")
property = []
for x in f:
    property.append(x[:-1])
f.close()

# -- SCHEMA DIFFERENCES BETWEEN PREVIOUS AND CURRENT VERSION OF APP --
final_drfields1 = []
for drfield in drfields1:
    if drfield not in fields1:
        final_drfields1.append(drfield)

final_drfields2 = []
for drfield in drfields2:
    if drfield not in fields2:
        final_drfields2.append(drfield)

final_db = {}
for drfield in final_drfields2:
    if drfield not in final_drfields1 and drfield not in property:
        final_db[drfield] = drfields2[drfield]

final_drmodels1 = []
for drmodel in drmodels1:
    if drmodel not in models1:
        final_drmodels1.append(drmodel)

final_drmodels2 = []
for drmodel in drmodels2:
    if drmodel not in models2:
        final_drmodels2.append(drmodel)

final_drmodels = {}
for drmodel in final_drmodels2:
    if drmodel not in final_drmodels1:
        final_drmodels[drmodel] = drmodels2[drmodel]

final_assoctypes = {}
for assoctype in assoctypes2:
    if assoctype not in assoctypes1:
        final_assoctypes[assoctype] = assoctypes2[assoctype]

final_types = {}
for type in types2:
    if type not in types1:
        final_types[type] = types2[type]

final_indexes = {}
for index in indexes2:
    if index not in indexes1:
        final_indexes[index] = indexes2[index]

#--- GET QUERIES ---

# get raw data from file first
f = open("queries/query-output.txt", "r")
lines = []
for x in f:
    if "/" not in x and "-" in x:
        lines.append(x.replace('-', '')[:-1])
    else:
        lines.append(x[:-1])
f.close()

# put queries in according files 
files = {}
c=0
while c < len(lines):
    curr = lines[c]
    if ".py" in curr:
        c2 = c+1
        while c2 < len(lines) and ".py" not in lines[c2]:
            c2+=1
        files[curr] = lines[(c+1):c2]
    c=c2

# put queries in dictionary for lineno, colno
for fi in files:
    qs = {}
    file_queries = files[fi]
    c=0
    while c < len(file_queries)-1:
        query = file_queries[c]
        logistics = file_queries[c+1]
        if query in qs:
            qs[query].append(logistics)
        else:
            qs[query] = [logistics]
        c+=2
    files[fi] = qs

# -- CHECK --
def changetype_convert(s):
    if s == "remove field":
        return "column delete"
    elif s == "rename field":
        return "column rename"
    elif s == "rename model":
        return "table rename"
    else:
        return s

def patch_type(func):
    if func[:12] == "rename field":
        lst = func.split()
        new_field = lst[-1]
        ren = new_field[new_field.index(".")+1:]
        return ren
    elif func[:12] == "rename model":
        lst = func.split()
        ren = lst[-1]
        return ren
    else:
        return func[13:]

def jsonconvert(logistics, func):
    position = {
                    "start": {},
                    "end": {}
                }
    if func[:12] in ["rename field", "create index", "remove index"] and "7:**" not in logistics:
        position["start"]["line"] = int(logistics[logistics.index("5:")+2:logistics.index("6:")-1])
        position["start"]["column"] = int(logistics[logistics.index("6:")+2:logistics.index("7:")-1])
        position["end"]["line"] = int(logistics[logistics.index("5:")+2:logistics.index("6:")-1])
        position["end"]["column"] = int(logistics[logistics.index("7:")+2:logistics.index("8:")-1])
    elif func[:12] in ["rename field", "create index", "remove index"]:
        position["start"]["line"] = int(logistics[logistics.index("5:")+2:logistics.index("6:")-1])
        position["start"]["column"] = int(logistics[logistics.index("6:")+2:logistics.index("7:")-1])
        position["end"]["line"] = int(logistics[logistics.index("5:")+2:logistics.index("6:")-1])
        position["end"]["column"] = int(logistics[logistics.index("8:")+2:logistics.index("9:")-1])
    elif func[:12] in ["remove field", "assoc change", "changed type"]:
        position["start"]["line"] = int(logistics[logistics.index("5:")+2:logistics.index("6:")-1])
        position["start"]["column"] = int(logistics[logistics.index("6:")+2:logistics.index("7:")-1])
        position["end"]["line"] = int(logistics[logistics.index("9:")+2:logistics.index("10:")-1])
        position["end"]["column"] = int(logistics[logistics.index("8:")+2:logistics.index("9:")-1])
    elif func[:12] == "rename model":
        position["start"]["line"] = int(logistics[logistics.index("1:")+2:logistics.index("2:")-1])
        position["start"]["column"] = int(logistics[logistics.index("2:")+2:logistics.index("3:")-1])
        position["end"]["line"] = int(logistics[logistics.index("1:")+2:logistics.index("2:")-1])
        position["end"]["column"] = int(logistics[logistics.index("3:")+2:logistics.index("4:")-1])
    elif func[:12] == "delete model":
        position["start"]["line"] = int(logistics[logistics.index("1:")+2:logistics.index("2:")-1])
        position["start"]["column"] = int(logistics[logistics.index("2:")+2:logistics.index("3:")-1])
        position["end"]["line"] = int(logistics[logistics.index("10:")+3:])
        position["end"]["column"] = int(logistics[logistics.index("4:")+2:logistics.index("5:")-1])

    dct = {   
            "reason": {
                "type": changetype_convert(func[:12]), 
                "detailed": func[13:]
            },
            "patch": patch_type(func),
            "position": position
          }

    return dct

data = []

# check if any existing queries cause errors
for fi in files:
    dmodels = {}
    fileinfo = {
        "file": fi,
        "issues": []
    }
    for q in files[fi]:
        if q in final_db or (" " not in q and q in final_drmodels):
            for lo in files[fi][q]:
                if " " not in q:
                    func = final_drmodels[q]
                else:
                    func = final_db[q]
                if func[:12] == "delete model":
                    st = func+lo[:lo.index("3:")]
                    if st in dmodels:
                        dmodels[st].append(lo)
                    else:
                        dmodels[st] = [lo]
                elif func[:12] == "rename model":
                    if "3:**" not in lo:
                        jc = jsonconvert(lo, func)
                        if jc not in data:
                            fileinfo["issues"].append(jc)
                else:
                    jc = jsonconvert(lo, func)
                    if jc not in data:
                        fileinfo["issues"].append(jc)
        if q in final_assoctypes:
            for lo in files[fi][q]:
                jc = jsonconvert(lo, final_assoctypes[q])
                if jc not in data:
                    fileinfo["issues"].append(jc)
        if q in final_indexes:
            for lo in files[fi][q]:
                jc = jsonconvert(lo, final_indexes[q])
                if jc not in data:
                    fileinfo["issues"].append(jc)
        if q in final_types:
            for lo in files[fi][q]:
                jc = jsonconvert(lo, final_types[q])
                if jc not in data:
                    fileinfo["issues"].append(jc)
    for dmodel in dmodels:
        endco = []
        endline = []
        for lo in dmodels[dmodel]:
            endco.append(int(lo[lo.index("4:")+2:lo.index("5:")-1]))
            endline.append(int(lo[lo.index("10:")+3:]))
        four = max(endco)
        ten = max(endline)
        holder = dmodels[dmodel][0]
        logistics = holder[:holder.index("4:")]+"4:{} ".format(four)+holder[holder.index("5:"):holder.index("10:")+3]+str(ten)
        fileinfo["issues"].append(jsonconvert(logistics, dmodel[:dmodel.index("1:")]))
    if len(fileinfo["issues"]) > 0:
        data.append(fileinfo)

def run(args):
    app_dir = args.app_dir+"/output.json"
    with open(app_dir, "w") as write_file:
        json.dump(data, write_file)

def main():
	parser=argparse.ArgumentParser(description="schema")
	parser.add_argument("-d",help="app_dir" ,dest="app_dir", type=str, required=True)
	parser.set_defaults(func=run)
	args=parser.parse_args()
	args.func(args)

if __name__=="__main__":
	main()

# -- CLEAR FILES --

file = open("queries/complex-lookups.txt","r+")
file.truncate(0)
file.close()

file = open("db1/drfields/fields.txt","r+")
file.truncate(0)
file.close()

file = open("db1/drfields/drfields.txt","r+")
file.truncate(0)
file.close()

file = open("db1/drfields/models.txt","r+")
file.truncate(0)
file.close()

file = open("db1/drfields/drmodels.txt","r+")
file.truncate(0)
file.close()

file = open("db1/drfields/indexes.txt","r+")
file.truncate(0)
file.close()

file = open("db1/assoc/assoc.txt","r+")
file.truncate(0)
file.close()

file = open("db1/assoc/assoc-type.txt","r+")
file.truncate(0)
file.close()

file = open("db2/drfields/fields.txt","r+")
file.truncate(0)
file.close()

file = open("db2/drfields/drfields.txt","r+")
file.truncate(0)
file.close()

file = open("db2/drfields/models.txt","r+")
file.truncate(0)
file.close()

file = open("db2/drfields/drmodels.txt","r+")
file.truncate(0)
file.close()

file = open("db2/drfields/indexes.txt","r+")
file.truncate(0)
file.close()

file = open("db2/assoc/assoc.txt","r+")
file.truncate(0)
file.close()

file = open("db2/assoc/assoc-type.txt","r+")
file.truncate(0)
file.close()

file = open("queries/property.txt","r+")
file.truncate(0)
file.close()

file = open("queries/get-models.txt","r+")
file.truncate(0)
file.close()

file = open("queries/query-output.txt","r+")
file.truncate(0)
file.close()

file = open("queries/binop.txt","r+")
file.truncate(0)
file.close()

file = open("db1/type/output.txt","r+")
file.truncate(0)
file.close()

file = open("db2/type/output.txt","r+")
file.truncate(0)
file.close()