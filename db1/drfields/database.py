import ast
from pathlib import Path

class VisitAssign(ast.NodeVisitor):

    def visit_Assign(self, node): 
        if type(node.targets[0]) == ast.Name:
            if node.targets[0].id == 'operations':
                vc = VisitCall()
                vc.visit(node)

class VisitCall(ast.NodeVisitor):

    def visit_Call(self, node):
        # get existing fields
        b = open("db1/drfields/buffer.txt", "r")
        fields = []
        for x in b:
            fields.append(x[:-1])
        b.close()
        # parse through migrations
        b = open("db1/drfields/buffer.txt", "a")
        func = node.func
        if type(func) == ast.Attribute:
            funcname = func.attr
            keywords = node.keywords
            if funcname == 'CreateModel':
                model_name = keywords[0].value.value.lower()
                m = open("db1/drfields/buffer2.txt", "a")
                print(model_name, file=m)
                print("add", file=m)
                m.close()
                # if create model that was once deleted all fields from deleted model change from delete model to remove field, this will be fixed if need to by next step with add field.
                for field in fields:
                    if field[:len(model_name)+1] == model_name+" ":
                        print("{} {}".format(model_name, field[(len(model_name)+1):]), file=b)
                        print("remove field remove {}".format(field[(len(model_name)+1):]), file=b)
                tuples = keywords[1].value.elts
                for t in tuples:
                    print("{} {}".format(model_name, t.elts[0].value.lower()), file=b)
                    print("add", file=b)
            elif funcname == 'AddField':
                model_name = keywords[0].value.value.lower()
                print("{} {}".format(model_name, keywords[1].value.value.lower()), file=b)
                print("add", file=b)
            elif funcname == 'DeleteModel':
                model_name = keywords[0].value.value.lower()
                m = open("db1/drfields/buffer2.txt", "a")
                print(model_name, file=m)
                print("delete model delete model {}".format(model_name), file=m)
                m.close()
                for field in fields:
                    if field[:len(model_name)+1] == model_name+" ":
                        print(field, file=b)
                        print("delete model delete model {}".format(model_name), file=b)
            elif funcname == 'RenameModel':
                if keywords != []:
                    model_name_1 = keywords[0].value.value.lower()
                    model_name_2 = keywords[1].value.value.lower()
                else:
                    model_name_1 = node.args[0].value.lower()
                    model_name_2 = node.args[1].value.lower()
                m = open("db1/drfields/buffer2.txt", "a")
                print(model_name_1, file=m)
                print("rename model {} to {}".format(model_name_1, model_name_2), file=m)
                print(model_name_2, file=m)
                print("add", file=m)
                m.close()
                #if create model that was once deleted all fields from deleted model change from delete model to remove field, this will be fixed if need to by next step with add field.
                for field in fields:
                    if field[:len(model_name_2)+1] == model_name_2+" ":
                        print("{} {}".format(model_name_2, field[(len(model_name_2)+1):]), file=b)
                        print("remove field remove {}".format(field[(len(model_name_2)+1):]), file=b)
                for field in fields:
                    if field[:len(model_name_1)+1] == model_name_1+" ":
                        print(field, file=b)
                        print("rename model {} to {}".format(model_name_1, model_name_2), file=b)
                        print("{} {}".format(model_name_2, field[(len(model_name_1)+1):]), file=b)
                        print("add", file=b)
            elif funcname == 'RemoveField':
                model_name = ""
                for keyword in keywords:
                    if keyword.arg == "model_name":
                        model_name = keyword.value.value.lower()
                    if keyword.arg == "name":
                        print("{} {}".format(model_name, keyword.value.value), file=b) 
                        print("remove field remove {}".format(keyword.value.value), file=b)
            elif funcname == 'RenameField':
                if keywords != []:
                    model_name = keywords[0].value.value.lower()
                    print("{} {}".format(model_name, keywords[1].value.value.lower()), file=b)
                    print("rename field {} to {}".format(keywords[1].value.value.lower(), keywords[2].value.value.lower()), file=b)
                    print("{} {}".format(model_name, keywords[2].value.value.lower()), file=b)
                    print("add", file=b)
                else:
                    model_name = node.args[0].value.lower()
                    print("{} {}".format(model_name, node.args[1].value.lower()), file=b)
                    print("rename field {} to {}".format(node.args[1].value.lower(), node.args[2].value.lower()), file=b)
                    print("{} {}".format(model_name, node.args[2].value.lower()), file=b)
                    print("add", file=b)
            elif funcname == 'AddIndex':
                model_name = keywords[0].value.value.lower()
                index = keywords[1].value.keywords
                for keyword in index:
                    if keyword.arg.lower() == 'fields':
                        indfields = keyword.value.elts
                    if keyword.arg.lower() == 'name':
                        indexname = keyword.value.value
                for indfield in indfields:
                    ind = open("db1/drfields/index.txt", "a")
                    print("{} {}".format(model_name, indfield.value), file=ind)
                    print(indexname, file=ind)
                    ind.close()
            elif funcname == 'RemoveIndex':
                indexname = keywords[1].value.value.lower()
                ind = open("db1/drfields/index.txt", "a")
                print("remove", file=ind)
                print(indexname, file=ind)
                ind.close()
        b.close()

mfiles = []
paths = Path("/Users/sophiexie/Downloads/code/dsp/posthog/").glob('**/*.py')
for path in paths:
    filepath = str(path)
    if '/migrations/' in filepath:
        mfiles.append(filepath)

app_mfiles = []
all_mfiles = []
appname = ""
filepath_header = ""
for i in range(len(mfiles)):
    m = mfiles[i]
    mpoint = m[:(m.index("/migrations"))]
    m_appname = mpoint[::-1][:(mpoint[::-1].index("/"))][::-1]
    m_filepath_header = mpoint[::-1][(mpoint[::-1].index("/")):][::-1]
    if m_appname == appname and "/migrations/0" in m:
        app_mfiles.append(m[m.index("/migrations/"):])
    if m_appname != appname or i == (len(mfiles)-1):
        app_mfiles.sort()
        for sm in app_mfiles:
            all_mfiles.append(filepath_header+appname+sm)
        all_mfiles.append("break")
        app_mfiles = []
        appname = m_appname
        filepath_header = m_filepath_header
        app_mfiles.append(m[m.index("/migrations/"):])

for m in all_mfiles:
    if m != "break":
        contents = open(m).read()
        tree = ast.parse(contents)
        va = VisitAssign()
        va.visit(tree)
    if m == "break":
        # database fields
        fields = {}
        b = open("db1/drfields/buffer.txt", "r")
        lines = []
        for x in b:
            lines.append(x[:-1])
        b.close()
        c = 0
        while c < len(lines)-1:
            field = lines[c]
            status = lines[c+1]
            if field in fields:
                fields[field].append(status)
            else:
                fields[field] = [status]
            c+=2 
        b = open("db1/drfields/buffer.txt", "r+")
        b.truncate(0)
        b.close()
        f = open("db1/drfields/fields.txt", "a")
        drf = open("db1/drfields/drfields.txt", "a")
        for i in fields:
            if fields[i][-1] == "add":
                print(i, file=f)
            else:
                print(i, file=drf)
                print(fields[i][-1], file=drf)
        drf.close()
        f.close()
        # database models
        models = {}
        b2 = open("db1/drfields/buffer2.txt", "r")
        lines2 = []
        for x in b2:
            lines2.append(x[:-1])
        b2.close()
        c = 0
        while c < len(lines2)-1:
            model = lines2[c]
            status = lines2[c+1]
            if model in models:
                models[model].append(status)
            else:
                models[model] = [status]
            c+=2 
        b2 = open("db1/drfields/buffer2.txt", "r+")
        b2.truncate(0)
        b2.close()
        m = open("db1/drfields/models.txt", "a")
        drm = open("db1/drfields/drmodels.txt", "a")
        for i in models:
            if models[i][-1] == "add":
                print(i, file=m)
            else:
                print(i, file=drm)
                print(models[i][-1], file=drm)
        f.close()
        drm.close()
        # indexes
        indexes = {}
        b3 = open("db1/drfields/index.txt", "r")
        lines3 = []
        for x in b3:
            lines3.append(x[:-1])
        b3.close()
        c=0
        while c<len(lines3)-1:
            fi = lines3[c]
            name = lines3[c+1]
            if fi == "remove":
                for inds in indexes:
                    if indexes[inds][-1] == name:
                        indexes[inds].append("remove")
            elif fi in indexes:
                indexes[fi].append(name)
            else:
                indexes[fi] = [name]
            c+=2
        b3 = open("db1/drfields/index.txt","r+")
        b3.truncate(0)
        b3.close()
        f = open("db1/drfields/indexes.txt", "a")
        for index in indexes:
            if indexes[index][-1] != "remove":
                print(index, file=f)
                print("create index this query benefits from an added index", file=f)
            else: 
                print(index, file=f)
                print("remove index this query no longer benefits from an added index because that index has been deleted", file=f)
        f.close()
