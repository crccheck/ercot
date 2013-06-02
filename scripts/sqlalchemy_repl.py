"""
REPL for playing with Postgres database and sqlalchemy.
"""
import os

import sqlalchemy

engine = sqlalchemy.create_engine(
        os.environ.get('DATABASE_URL', 'postgres:///ercot'))
metadata = sqlalchemy.MetaData(bind=engine)
metadata.reflect(only=[
    'ercot_realtime',
])

t = metadata.tables['ercot_realtime']
