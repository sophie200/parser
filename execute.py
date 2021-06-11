import subprocess
import argparse
import os
from pathlib import Path
import time

def run(args):
    #start_time = time.time()
    commit1 = args.commit1
    commit2 = args.commit2
    app_dir = args.app_dir
    os.system("cd {} && git checkout -f {}".format(app_dir, commit1))
    os.system("python db1/drfields/database.py -d {}".format(app_dir))
    os.system("python db1/assoc/assoc.py -d {}".format(app_dir))
    os.system("python db1/type/type-change.py -d {}".format(app_dir))
    os.system("cd {} && git checkout -f {}".format(app_dir, commit2))
    os.system("python db2/drfields/database.py -d {}".format(app_dir))
    os.system("python db2/assoc/assoc.py -d {}".format(app_dir))
    os.system("python db2/type/type-change.py -d {}".format(app_dir))
    os.system("python queries/get-models.py -d {}".format(app_dir))
    os.system("python queries/queries.py -d {}".format(app_dir))
    os.system("python queries/property.py -d {}".format(app_dir))
    os.system("python compare.py -d {}".format(app_dir))
    #print("--- %s seconds ---" % (time.time() - start_time))
    

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
