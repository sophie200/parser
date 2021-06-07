import subprocess
import argparse
from pathlib import Path

def run(args):
    commit1 = args.commit1
    commit2 = args.commit2
    app_dir = args.app_dir
    curr_dir = Path.cwd()
    subprocess.Popen(["git","reset", "--hard", commit1], cwd=app_dir)
    subprocess.Popen(["python","db1/drfields/database.py", "-d", app_dir], cwd=curr_dir)
    subprocess.Popen(["python","db1/assoc/assoc.py", "-d", app_dir], cwd=curr_dir)
    subprocess.Popen(["rm", "-f", ".git/index.lock"], cwd=app_dir)
    subprocess.Popen(["git","reset", "--hard", commit2], cwd=app_dir)
    subprocess.Popen(["python","db2/drfields/database.py", "-d", app_dir], cwd=curr_dir)
    subprocess.Popen(["python","db2/assoc/assoc.py", "-d", app_dir], cwd=curr_dir)
    subprocess.Popen(["python","queries/get-models.py", "-d", app_dir], cwd=curr_dir)
    subprocess.Popen(["python","queries/queries.py", "-d", app_dir], cwd=curr_dir)
    subprocess.Popen(["python","queries/property.py", "-d", app_dir], cwd=curr_dir)
    subprocess.Popen(["python","compare.py"])
    

def main():
	parser=argparse.ArgumentParser(description="schema")
	parser.add_argument("-c1",help="commit/version 1" ,dest="commit1", type=str, required=True)
	parser.add_argument("-c2",help="commit/version 2" ,dest="commit2", type=str, required=True)
	parser.add_argument("-ad",help="app_dir" ,dest="app_dir", type=str, required=True)
	parser.set_defaults(func=run)
	args=parser.parse_args()
	args.func(args)

if __name__=="__main__":
	main()