from opt.obs.filters import EKF
from opt.mpc.mpc import ConfigJson
from opt.mpc.mpc import MPC
from api.boptest_api import Boptest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pdb

import casadi as ca

from model import TestCase1, TestCase2, TestCase3, TestCase4

if __name__ == '__main__':

    # read mpc problem config file
    #cfg = ConfigJson().associate(TestCase4)
    #cfg = ConfigJson().associate(TestCase2)
    cfg = ConfigJson().associate(TestCase3)

    # initialize mpc
    mpc = MPC(cfg)

    # initialize BOPTEST
    boptest = Boptest(cfg)

    # frame for closed-loop results
    #df_cl = pd.DataFrame(columns=mpc.df_labels['df'])

    # mpc settings:
    T = cfg['mosiop']['MPC']['temporal']['T']
    h = cfg['mosiop']['MPC']['temporal']['h']
    N = cfg['mosiop']['MPC']['temporal']['N']

    # use those for boptest:
    boptest.set_step(h)
    boptest.set_forecast_params({"horizon": h*N, "interval": h})

    y_0 = cfg['mosiop']['PLANT']["initial"]["y0"]
    r_mpc = None

    R = ca.DM(2,2)
    R[0,0] = 1
    R[1,1] = 100

    # consider how to pass these settings to the filter
    # should have a config similar to mpc, boptest
    ekf = EKF(mpc.ocp, R=R, \
              grid=mpc.grid, \
              h=h, \
              params=cfg["mosiop"]["PLANT"]["parameters"])
    
    ################################ EKF #####################################

    for k in range(int(T/h)):

        # solve mpc for control law
        df_ol, u_0, _ = mpc.solve_open_loop(y_0, r_mpc, k)
        # evolve BOPTEST emulator
        r_mpc, y_0 = boptest.evolve(u_0)
        # estimate state with ekf
        y_0 = ekf.step(df_ol, y_0, k)



    fig, axs = boptest.plot_results(T)
    plt.show()
    
    fig, axs = ekf.plot_results(boptest.get_results(T), \
                                boptest.maps["z"])
    plt.show()
