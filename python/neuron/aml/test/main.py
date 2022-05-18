## let's import the relevant libraries
import glob
import os
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.integrate import odeint
import random

class NN(nn.Module):
    def __init__(self):
        super(NN, self).__init__()
        self.neural_stack = nn.Sequential(  nn.Linear(1, 10), nn.Sigmoid(),
                                            nn.Linear(10, 10), nn.Sigmoid(),
                                            nn.Linear(10, 10), nn.Sigmoid(),
                                            nn.Linear(10, 10), nn.Sigmoid(),
                                            nn.Linear(10, 10), nn.Sigmoid(),                               
                                            nn.Linear(10,1, bias=False) )
      
    def forward(self,x):
        logits = self.neural_stack(x)
        return logits


class Model():
    def __init__(self, samples_file):
        
        self.t_range = [0,3]
        self.x_init = [0,1]

        if os.path.exists(r'./data/{}'.format(samples_file)) is False:
            self.simulate([0,3], [0,1], 100, samples_file)  

        self.historical_samples = pd.read_json (r'./data/{}'.format(samples_file))
        self.historical_batch_size = len(self.historical_samples)

    # ODE of model
    def f(self,x, t):

            x0 = x[0]
            x1 = x[1]

            if isinstance(t,float):

                f0 = np.cos(t) + x0**2 + x1 - (1+t**2+np.sin(t)**2)
                f1 = 2*t - (1+t**2)*np.sin(t) +  x0*x1

            else:

                f0 = torch.cos(t) + x0**2 + x1 - (1+t**2+torch.sin(t)**2)
                f1 = 2*t - (1+t**2)*torch.sin(t) +  x0*x1

            return [f0, f1]

    # simulate
    def simulate(self, t_range, x_init, sample_cnt, filename=None):
        
        t = np.linspace(t_range[0],t_range[1], sample_cnt)
        x = odeint(self.f, x_init, t)

        df = pd.DataFrame(data=np.column_stack([t,x]), columns=['t','x0','x1'])
        if filename is not None:
            df.to_json(r'./data/{}'.format(filename))
            plt.plot(df['t'].values, (df.loc[:, df.columns != 't']).values)
            plt.show()
        return df

class PINN():
    def __init__(self, model, load_dnn=True):

        # device for processing
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print('Tensor deployment on the folling device: {}'.format(self.device))

        # extract model metadata
        self.model = model
        self.n = len(model.x_init)
        self.x0 = torch.Tensor( model.x_init)

        self.t_historical = torch.tensor(self.model.historical_samples['t'].values).float().to(self.device)
        self.x_historical = torch.tensor((self.model.historical_samples.loc[:, self.model.historical_samples.columns != 't']).values).float().to(self.device)

        # hyper parameters
        self.max_iter =1000                                                      # iterations over NN 
        self.batch_n = 1000                                                      # data batch size to iterate and learn over
        self.drawn_n = np.min([100,len(self.model.historical_samples)])          # random drawn historical batch size
        self.lr = 0.01                                                           # learning rate

        # instantiate NN for whole ODE dimension and attach to GPU is availible
        if load_dnn is True and glob.glob('*.pt'):
            self.NNi = [NN() for i in range(self.n)]
        else:
            self.NNi = [NN() for i in range(self.n)]
            [self.NNi[i].to(self.device).float() for i in range(self.n)]

        #instantiate optimizers
        self.adami = [torch.optim.Adam(self.NNi[i].parameters(), lr=self.lr) for i in range(self.n)]

        # trail functions for pinn
        self.XTi =  lambda t, x=None: [ (self.x0[i] if x is None else x[i]) + t*self.NNi[i].forward(t) for i in range(self.n)]


    def loss(self,i, t, tk, xk):

        t.requires_grad = True
        x = self.XTi(t)
        f = self.model.f(x, t)[i]
 
        # gradient calulations
        dXTidt = torch.autograd.grad(x[i], t, grad_outputs=torch.ones_like(x[i]),create_graph=True)[0]
        XTi = self.XTi(torch.reshape(tk,(len(tk),1)))[i]
        xk  = torch.reshape(xk[:,i],(len(xk[:,i]),1))
        
        # loss based on both boundary conditions and physics
        return torch.mean((dXTidt - f) ** 2)/self.batch_n + torch.mean((xk - XTi) ** 2)/self.drawn_n 

    def train(self):

        for j in range(self.max_iter):

            # sample random time drawn samples
            t = (self.model.t_range[1]-self.model.t_range[0])*torch.rand(self.batch_n,1).to(self.device)
            
            # draw sample
            tk, xk = self.draw(self.drawn_n)

            # zero gradients
            [self.adami[i].zero_grad() for i in range(self.n)]

            # evaluate loss
            lossi = [self.loss(i, t, tk, xk) for i in range(self.n)]

            # backward pass for weight updates
            [lossi[i].backward() for i in range(self.n)]

            # step optimizer
            [self.adami[i].step() for i in range(self.n)]

            # Print the iteration number
            if j % 100 == 0:
                print('Batch [{}] with loss [{}]'.format(j,lossi))

        # save trained model
        self.save()

    # simulate 
    def simulate(self, t_range, x_init, sample_cnt, filename=None):
        t = np.linspace(t_range[0],t_range[1], sample_cnt)
        x = odeint(self.model.f,x_init, t)

        df = pd.DataFrame(data=np.column_stack([t,x]), columns=['t','x0','x1'])
        if filename is not None:
            df.to_json(r'./data/{}'.format(filename))
            plt.plot(df['t'].values, (df.loc[:, df.columns != 't']).values)
            plt.show()
        return df

    # draw n random sample historical sample batch
    def draw(self, n):
        idx = random.sample(range(len(self.t_historical)),n)
        return self.t_historical[idx], self.x_historical[idx] 

    # save NN's
    def save(self):
        print('Save trained DNN\'s')
        [ torch.save(self.NNi[i], r'./trained/dnn_{}.pt'.format(i)) for i in range(self.n) ]

    # load NN's
    def load(self):
        print('Load trained DNN\'s')
        return [ torch.load(r'./trained/ddn_{}.pt'.format(i)) for i in range(self.n) ]

if __name__ == '__main__':
    
    model = Model(r'samples.json')
    nn = PINN(model)
    nn.train()
        
    # simulate to inspect learning
    x_real = model.simulate([0,5],[0,1],1000) 
    x_pinn = nn.simulate([0,5],[0,1],1000)

    fig, ax = plt.subplots(dpi=100)
    ax.plot(x_real['t'].values, x_real.loc[:, x_real.columns != 't'].values, label='True')
    ax.plot(x_pinn['t'].values, x_pinn.loc[:, x_pinn.columns != 't'].values,'--', label='PINN')
    ax.set_xlabel('$t$')
    ax.set_ylabel('$x$')
    plt.legend(loc='best')
    plt.show()