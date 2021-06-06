import ast
import os, glob
from pathlib import Path

def queries(s, li):
    lst = s.split("__")
    for i in range(len(lst)-1):
        f = open("queries/query-output.txt", "a")
        print("{} {}".format(lst[i].lower(), lst[i+1].lower()), file=f)
        two = li.col_offset+s.index(lst[i])
        three = two+len(lst[i])
        seven = three+2+len(lst[i+1])
        six = three+2
        print("1:{} 2:{} 3:{} 4:{} 5:{} 6:{} 7:{} 8:{} 9:{} 10:{}".format(li.lineno - 1, two, three, li.end_col_offset, li.lineno-1, six, seven, li.end_col_offset, li.end_lineno-1, li.end_lineno-1), file=f)
        f.close()

class ChainedQueries(ast.NodeVisitor):

    def visit_FunctionDef(self, node):
        file = open("queries/var-output.txt","r+")
        file.truncate(0)
        file.close()
        file = open("queries/complex-lookups.txt","r+")
        file.truncate(0)
        file.close()
        m = open("queries/model.txt","r+")
        m.truncate(0)
        m.close()
        body = node.body
        for b in body:
            cq = ChainedQueries()
            cq.visit(b)
        file = open("queries/var-output.txt","r+")
        file.truncate(0)
        file.close()
        file = open("queries/complex-lookups.txt","r+")
        file.truncate(0)
        file.close()
        m = open("queries/model.txt","r+")
        m.truncate(0)
        m.close()

    def visit_Assign(self, node):
        m = open("queries/model.txt","r+")
        m.truncate(0)
        m.close()
        vs = open("queries/var-output.txt", "a")
        var=""
        if type(node.targets[0]) == ast.Name or type(node.targets[0]) == ast.Attribute:
            # first deal with variable names (for chained queries)
            if type(node.targets[0]) == ast.Name:
                var = node.targets[0].id
            # next deal with content of query: first var = Model.objects
            if type(node.value) == ast.Attribute and node.value.attr == 'objects':
                if type(node.value.value) == ast.Name:
                    print("-- {}".format(var), file=vs)
                    print(node.value.value.id, file=vs)
            # next: regular queries
            elif type(node.value) == ast.Call or (type(node.value) == ast.UnaryOp and type(node.value.operand) == ast.Call):
                # parts of queries spread out over several variables
                if type(node.value) == ast.UnaryOp:
                    call = node.value.operand
                else:
                    call = node.value
                if type(call.func) == ast.Name:
                    complexlookups = open("queries/complex-lookups.txt","a")
                    print(var, file=complexlookups)
                    kws = call.keywords
                    args = call.args
                    # I have seen no evidence of Q() object with multiple keyword args
                    for kw in kws:
                        if type(kw) == ast.keyword:
                            if type(kw.arg) == str and "__" in kw.arg:
                                qu = kw.arg
                                field = qu[:(qu.index("__"))]
                                print("-- {}".format(field), file=complexlookups)
                                print("5:{} 6:{} 7:{} 8:{} 9:{}".format(kw.lineno-1, kw.col_offset, kw.col_offset+len(field), kw.end_col_offset, kw.end_lineno-1), file=complexlookups)
                                queries(qu, kw)
                            else:
                                print("-- {}".format(kw.arg), file=complexlookups)
                                print("5:{} 6:{} 7:{} 8:{} 9:{}".format(kw.lineno-1, kw.col_offset, kw.value.col_offset-1, kw.end_col_offset, kw.end_lineno-1), file=complexlookups)
                    for arg in args:
                        if type(arg) == ast.Constant and type(arg.value) == str: 
                            print("-- {}".format(arg.value), file=complexlookups)
                            print("5:{} 6:{} 7:** 8:{} 9:{}".format(arg.lineno-1, arg.col_offset, arg.end_col_offset, arg.end_lineno-1), file=complexlookups)
                    complexlookups.close()
                # regular queries
                cq = ChainedQueries()
                cq.visit(call)
            # queries with subscripts
            elif type(node.value) == ast.Subscript:
                if type(node.value.value) == ast.Call:
                    cq = ChainedQueries()
                    cq.visit(node.value)
            # get model and annotations for the chained query
            m = open("queries/model.txt", "r")
            model = []
            for i in m:
                model.append(i[:-1])
            m.close()
            c=0
            m_dct = {}
            while c < len(model):
                mo = model[c][3:]
                c+=1
                anns = []
                while c < len(model) and "-- " not in model[c]:
                    anns.append(model[c])
                    c+=1
                m_dct[mo] = anns
            if len(m_dct) > 0 and var != "":
                print("-- {}".format(var), file=vs)
                print(list(m_dct)[-1], file=vs)
                for a in m_dct[list(m_dct)[-1]]:
                    print(a, file=vs)
        vs.close()
        m = open("queries/model.txt","r+")
        m.truncate(0)
        m.close()

    def visit_Call(self, node):
        # get variables
        vs_file = open("queries/var-output.txt", "r")
        vs_lst = []
        for v in vs_file:
            vs_lst.append(v[:-1])
        vs_file.close()
        c = 0
        vs = {}
        while c < len(vs_lst)-1:
            var = vs_lst[c][3:]
            vs[var] = {"model": vs_lst[c+1], "annotations": []}
            j=c+2
            while j < len(vs_lst) and "-- " not in vs_lst[j]:
                vs[var]["annotations"].append(vs_lst[j])
                j+=1
            c=j
        # annotations
        annotations = []
        # --- AST analysis --- 
        # READ queries
        f = open("queries/query-output.txt", "a")
        if type(node.func) == ast.Attribute:
            q = node.func
            three = "**"
            model_name = "" 
            STOP = False
            # unchained queries 
            if type(q.value) == ast.Attribute and q.value.attr == "objects" and type(q.value.value) == ast.Name:
                model_name = q.value.value.id.lower()
                three = q.value.value.end_col_offset
            # chained queries
            elif type(q.value) == ast.Name and q.value.id in vs:
                model_name = vs[q.value.id]["model"].lower()
                for annotation in vs[q.value.id]["annotations"]:
                    annotations.append(annotation)
            # chaining queries
            elif type(q.value) == ast.Call:
                cq = ChainedQueries()
                cq.visit(q.value)
                m = open("queries/model.txt", "r")
                m_lst = []
                for i in m:
                    m_lst.append(i[:-1])
                m.close()
                c=0
                m_dct = {}
                while c < len(m_lst):
                    mo = m_lst[c][3:]
                    c+=1
                    anns = []
                    while c < len(m_lst) and "-- " not in m_lst[c]:
                        anns.append(m_lst[c])
                        c+=1
                    m_dct[mo] = anns
                if len(m_dct) > 0:
                    model_name = list(m_dct)[-1]
                    if len(m_dct[model_name]) > 0:
                        annotations+=m_dct[model_name]
                        STOP = True
            # -- QUERY PARSING START --    
            if model_name != "":
                if q.attr == "annotate":
                    a = open("queries/model.txt", "a")
                    for i in node.keywords:
                        if type(i) == ast.keyword:
                            print("-- {}".format(model_name), file=a)
                            print(i.arg, file=a)
                    for i in node.args:
                        if type(i) == ast.Call and type(i.func) == ast.Name:
                            fake_field = "__{}".format(i.func.id)
                            if len(i.args) > 0 and type(i.args[0]) == ast.Constant:
                                fake_field = i.args[0].value+fake_field
                        print("-- {}".format(model_name), file=a)
                        print(fake_field, file=a)
                    a.close()
                elif q.attr != "aggregate":
                    # regular keyword queries
                    for i in node.keywords:
                        if type(i) == ast.keyword:
                            # check for __ queries
                            if type(i.arg) == str and "__" in i.arg:
                                qu = i.arg
                                queries(qu, i)
                                field = qu[:(qu.index("__"))]
                                if field.lower() not in annotations:
                                    print("{} {}".format(model_name, field.lower()), file=f)
                                    print("1:{} 2:{} 3:{} 4:{} 5:{} 6:{} 7:{} 8:{} 9:{} 10:{}".format(node.lineno - 1, node.col_offset, three, node.end_col_offset, i.lineno-1, i.col_offset, i.col_offset+len(field), i.end_col_offset, i.end_lineno-1, node.end_lineno-1), file=f)
                            elif type(i.arg) == str and i.arg.lower() not in annotations:
                                print("{} {}".format(model_name, i.arg.lower()), file=f)
                                print("1:{} 2:{} 3:{} 4:{} 5:{} 6:{} 7:{} 8:{} 9:{} 10:{}".format(node.lineno - 1, node.col_offset, three, node.end_col_offset, i.lineno-1, i.col_offset, i.value.col_offset-1, i.end_col_offset, i.end_lineno-1, node.end_lineno-1), file=f)
                    # argument queries --> widerange
                    for i in node.args:
                        # for Q() django queries with operators
                        if type(i) == ast.BinOp:
                            bo = VisitBinOp()
                            bo.visit(i)
                        elif type(i) == ast.Call or (type(i) == ast.UnaryOp and type(i.operand) == ast.Call):
                            # for ~Q() but no operators
                            if type(i) == ast.UnaryOp:
                                i = i.operand
                            # Q() and other wrapper functions
                            if type(i.func) == ast.Name:
                                # for Q() with no operators
                                for j in i.keywords:
                                    qu = j.arg
                                    if not qu:
                                        val = ""
                                    elif type(qu) == str and "__" in qu:
                                        val = qu[:(qu.index("__"))]
                                        queries(qu, j)
                                    else:
                                        val = qu
                                    seven = j.col_offset+len(val)
                                    b = open("queries/binop.txt", "a")
                                    print(val, file=b)
                                    print("5:{} 6:{} 7:{} 8:{} 9:{}".format(j.lineno-1, j.col_offset, seven, j.end_col_offset, j.end_lineno-1), file=b)
                                    b.close()
                                """# for Count(), Low(), aggregate functions
                                for j in i.args:
                                    if type(j) == ast.Constant and type(j.value) == str and j.value.lower() not in annotations:
                                        print("{} {}".format(model_name, j.value.lower()), file=f)
                                        print("1:{} 2:{} 3:{} 4:{} 5:{} 6:{} 7:** 8:{} 9:{} 10:{}".format(node.lineno - 1, node.col_offset, three, node.end_col_offset, j.lineno-1, j.col_offset, j.end_col_offset, j.end_lineno-1, node.end_lineno-1), file=f)"""
                        # for Q() and other wrapper functions set to variables
                        elif type(i) == ast.Name:
                            complexlookups = open("queries/complex-lookups.txt","r")
                            cls_lst = []
                            for x in complexlookups:
                                cls_lst.append(x[:-1])
                            complexlookups.close()
                            c=0
                            cls = {}
                            while c < len(cls_lst)-2:
                                cl = cls_lst[c]
                                cls[cl] = [cls_lst[c+1][3:]]
                                cls[cl].append(cls_lst[c+2])
                                j = c+3
                                while j < len(cls_lst)-1 and "-- " in cls_lst[j]:
                                    cls[cl].append(cls_lst[j][3:])
                                    cls[cl].append(cls_lst[j+1])
                                    j+=2
                                c=j
                            for cl in cls:
                                if i.id == cl:
                                    b = open("queries/binop.txt", "a")
                                    c=0
                                    while c<len(cls[cl])-1:
                                        print(cls[cl][c], file=b)
                                        print(cls[cl][c+1], file=b)
                                        c+=2
                                    b.close()
                        # regular arg queries
                        elif type(i) == ast.Constant and type(i.value) == str:
                            # check for __ queries
                            if "__" in i.value:
                                qu = i.value
                                queries(qu, i)
                                field = qu[:(qu.index("__"))]
                                if field.lower() not in annotations:
                                    print("{} {}".format(model_name, field.lower()), file=f)
                                    print("1:{} 2:{} 3:{} 4:{} 5:{} 6:{} 7:** 8:{} 9:{} 10:{}".format(node.lineno - 1, node.col_offset, three, node.end_col_offset, i.lineno-1, i.col_offset, i.end_col_offset, i.end_lineno-1, node.end_lineno-1), file=f)
                            elif i.value.lower() not in annotations:
                                print("{} {}".format(model_name, i.value.lower()), file=f)
                                print("1:{} 2:{} 3:{} 4:{} 5:{} 6:{} 7:** 8:{} 9:{} 10:{}".format(node.lineno - 1, node.col_offset, three, node.end_col_offset, i.lineno-1, i.col_offset, i.end_col_offset, i.end_lineno-1, node.end_lineno-1), file=f)
                        # finish up Q() queries
                        values_file = open("queries/binop.txt", "r")
                        values = []
                        for x in values_file:
                            values.append(x[:-1])
                        values_file.close()
                        first_part = "1:{} 2:{} 3:{} 4:{} ".format(node.lineno - 1, node.col_offset, three, node.end_col_offset)
                        last_part = " 10:{}".format(node.end_lineno-1)
                        c = 0
                        while c < len(values):
                            v = values[c]
                            if v[:-1] not in annotations:
                                print("{} {}".format(model_name, v.lower()), file=f)
                                print(first_part+values[c+1]+last_part, file=f)
                            c+=2
                        file = open("queries/binop.txt","r+")
                        file.truncate(0)
                        file.close()
                    # info for chained queries
                    if not STOP:
                        model_file = open("queries/model.txt", "a")
                        print("-- {}".format(model_name), file=model_file)
                        model_file.close()
        # WRITE queries    
        elif type(node.func) == ast.Name:
            m = open("queries/get-models.txt", "r")
            models = []
            for i in m:
                models.append(i[:-1])
            m.close()
            if node.func.id in models:
                for keyword in node.keywords:
                    if keyword.arg != None:
                        print(node.func.id.lower(), keyword.arg.lower(), file=f)
                        print("1:{} 2:{} 3:{} 4:{} 5:{} 6:{} 7:{} 8:{} 9:{} 10:{}".format(node.lineno - 1, node.col_offset, node.func.end_col_offset, node.end_col_offset, keyword.lineno-1, keyword.col_offset, keyword.value.col_offset-1, keyword.end_col_offset, keyword.end_lineno-1, node.end_lineno-1), file=f)
            for arg in node.args:
                if type(arg) == ast.Call:
                    cq = ChainedQueries()
                    cq.visit(arg)
        f.close()

class VisitBinOp(ast.NodeVisitor):
    def visit_BinOp(self, node):
        if type(node.left) == ast.BinOp:
            bo = VisitBinOp()
            bo.visit(node.left)
        elif type(node.left) == ast.Call or (type(node.left) == ast.UnaryOp and type(node.left.operand) == ast.Call):
            if type(node.left) == ast.UnaryOp:
                qo = node.left.operand
            else:
                qo = node.left
            for i in qo.keywords:
                qu = i.arg
                if type(qu) == str and "__" in qu:
                    val = qu[:(qu.index("__"))]
                    queries(qu, i)
                else:
                    val = qu
                seven = i.col_offset+len(val)
                b = open("queries/binop.txt", "a")
                print(val, file=b)
                print("5:{} 6:{} 7:{} 8:{} 9:{}".format(i.lineno-1, i.col_offset, seven, i.end_col_offset, i.end_lineno-1), file=b)
                b.close()
        elif type(node.left) == ast.Name:
            complexlookups = open("queries/complex-lookups.txt","r")
            cls_lst = []
            for x in complexlookups:
                cls_lst.append(x[:-1])
            complexlookups.close()
            c=0
            cls = {} 
            while c < len(cls_lst)-2:
                cl = cls_lst[c]
                if cl in cls:
                    cls[cl].append(cls_lst[c+1][3:])
                else:
                    cls[cl] = [cls_lst[c+1][3:]]
                cls[cl].append(cls_lst[c+2])
                c+=3
            for cl in cls:
                if node.right.id == cl:
                    b = open("queries/binop.txt", "a")
                    print(cls[cl][-2], file=b)
                    print(cls[cl][-1], file=b)
                    b.close()
        if type(node.right) == ast.BinOp:
            bo = VisitBinOp()
            bo.visit(node.right)
        elif type(node.right) == ast.Call or (type(node.right) == ast.UnaryOp and type(node.right.operand) == ast.Call):
            if type(node.right) == ast.UnaryOp:
                qo = node.right.operand
            else:
                qo = node.right
            for i in qo.keywords:
                qu = i.arg
                if type(qu) == str and "__" in qu:
                    val = qu[:(qu.index("__"))]
                    queries(qu, i)
                else:
                    val = qu
                seven = i.col_offset+len(val)
                b = open("queries/binop.txt", "a")
                print(val, file=b)
                print("5:{} 6:{} 7:{} 8:{} 9:{}".format(i.lineno-1, i.col_offset, seven, i.end_col_offset, i.end_lineno-1), file=b)
                b.close()
        elif type(node.right) == ast.Name:
            complexlookups = open("queries/complex-lookups.txt","r")
            cls_lst = []
            for x in complexlookups:
                cls_lst.append(x[:-1])
            complexlookups.close()
            c=0
            cls = {} 
            while c < len(cls_lst)-2:
                cl = cls_lst[c]
                if cl in cls:
                    cls[cl].append(cls_lst[c+1][3:])
                else:
                    cls[cl] = [cls_lst[c+1][3:]]
                cls[cl].append(cls_lst[c+2])
                c+=3
            for cl in cls:
                if node.right.id == cl:
                    b = open("queries/binop.txt", "a")
                    print(cls[cl][-2], file=b)
                    print(cls[cl][-1], file=b)
                    b.close()

paths = Path("/Users/sophiexie/Downloads/code/dsp/saleor/").glob('**/*.py')
for path in paths:
    if "/migrations/" not in str(path):
        filepath = str(path)
        contents = open(filepath).read()
        tree = ast.parse(contents)
        f = open("queries/query-output.txt", "a")
        print(filepath[len("/Users/sophiexie/Downloads/code/dsp/saleor/"):], file=f)
        f.close()
        cq = ChainedQueries()
        cq.visit(tree)
        file = open("queries/var-output.txt","r+")
        file.truncate(0)
        file.close()
        file = open("queries/complex-lookups.txt","r+")
        file.truncate(0)
        file.close()

"""file="test.py"
contents = open(file).read()
tree = ast.parse(contents)
#print(ast.dump(tree))
cq = ChainedQueries()
cq.visit(tree)"""

# clear files
file = open("queries/var-output.txt","r+")
file.truncate(0)
file.close()
file = open("queries/complex-lookups.txt","r+")
file.truncate(0)
file.close()
m = open("queries/model.txt","r+")
m.truncate(0)
m.close()
