from configparser import ConfigParser
from api.aiohttp_api import Server, Client
from dashboard import Dashboard
from http import HTTPStatus

from datetime import datetime
import time

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

class ExtPlant():

    def __init__(self):
        # TODO API setup to external plant asset
        pass

    def advance(self, ctrl):
        # TODO advance external plant by control and return current state/measurement
        # TODD mqtt.put(ctrl)
        return True

    def measure(self):
        # TODO add functionality to measure plant
        return 0

class Orchestrator():
    
    def __init__(self, ini='./orchestrator.ini'):
    
        # parse the container depencies config file
        self.ini = Config(ini).parse()

        # microservice clients
        self.mosiop = Client(self, self.ini['mosiop']['url'])

        # TODO instantiate external plant
        self.plant = ExtPlant()

        #  run interactive dashboard
        Dashboard(self.ini).run()

        # Set extermal sampling rates
        self.Ts = float(self.ini['orchestrator']['ext_ts'])

    def healthy(self):
        try:
            resp = self.mosiop.request({'request':'health'})[1]
            return resp['meta']['health'] == HTTPStatus.OK.value
        except Exception as error:
            error_msg('Exception in {}.healthy:{}'.format(self.__class__.__name__,  str(error)))  
            time.sleep(1)
        return False 

    def handler(self, payload):

        notice_msg('Handler routine of {} running for incomping request of {}'.format(self.__class__.__name__,payload['meta']['source']))

    def external(self):

        while self.healthy():
            ext_meas = self.plant.measure()
            ext_ctrl = self.mosiop.request({'request':'advance','meta':{'ext_meas':ext_meas}})
            self.plant.advance( ext_ctrl )

            # sample external plant
            time.sleep(self.Ts) 
    
    
    def main(self):
        
        notice_msg('Main routine of {} running'.format(self.__class__.__name__))

        # main execution loop
        while True:
            if self.healthy():
                self.external()
            else:
                warning_msg('[{}] Orchestrator offline.'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])) 
                time.sleep(1)
            

if __name__ == '__main__':
    Server(Orchestrator()).main()