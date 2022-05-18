import matplotlib.pyplot as plt
from opt.debug import Debug
from opt.mpc.nlp import NLP
import pandas as pd
import numpy as np
import json

class MPC(NLP):

    def __init__(self, cfg):

        # extract relevant config information
        cfg = cfg['mosiop']

        # extract parameters required for MPC
        try:
            assert( "T" in cfg['MPC']['temporal'].keys()), "MPC"
        except AssertionError as e:
            e.args += ('User need to supply final simulation time <MPC:temporal:T>')
            raise
        self.T = cfg['MPC']['temporal']['T']

        try:
            assert( "h" in cfg['MPC']['temporal'].keys()), "MPC"
        except AssertionError as e:
            e.args += ('User need to supply sampling base time <MPC:temporal:h>')
            raise
        self.h = cfg['MPC']['temporal']['h']

        try:
            assert( "order" in cfg['NLP']['collocation'].keys()), "NLP"
        except AssertionError as e:
            e.args += ('User need to supply collocation order <NLP:collocation:order>')
            raise
        self.K = cfg['NLP']['collocation']['order']

        # initialize base class
        NLP.__init__(self, cfg)

        # labelling operations
        self.df_labels = self.get_labels()
        self.df_cl = pd.DataFrame(columns=self.df_labels['df'])

    def solve_open_loop(self, y_0=[], r_fn=None, k=0, plot=False):

        df_ol, u_0, y_1 = self.solve_ocp(y_0, r_fn if r_fn is not None else (self.ocp.r_fn(k) if self.ocp.r_fn_active else np.array([])), k)

        if plot:

            self.plot(df_ol, self.df_labels['y'], 'Open-loop Differential') if len(self.df_labels['y']) else print('No open-loop results for ODE')
            self.plot(df_ol, self.df_labels['z'], 'Open-loop Algebraic') if len(self.df_labels['z']) else print('No open-loop results for algebraic')
            self.plot(df_ol, self.df_labels['u'], 'Open-loop Control') if len(self.df_labels['u']) else print('No open-loop results for control')
            self.plot(df_ol, self.df_labels['r'], 'Open-loop Reference') if len(self.df_labels['r']) else print('No open-loop results for reference')

            plt.show()

        return df_ol, u_0, y_1

    def solve_closed_loop(self, y_0=[], r_fn=None, k=0, plot=False):

        if r_fn is not None:
            self.ocp.r_fn_active = True
            if hasattr(self.ocp, 'r_fn') is True:
                Debug.MOSIOP_NOTICE('Overwrite previously defined function <{}> for class<{}>'.format('r_fn(self,k)', self.ocp.__class__.__name__))
            else:
                Debug.MOSIOP_NOTICE('Add externally supplied reference function <{}> for class<{}>'.format('r_fn(self,k)', self.ocp.__class__.__name__))
            self.ocp.r_fn = r_fn

        for j in range(k,int(self.T/self.h)):

            df_ol, _, y_0 = self.solve_open_loop(y_0, r_fn(j) if r_fn is not None else np.array([]), j)

            df_ol['time'] += self.h*j

            self.df_cl = self.df_cl.append(df_ol.loc[0:self.K,self.df_labels['df']], ignore_index=True)

        if plot:

            self.plot(self.df_cl, self.df_labels['y'], 'Closed-loop Differential') if len(self.df_labels['y']) else print('No closed-loop results for ODE')
            self.plot(self.df_cl, self.df_labels['z'], 'Closed-loop Algebraic') if len(self.df_labels['z']) else print('No closed-loop results for algebraic')
            self.plot(self.df_cl, self.df_labels['u'], 'Closed-loop Control') if len(self.df_labels['u']) else print('No closed-loop results for control')
            self.plot(self.df_cl, self.df_labels['r'], 'Closed-loop Reference') if len(self.df_labels['r']) else print('No closed-loop results for reference')

            plt.show()

        return self.df_cl, 0, 0

    def simulate(self, y0, u, p=[]):

        if len(p) ==0:
            p = self.get_parameter()
        return self.ocp.sim(y0, u, p)

    def plot(self, df, labels, title):

        n = len(labels)
        row = n if n<=3 else int(np.ceil(np.sqrt(n)))
        col = 1 if n<=3 else int(np.ceil(n/row))

        fig, axs = plt.subplots(row,col)

        if n==1:
            axs.plot(df['time'], df[labels[0]], label=labels[0], marker='.' )
            axs.legend(loc='upper right',prop={'size': 10},ncol=1,frameon=False)
        elif n<=3:
            for i in range(n):
                axs[i].plot(df['time'], df[labels[i]], label=labels[i], marker='.' )
                axs[i].legend(loc='upper right',prop={'size': 10},ncol=1,frameon=False)
        else:
            for r in range(row):
                for c in range(col):

                    axs[r,c].plot(df['time'], df[labels[r*col+c]], label=labels[r*col+c], marker='.' )
                    axs[r,c].legend(loc='upper right',prop={'size': 10},ncol=1,frameon=False)
                    if (r*col + c + 1) == n :
                        break

        fig.text(0.5, 0.04, 'time', ha='center', va='center')
        fig.suptitle(title)


class ConfigJson():

    def __init__(self,filename='./config.json'):

        try:

            fh = open(filename)
            data = json.load(fh)

            self.config = {}
            for key in data.keys():
                self.config[key] = data[key]

        except:

            print('Could not open {}!'.format(filename))
            exit(1)

    def associate(self, ocp):

        cfg_ID = ocp().cfg_ID
        if int(cfg_ID):
            self.config = self.config[cfg_ID]
        self.config['mosiop']['PLANT']['ocp'] = ocp

        return self.config


