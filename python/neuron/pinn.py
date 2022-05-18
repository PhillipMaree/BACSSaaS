from configparser import ConfigParser

from matplotlib import scale
from api.database_api import Database
from datetime import datetime
import glob

import torch.nn as nn
import numpy as np
import torch

def debug_msg(msg):
    print('\033[95m'+msg+'\033[0m\n') 

def notice_msg(msg): 
    print('\033[94m'+msg+'\033[0m\n') 

def warning_msg(msg): 
    print('\033[93m'+msg+'\033[0m\n')   

def error_msg(msg):
    print('\033[91m'+msg+'\033[0m\n')

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

class NN(nn.Module):
    def __init__(self):
        super(NN, self).__init__()
        self.neural_stack = nn.Sequential(  nn.Linear(5, 10), nn.ReLU(),
                                            nn.Linear(10, 20), nn.ReLU(),
                                            nn.Linear(20, 10), nn.ReLU(),                               
                                            nn.Linear(10, 1, bias=True) )
      
    def forward(self,x):        
        logits = self.neural_stack(x.float())
        return logits

class Model():
    def __init__(self):
        
        # scaling constant prior to PINN learning
        self.t_scale = 3600
        self.T_scale = 4e2
        self.phi_h_scale = 1e5
        self.phi_s_scale = 1e2

        # order of RC model
        self.n = 3

        # parameters
        self.Rie = 4.81e-5       # Thermal resistance, interior and envelope [K/W]
        self.Rea = 1.63e-3       # Thermal resistance, envelope and ambient [K/W]
        self.Rih = 1.33e-4       # Thermal resistance, interior and heaterp [K/W]
        self.Ria = 0.1e-1        # Thermal resistance, interior and ambient [K/W]
        self.Ci = 2.82e7         # Thermal capacitance of interior [J/W]
        self.Ch = 9.40e6         # Thermal capacitance of heater [J/W]
        self.Ce = 6.87e8         # Thermal capacitance of envelope (inf.) [J/W]
        self.Ai = 50             # Equivalent window area of interior [m2]
        self.Ae = 50             # Equivalent window area of envelope [m2]
  
    # ODE of model
    def f(self, x, u, r):

        # process states
        Ti = x[0]
        Te = x[1]
        Th = x[2]

        # process controls
        phi_h = u

        # process references
        Ta = r[0]
        phi_s = r[1]

        # ode
        dTidt = (Te - Ti)/(self.Rie*self.Ci) + (Th - Ti)/(self.Rih*self.Ci) + (Ta - Ti)/(self.Ria*self.Ci) + self.Ai*phi_s/self.Ci
        dTedt = (Ti - Te)/(self.Rie*self.Ce) + (Ta - Te)/(self.Rea*self.Ce) + self.Ae*phi_s/self.Ce
        dThdt = (Ti - Th)/(self.Rih*self.Ch) + phi_h/self.Ch

        return torch.hstack([dTidt, dTedt, dThdt])
        
class Batch():
    def __init__(self, cfg):
        self.active = False
        self.t = cfg['emu_cfg']['emu_sampling_rate']
        if cfg['db'].has_table('internal',cfg['emu_cfg']['emu_name']):
             self.active = True
             self.df =  cfg['db'].sample('internal',cfg['emu_cfg']['emu_name'], cfg['batch_n']+1)
        

    def size(self):

        return (self.df.shape[0]-1) if self.active else 0
    
    def sample(self, j):

         t = np.array(self.t)
         x = np.array(self.df.iloc[j,:][['ti_0','te_0','th_0']])
         u = np.array(self.df.iloc[j,:]['phi_h_0'])
         y = np.array(self.df.iloc[j+1,:]['ti_ext'])
         r = np.array(self.df.iloc[j,:][['ta_0','phi_s_0']])

         return {'t':t,'x':x,'u':u,'y':y,'r':r}
    
class PINN(Model):
    def __init__(self, cfg):
        Model.__init__(self)
        self.cfg = cfg

        # hyper parameters
        self.max_epoch =100      # iterations over NN 
        self.batch_n = 500        # data batch size to iterate and learn over
        self.lr = 0.1            # learning rate

        # instantiate NN for whole ODE dimension and attach to GPU is availible
        if cfg['preserve'] is True and glob.glob('./trained/*.pt'):
            self.NNi = self.load()
        else:
            self.NNi = [NN().float() for i in range(self.n)]

        #instantiate optimizers
        self.adami = [torch.optim.Adam(self.NNi[i].parameters(), lr=self.lr) for i in range(self.n)]

        # trail functions for pinn
    def psi(self, v):
        
        # normalizaiton of PINN inputs
        v = v/torch.tensor([self.t_scale, self.phi_h_scale, self.T_scale, self.T_scale, self.phi_s_scale])
        t = v[0]
        y = v[2]

        # eval PINN's
        return [ y + t*self.NNi[i].forward(v) for i in range(self.n)]
           
    def predict(self, v):

        # forward pass on trail function
        psi = self.psi(v)

        # correct for normalization
        psi = [val.item() for val in psi]
        x = np.array(psi)*np.array([self.T_scale, self.T_scale, self.T_scale])

        return x

    # scaled
    def loss(self,arg):

        i = arg['i']
        
        t = torch.tensor(arg['v']['t'].astype(np.float64))
        t.requires_grad = True

        x = torch.tensor(arg['v']['x'].astype(np.float64))
        u = torch.tensor(arg['v']['u'].astype(np.float64))
        y = torch.tensor(arg['v']['y'].astype(np.float64))
        r = torch.tensor(arg['v']['r'].astype(np.float64))

        psi = self.psi(torch.hstack((t,u,y,r)))

        dpsidt = torch.autograd.grad(psi[i], t, grad_outputs=torch.ones_like(psi[i]),create_graph=True)[0]
        f = self.f(x, u, r)/self.T_scale
        
        return (psi[0]-y/self.T_scale)**2 + (dpsidt - f[i])**2 
        
    def train(self):

        # number of epochs used for training
        for e in range(self.max_epoch):
            
            # sample random time drawn samples
            batch = Batch({'db':self.cfg['db'],'emu_cfg':self.cfg['emu_cfg'],'batch_n':self.batch_n})

            # return if batch cannot be sampled
            if batch.active is False or batch.size() < self.batch_n:
                return

            # zero gradients
            [self.adami[i].zero_grad() for i in range(self.n)]

            # evaluate loss over ODE
            losse = [self.loss({'i':i, 'v':batch.sample(0)}) for i in range(self.n)]
            
            with open('trained/losse.csv','a') as file:
                file.write('{}\n'.format(np.sum([losse[i].item() for i in range(self.n)])))
            
            for j in range(1,batch.size()):
                
                lossj = [self.loss({'i':i, 'v':batch.sample(j)}) for i in range(self.n)]
                losse = [(losse[i] + lossj[i]) for i in range(self.n)]

                with open('trained/losse.csv','a') as file:
                    file.write('{}\n'.format(np.sum([lossj[i].item() for i in range(self.n)])))

            # normalize over batch
            losse = [losse[i]/batch.size() for i in range(self.n)]

            # backward pass for weight updates
            [losse[i].backward() for i in range(self.n)]
             
            # step optimizer
            [self.adami[i].step() for i in range(self.n)]
             
            # verbose
            losse = np.sum([losse[i].item() for i in range(self.n)])
            notice_msg('Epoch [{}/{}] with loss {}'.format(e,batch.size(),losse))

        # safe dnn
        if self.cfg['preserve']:
            self.save()

    # save NN's
    def save(self):
        [ torch.save(self.NNi[i], r'./trained/dnn_{}.pt'.format(i)) for i in range(self.n) ] 

    # load NN's
    def load(self):
        return [ torch.load(r'./trained/dnn_{}.pt'.format(i)) for i in range(self.n) ]

if __name__ == '__main__':

    from entrypoint import Config

    nn = PINN(Database(Config('neuron.ini').parse()['database']),'testcase5')
    nn.train()
