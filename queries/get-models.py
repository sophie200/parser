import ast
import argparse
from pathlib import Path

class VisitCall(ast.NodeVisitor):

    def visit_Call(self, node):
        f = open("queries/get-models.txt", "a")
        func = node.func
        if type(func) == ast.Attribute:
            funcname = func.attr
            keywords = node.keywords
            # including all models, even those deleted or renamed because parser will deal with those errors, so parser doesn't need to include models that exist only in the current version.
            if funcname == 'CreateModel':
                model_name = keywords[0].value.value
                print(model_name, file=f)
            elif funcname == 'RenameModel':
                if keywords != []:
                    print(keywords[1].value.value, file=f)
                else:
                    args = node.args
                    print(args[1].value, file=f)
        f.close()

# add User model
f = open("queries/get-models.txt", "a")
print("User", file=f)   
f.close()

# start going through app
def run(args):
    app_dir = args.app_dir
    paths = Path(app_dir).glob('**/*.py')
    for path in paths:
        filepath = str(path)
        if "/migrations/" in filepath:
            contents = open(filepath).read()
            #f = open("queries/get-models.txt", "a")
            #print(filepath[42:], file=f)
            #f.close()
            tree = ast.parse(contents)
            vc = VisitCall()
            vc.visit(tree)

def main():
	parser=argparse.ArgumentParser(description="schema")
	parser.add_argument("-d",help="app_dir" ,dest="app_dir", type=str, required=True)
	parser.set_defaults(func=run)
	args=parser.parse_args()
	args.func(args)

if __name__=="__main__":
	main()