import logging as log
import sql

log.basicConfig(level=log.DEBUG)

sql.Table.db = sql.Db('dbname=jigsaw user=postgres password=1234 host=127.0.0.1 port=5432')

print(sql.Table.db.version())
