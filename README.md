# parser

## commands:

git reset --hard (commit before schema change)

python db1/drfields/database.py

python db1/drfields/assoc.py

git reset --hard (commit after schema change)

python db2/drfields/database.py

python db2/drfields/assoc.py

python queries/get-models.py

python queries/queries.py

python queries/property.py

python compare.py

## imports and requirements:

python version >= 3.9.4

No required libraries to install.
