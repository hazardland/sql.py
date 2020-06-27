import os
import sys
import sql
import fakedb

if sys.platform.lower() == "win32":
    os.system('color')

import logging as log
log.basicConfig(level=log.DEBUG)

sql.Table.get_db = fakedb.get_db
sql.Table.put_db = fakedb.put_db
