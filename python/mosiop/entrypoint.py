from configparser import ConfigParser

from opt.mpc.mpc import ConfigJson
from opt.mpc.mpc import MPC
from model import TestCase5

from api.aiohttp_api import Server, Client
from api.boptest_api import Boptest
from api.database_api import Database
from http import HTTPStatus

from datetime import datetime
import pandas as pd
import numpy as np
import time, json

import random

def debug_msg(msg):
    print(msg)

def notice_msg(msg): 
    print('\033[94m'+msg+'\033[0m') 

def warning_msg(msg): 
    print('\033[93m'+msg+'\033[0m')   

def error_msg(msg):
    print('\033[91m'+msg+'\033[0m')

class Config():
    def __init__(self,cfg_ini):
        self.parser = ConfigParser()

        try:
            self.parser.read(cfg_ini)
        except Exception as error:
            error_msg('Exception in {}.__init__:{}'.format(self.__class__.__name__,  str(error)))  

    def parse(self):

        cfg = {}
        for section in self.parser.sections():
            params = self.parser.items(section)
            cfg_section = {}
            for param in params:
                cfg_section[param[0]] = param[1]
            cfg[section] = cfg_section

        return cfg

class Mosiop:

    def __init__(self, ini = './mosiop.ini'):

        # parse the container depencies config file
        self.ini = Config(ini).parse()

        # initilize database
        self.db = Database(self.ini['database'])

        # initiate communication with microservices
        self.orchestrator = Client(self, self.ini['orchestrator']['url'])
        self.neuron = Client(self, self.ini['neuron']['url'])
        
        # instantiate testcase of bootsampling
        self.cfg = ConfigJson().associate(TestCase5)
        
        # instantiate controll
        self.mpc_int = MPC(self.cfg) 

        # instantiate boptest after MPC
        self.boptest = Boptest(self.cfg) 

        # get inter internal smpling rate  
        self.Ts = float(self.ini['mosiop']['int_ts'])

    def healthy(self):
        try:
            resp = self.neuron.request({'request':'health'})[1]
            return resp['meta']['health'] == HTTPStatus.OK.value
        except Exception as error:
            error_msg('Exception in {}.healthy:{}'.format(self.__class__.__name__,  str(error)))  
            return False   
        
    def handler(self, payload):

        notice_msg('Handler routine of {} running for incomping request of {}'.format(self.__class__.__name__,payload['meta']['source']))

        if payload['meta']['meta']['request'] == 'health':

            if self.healthy():                
                return {'health':HTTPStatus.OK}
            else:
                return {'health':HTTPStatus.BAD_GATEWAY}

        if payload['meta']['meta']['request'] == 'emu_config':
            
            return {'emu_config':json.dumps({'emu_name':self.boptest.name,'emu_sampling_rate':self.cfg['mosiop']['MPC']['temporal']['h']})}

        else:
            return HTTPStatus.BAD_REQUEST

    def internal(self, y_meas, r_ext):

        k=0
        y_0 = []
        perturb = -2 # dev from 20 degrees C

        while self.healthy():

            if k%200==0:
                error_factor = 1e-0
                perturb *= -1
                # set seed for reproducible results
                #random.seed(42)
                #self.mpc_int.set_parameter(np.array([4.81e-5, 1.63e-3, 1.33e-4, 0.1e-1, 2.82e7*error_factor, 9.40e6, 6.87e8*error_factor, 50, 50, 293.15+perturb, 1e-5, 1]))
                self.mpc_int.set_parameter(np.array([4.81e-5, 1.63e-3, 1.33e-4, 0.1e-1, 2.82e7*error_factor, 9.40e6, 6.87e8*error_factor, 50, 50, 293.15+perturb, 1e-6, 1]))
                #self.mpc_int.set_parameter(np.array([4.81e-5, 1.63e-3, 1.33e-4, 0.1e-1, 2.82e7*error_factor, 9.40e6, 6.87e8*error_factor, 50, 50, 295+random.randint(-10, 10), 1e-5, 1]))
            k = k + 1
            
            # solve MPC for control law
            r = r_ext
            df_ol, u_0, x = self.mpc_int.solve_open_loop(y_0, r)
 
            # evolve BOPTEST emulator
            r_ext, y_ext = self.boptest.evolve(u_0)
            
            # get state estimate
            if self.cfg['mosiop']['PLANT']['observer']['enable'] == 0:
                status, resp = self.neuron.request({'request':'adapt','t':[self.cfg['mosiop']['MPC']['temporal']['h']], 'u':u_0.to_list(),'y':[y_ext[0]],'r':list(r[0,:])})
                if status == HTTPStatus.OK.value:
                    y_0 = json.loads(resp['meta']['adapt'])['x']
            else:
                y_0 = np.array([y_ext[0]])
                            
            # log to database
            columns = np.hstack(('time',df_ol.columns.values[1:,]+'_0' ,df_ol.columns.values[1:,]+'_1','Ti_ext', 'Te_ext', 'Th_ext','ti_ref'))
            data = np.hstack([datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],np.hstack((df_ol.iloc[0,1:].values,df_ol.iloc[1,1:].values,y_ext,self.mpc_int.get_parameter()[9]))])
            df=pd.DataFrame(columns=columns,data=[data])
            
            # dump to database
            self.db.write('internal',self.boptest.name, df)
        
    def reset(self):
        if 'bacssaas' in self.db.list():
            self.db.drop('bacssaas')
    
    def main(self):

        notice_msg('Main routine of {} running'.format(self.__class__.__name__))

        # main execution loop
        
        while True:
            if self.healthy():
                self.internal(self.mpc_int.y0['y0'], self.boptest.forcast())
            else: 
                warning_msg('[{}] Mosiop offline.'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])) 
                time.sleep(1)
                
if __name__ == '__main__':
    Server(Mosiop()).main()