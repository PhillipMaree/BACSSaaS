from pickle import FALSE
from opt.mpc.mpc import ConfigJson
from opt.mpc.mpc import MPC
from cstr import Cstr

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def test_closed_loop():

    # read problem config file
    cfg = ConfigJson().associate(Cstr)

    # initialize MPC problem
    mpc = MPC(cfg)

    # solve MPC problem
    mpc.solve_closed_loop([], None, 0, True)

def test_observer():

    # read problem config file
    cfg = ConfigJson().associate(Cstr)

    # initialize MPC problem
    mpc = MPC(cfg)
    
    # closed-loop data frame
    df_cl = pd.DataFrame(columns=mpc.df_labels['df'])

    # default initial condition
    y_0 = mpc.y0['y0']

    for j in range(int(mpc.T/mpc.h)):

        # noisy full_measurement
        y_0 += np.random.normal(0,1,len(y_0))

        df_ol, _, y_0 = mpc.solve_open_loop(y_0)

        df_ol['time'] += mpc.h*j

        df_cl = df_cl.append(df_ol.loc[0:mpc.K,mpc.df_labels['df']], ignore_index=True)

    mpc.plot(df_cl, mpc.df_labels['y'], 'Closed-loop Differential') if len(mpc.df_labels['y']) else print('No closed-loop results for ODE')
    mpc.plot(df_cl, mpc.df_labels['z'], 'Closed-loop Algebraic') if len(mpc.df_labels['z']) else print('No closed-loop results for algebraic')
    mpc.plot(df_cl, mpc.df_labels['u'], 'Closed-loop Control') if len(mpc.df_labels['u']) else print('No closed-loop results for control')
    mpc.plot(df_cl, mpc.df_labels['r'], 'Closed-loop Reference') if len(mpc.df_labels['r']) else print('No closed-loop results for reference')

    plt.show()


if __name__ == '__main__':

    test_observer()
