from sqlalchemy import create_engine, text
import pandas as pd

class Database():
    def __init__(self, cfg):

        self.cfg = cfg

        try:

            self.conn = self.engine()
            self.create()
            self.connect()

            print('\033[93mDatabase version: <{}>\nCurrent database: <{}>\033[0m'.format(self.version(),self.current()))

        except Exception as error:

            print('\033[91mException in {}.__init__:{}\033[0m'.format(self.__class__.__name__,  str(error)))    

    def version(self):

        return self.conn.execute( text( 'SELECT version();')).fetchall()[0]['version']

    def current(self):
        
        return self.conn.execute( text( 'SELECT current_database();')).fetchall()[0][0]

    def engine(self):
        
        return create_engine( self.cfg['type']+'+'+ self.cfg['connector']+ '://'+ self.cfg['user']+':'+ self.cfg['password']+'@'+self.cfg['host']+':'+self.cfg['port']+'/'+self.cfg['db'])

    def create(self):
        
        if self.cfg['db'] not in self.list():

            self.conn.connect().execution_options(isolation_level="AUTOCOMMIT").execute( text( 'CREATE DATABASE '+self.cfg['db']+';'))

    def connect(self):
        
        if self.cfg['db'] in self.list() and self.cfg['db'] not in self.current():

            self.conn.connect().invalidate()
            self.conn.dispose()
            self.conn = self.engine(self.cfg['db'])
            self.conn.autocommit = True

    def list(self):
        
        if self.engine is not None:
            resp = self.conn.execute( text( 'SELECT datname FROM pg_database WHERE datistemplate = false;')).fetchall()
            return [resp[i][0] for i in range(len(resp))] 
    
    def drop(self, *args):
        
        if len(args[0]) == 1:
            db = args[0]
            if db in self.list():
                self.conn.connect().execution_options(isolation_level="AUTOCOMMIT").execute( text( 'DROP DATABASE '+db+';'))
            
        elif len(args[0]) == 3:
            db = args[0][0]
            schema = args[0][1]
            table = args[0][2]
            sql = 'DROP TABLE IF EXISTS {}.{}.{};'.format(db,schema, table)
            self.conn.execute( text( sql ))

    def write(self, schema, table, df):
        columns = list(df.columns)
        data = df.values

        if self.has_table(schema, table, columns):
            
            sql_columns = '\",\"'.join(columns)
            sql = 'INSERT INTO {}.{} ('.format(schema, table) + '\"' + sql_columns.lower() + '\") VALUES\n'
            for row in range(data.shape[0]):
                sql_values = '\',\''.join(data[row,:])
                print('row {}'.format(row))
                sql += ' ( \'' +sql_values+ '\'' + (' ),\n' if row<=data.shape[0]-2 else ' );')
            self.conn.execute( text( sql ))

    def read(self, schema, table, N=1):
        sql = 'SELECT * FROM {}.{} ORDER BY time DESC LIMIT {};'.format(schema,table,min(N,self.count(schema,table)))
        return (pd.read_sql_query(sql, self.conn)).iloc[::-1]

    def count(self, schema, table):
        sql = 'SELECT count(*) FROM {}.{}'.format(schema,table)+';'
        return pd.read_sql_query(sql, self.conn)['count'][0]
                
    def sample(self, schema, table, N=1):
        sql = 'SELECT * FROM {}.{} ORDER BY random() LIMIT {};'.format(schema,table,min(N,self.count(schema,table)))
        return pd.read_sql_query(sql, self.conn)
        

    def has_table(self, schema, table, columns):
    
        resp = self.conn.execute( text( 'SELECT schema_name FROM information_schema.schemata;')).fetchall()
        if schema not in [resp[i][0] for i in range(len(resp))]:
            self.conn.execute( text( 'CREATE SCHEMA '+schema+';'))
      
        resp = self.conn.execute( text( 'SELECT * FROM information_schema.tables WHERE table_schema = \'{}\';'.format(schema))).fetchall()
        if len(resp) == 0 or table not in list(resp[0]):
            print('Create new schema.table: {}.{}'.format(schema, table))
            sql = 'CREATE TABLE ' + schema +'.'+ table + ' ( time '
            for column in columns:
               sql +=  ', ' + column + ' float ( 24 )' if column != 'time' else 'TIMESTAMP(3) PRIMARY KEY'
            sql += ' );'
            self.conn.execute( text( sql ))

        return True
