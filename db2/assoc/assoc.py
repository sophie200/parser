import ast
import argparse
from pathlib import Path

def inherit(assoc, model_name):
    f = open("db2/drfields/fields.txt", "r")
    fields = []
    for x in f:
        fields.append(x[:-1])
    f.close()
    for field in fields:
        if field[0:len(assoc)+1] == assoc+" ":
            f = open("db2/assoc/assoc.txt", "a")
            print("--ih {} {}".format(model_name, field[len(assoc)+1:]), file=f)
            f.close()

class VisitCall(ast.NodeVisitor):

    def visit_Call(self, node):
        func = node.func
        if type(func) == ast.Attribute:
            funcname = func.attr
            args = node.keywords
            if funcname == 'CreateModel':
                model_name = ""
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
                            rel_names = []
                            if field.elts[1].func.attr in ['ForeignKey', 'ManyToManyField', 'OneToOneField']:
                                have_parent_link = False
                                keywords = field.elts[1].keywords
                                for keyword in keywords:
                                    if keyword.arg == 'to':
                                        association = keyword.value.value
                                        if type(association) == ast.Name:
                                            association = 'user'
                                        else:
                                            idx = association.index(".")
                                            association = association[idx+1:]
                                    elif keyword.arg == 'related_name' or keyword.arg == 'related_query_name':
                                        rel_names.append(keyword.value.value)
                                    # for inherited classes
                                    elif field.elts[1].func.attr == 'OneToOneField' and keyword.arg == 'parent_link':
                                        have_parent_link = True
                                f = open("db2/assoc/assoc.txt", "a")
                                print("{} {}".format(model_name, field_name), file=f)
                                if rel_names != []:
                                    for rel_name in rel_names:
                                        print("-- {} {}".format(association.lower(), rel_name), file=f)
                                else: 
                                    print("-- {} {}".format(association.lower(), model_name), file=f)
                                f.close()
                                f = open("db2/assoc/assoc-type.txt", "a")
                                print("{} {}".format(model_name, field_name), file=f)
                                print(field.elts[1].func.attr, file=f)
                                f.close()
                                # for inherited classes
                                if have_parent_link:
                                    inherit(association.lower(), model_name)
            elif funcname in ['AddField', 'AlterField']:
                model_name = node.keywords[0].value.value.lower()
                field_name = node.keywords[1].value.value.lower()
                rel_names = []
                if type(node.keywords[2].value.func) != ast.Name and node.keywords[2].value.func.attr in ['ForeignKey', 'ManyToManyField', 'OneToOneField']:
                    have_parent_link = False
                    keywords = node.keywords[2].value.keywords
                    for keyword in keywords:
                        if keyword.arg == 'to':
                            association = keyword.value.value
                            if type(association) == ast.Name:
                                association = 'user'
                            else:
                                idx = association.index(".")
                                association = association[idx+1:]
                        elif keyword.arg == 'related_name' or keyword.arg == 'related_query_name':
                            rel_names.append(keyword.value.value)
                        # for inherited classes
                        elif node.keywords[2].value.func.attr == 'OneToOneField' and keyword.arg == 'parent_link':
                            have_parent_link = True
                    f = open("db2/assoc/assoc.txt", "a")
                    print("{} {}".format(model_name, field_name), file=f)
                    if rel_names != []:
                        for rel_name in rel_names:
                            print("-- {} {}".format(association.lower(), rel_name), file=f)
                    else: 
                        print("-- {} {}".format(association.lower(), model_name), file=f)
                    f.close()
                    f = open("db2/assoc/assoc-type.txt", "a")
                    print("{} {}".format(model_name, field_name), file=f)
                    print(node.keywords[2].value.func.attr, file=f)
                    f.close()
                    # for inherited classes
                    if have_parent_link:
                        inherit(association.lower(), model_name)
            elif funcname == 'RenameField':
                a_ = open("db2/assoc/assoc.txt", "r")
                assocs = []
                for x in a_:
                    assocs.append(x[:-1])
                a_.close()
                if args != []:
                    model_name = args[0].value.value.lower()
                    o_f = args[1].value.value.lower()
                    n_f = args[2].value.value.lower()
                else:
                    model_name = node.args[0].value.lower()
                    o_f = node.args[1].value.lower()
                    n_f = node.args[2].value.lower()
                for i in range(len(assocs)-1):
                    a = assocs[i]
                    if "--" not in a:
                        if "{} {}".format(model_name, o_f) == a:
                            f = open("db2/assoc/assoc.txt", "a")
                            print("{} {}".format(model_name, n_f), file=f)
                            print(assocs[i+1], file=f)
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
            app_mfiles = []
            appname = m_appname
            filepath_header = m_filepath_header
            app_mfiles.append(m[m.index("/migrations/"):])

    for m in all_mfiles:
        #f = open("db2/assoc/assoc.txt", "a")
        #print(m[len("/Users/sophiexie/Downloads/code/dsp/"):], file=f)
        #f.close()
        contents = open(m).read()
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