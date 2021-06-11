import ast
import os, sys
from pathlib import Path
import argparse

class VisitCall(ast.NodeVisitor):

    def visit_Call(self, node):
        f = open("db1/type/output.txt", "r")
        fields = []
        for x in f:
            fields.append(x[:-1])
        f.close()
        f = open("db1/type/output.txt", "a")
        func = node.func
        # Call(expr func, expr* args, keyword* keywords)
        if type(func) == ast.Attribute:
            # Attribute(expr value, identifier attr, expr_context ctx) attr is used for function name
            funcname = func.attr
            if funcname == 'CreateModel':
                args = node.keywords
                for arg in args:
                    v = arg.value
                    if(type(arg.value) == ast.Str):
                        v = arg.value.s
                    if arg.arg == "name":
                        model_name = (arg.value.value).lower()
                    if arg.arg == "fields":
                        fields = v.elts 
                        field_name = ""
                        for field in fields:
                            if type(field.elts[0]) == ast.Name:
                                field_name = field.elts[0].id
                            else:
                                field_name = field.elts[0].value
                            print("{} {}".format(model_name, field_name), file=f)
                            print("-- {}".format(field.elts[1].func.attr), file=f)
            elif funcname == "RenameModel":
                args = node.args
                if args != []:
                    model_name_1 = args[0].value.lower()
                    model_name_2 = args[1].value.lower()
                else:
                    args = node.keywords
                    model_name_1 = args[0].value.value.lower()
                    model_name_2 = args[1].value.value.lower()
                for i in range(len(fields)):
                    field = fields[i]
                    if field[:len(model_name_1)] == model_name_1:
                        print(field, file=f)
                        print("-- {}".format("remove"), file=f)
                        print("{} {}".format(model_name_2, field[(len(model_name_1)+1):]), file=f)
                        print(fields[i+1], file=f)
            elif funcname == 'AddField':
                model_name = node.keywords[0].value.value.lower()
                c_name = node.keywords[1].value.value.lower()
                t = node.keywords[2].value.func
                if type(t) == ast.Name:
                    print("{} {}".format(model_name, c_name), file=f)
                    print("-- {}".format(t.id), file=f)
                else:
                    print("{} {}".format(model_name, c_name), file=f)
                    print("-- {}".format(t.attr), file=f)
            elif funcname == 'AlterField':
                model_name = node.keywords[0].value.value.lower()
                c_name = node.keywords[1].value.value.lower()
                t = node.keywords[2].value.func
                if type(t) == ast.Name:
                    print("{} {}".format(model_name, c_name), file=f)
                    print("-- {}".format(t.id), file=f)
                else:
                    print("{} {}".format(model_name, c_name), file=f)
                    print("-- {}".format(t.attr), file=f)
            elif funcname == 'RenameField':
                if node.keywords != []:
                    model_name = node.keywords[0].value.value.lower()
                    field_1 = node.keywords[1].value.value
                    field_2 = node.keywords[2].value.value
                else:
                    model_name = node.args[0].value.lower()
                    field_1 = node.args[1].value
                    field_2 = node.args[2].value
                pfield = "{} {}".format(model_name, field_1)
                for i in range(len(fields)):
                    field = fields[i]
                    if pfield == field:
                        print(field, file=f)
                        print("-- {}".format("remove"), file=f)
                        print("{} {}".format(model_name, field_2), file=f)
                        print(fields[i+1], file=f)
            elif funcname == 'DeleteModel':
                keywords = node.keywords
                model_name = keywords[0].value.value.lower()
                for field in fields:
                    if field[:len(model_name)] == model_name:
                        print(field, file=f)
                        print("-- {}".format("remove"), file=f)
            elif funcname == 'RemoveField':
                keywords = node.keywords
                model_name = ""
                for keyword in keywords:
                    if keyword.arg == "model_name":
                        model_name = keyword.value.value.lower()
                    if keyword.arg == "name":
                        field_name = keyword.value.value
                print("{} {}".format(model_name, field_name), file=f)
                print("-- {}".format("remove"), file=f)
                
        f.close()

def run(args):
    mfiles = []
    app_dir = args.app_dir
    paths = Path(app_dir).glob('**/*.py')
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

    tc = []
    for m in all_mfiles:
        if m != "break":
            contents = open(m).read()
            tree = ast.parse(contents)
            vc = VisitCall()
            vc.visit(tree)
        if m == "break":
            fields = {}
            f = open("db1/type/output.txt", "r")
            lines = []
            for x in f:
                lines.append(x[:-1])
            f.close()
            c = 0
            while c < len(lines)-1:
                field = lines[c]
                status = lines[c+1][3:]
                if field in fields:
                    fields[field].append(status)
                else:
                    fields[field] = [status]
                c+=2 
            for field in fields:
                types = fields[field]
                if len(types) >= 2 and 'remove' not in [types[-2], types[-1]] and types[-1] != types[-2]:
                    tc.append(field)
                    tc.append("changed type change type {} to {}".format(types[-2], types[-1]))
            
            file = open("db1/type/output.txt","r+")
            file. truncate(0)
            file.close()
    
    # Clear file
    file = open("db1/type/output.txt","r+")
    file. truncate(0)
    file.close()

    f = open("db1/type/output.txt","a")
    for t in tc:
        print(t, file=f)
    f.close()

def main():
	parser=argparse.ArgumentParser(description="schema")
	parser.add_argument("-d",help="app_dir" ,dest="app_dir", type=str, required=True)
	parser.set_defaults(func=run)
	args=parser.parse_args()
	args.func(args)

if __name__=="__main__":
	main()