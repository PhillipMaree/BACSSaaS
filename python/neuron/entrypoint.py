from configparser import ConfigParser
from api.aiohttp_api import Server, Client
from api.database_api import Database
from http import HTTPStatus

import torch

from datetime import datetime
import json, time, requests
import pandas as pd
import numpy as np

from pinn import PINN

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

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
            print('\033[91mException in {}.__init__:{}\033[0m'.format(self.__class__.__name__,  str(error)))    

    def parse(self):

        cfg = {}
        for section in self.parser.sections():
            params = self.parser.items(section)
            cfg_section = {}
            for param in params:
                cfg_section[param[0]] = param[1]
            cfg[section] = cfg_section

        return cfg


class Neuron:

    def __init__(self, ini = './neuron.ini'):

        # parse the container depencies config file
        self.ini = Config(ini).parse()

        # initilize database
        self.db = Database(self.ini['database'])

        # initiate communication with microservices
        self.mosiop = Client(self, self.ini['mosiop']['url'])

        # instantiate 
        self.nn = PINN({'db':self.db,'emu_cfg':self.emu_cfg(),'preserve':True})

    def emu_cfg(self):
        status = HTTPStatus.BAD_REQUEST
        while status == HTTPStatus.BAD_REQUEST:
            status, resp = self.mosiop.request({'request':'emu_config'})
            if status == HTTPStatus.OK:
                emu_cfg = json.loads(resp['meta']['emu_config'])
            else:
                warning_msg('[{}] Mosiop offline.'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
                time.sleep(1)
        return emu_cfg
    
    def healthy(self):
        try:
            assert(self.db.current()=='bacssaas')
            return True
        except Exception as error:
            error_msg('Exception in {}.healthy:{}'.format(self.__class__.__name__,  str(error)))  
        return False 
             
    def handler(self, payload):

        #notice_msg('Handler routine of {} running for incomping request of {}'.format(self.__class__.__name__,payload['meta']['source']))

        if payload['meta']['meta']['request'] == 'health':
            
            return {'health':HTTPStatus.OK}

        if payload['meta']['meta']['request'] == 'adapt':
            
            # concat argument
            v = torch.tensor(np.hstack((payload['meta']['meta']['t'],payload['meta']['meta']['u'],payload['meta']['meta']['y'],payload['meta']['meta']['r'])))

            # apply scaling
            x = self.nn.predict(v)

            return {'adapt':json.dumps({'x':x.tolist()})}

    def main(self):

        notice_msg('Main routine of {} running'.format(self.__class__.__name__))
       
        while True:
            
            if self.healthy():
                self.nn.train()
                notice_msg('{} Idle..'.format(self.__class__.__name__))
            else:
                warning_msg('[{}] Neuron offline.'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])) 
                
            time.sleep(1)

if __name__ == '__main__':
    Server(Neuron()).main()


    


    