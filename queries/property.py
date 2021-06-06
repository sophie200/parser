import ast
from pathlib import Path

class VisitClassDef(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        f = open("queries/model.txt","a")
        print(node.name, file=f)
        f.close()
        fd = VisitFunctionDef()
        fd.visit(node)
        f = open("queries/model.txt","r+")
        f.truncate(0)
        f.close()

class VisitFunctionDef(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        f = open("queries/model.txt","r")
        for x in f:
            model_name = x[:-1].lower()
        f.close()
        for i in node.decorator_list:
            if type(i) == ast.Name and i.id == 'property':
                p = open("queries/property.txt","a")
                print("{} {}".format(model_name, node.name), file=p)
                p.close()

paths = Path("/Users/sophiexie/Downloads/code/dsp/saleor/").glob('**/*.py')
for path in paths:
    filepath = str(path)
    if "/models" in filepath:
        contents = open(filepath).read()
        #f = open("queries/get-models.txt", "a")
        #print(filepath[42:], file=f)
        #f.close()
        tree = ast.parse(contents)
        cd = VisitClassDef()
        cd.visit(tree)

"""file="test.py"
contents = open(file).read()
tree = ast.parse(contents)
#print(ast.dump(tree))
cd = VisitClassDef()
cd.visit(tree)"""