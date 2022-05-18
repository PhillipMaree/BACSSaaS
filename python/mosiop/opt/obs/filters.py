#from lib.core.ocp import OCP
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pdb
import casadi as ca

'''
A simple EKF implementation.

TODO: 
- Figure out general way of passing integrator.
- Incorporate developments of sysid.py into
  this class.



'''

class Filter(object):
    pass

class EKF(Filter):
    ''' . '''
    def __init__(self, ocp, \
                 **kwargs):
        
        self.params = kwargs.pop("params", None) 
        self.grid = kwargs.pop("grid", None) # grid for collocation.
        self.h = kwargs.pop("h", None)

        self.ocp = ocp # contains symbolic vars, dynamics etc.
        self.init_DMs()
        self.init_integrators()
        self.set_one_step_symbolic()
        self.set_h_x() 
        self.set_jac_f()
        self.set_jac_h()
        # 
        self.init_identity()
        self.init_covars(**kwargs)
        self.df = pd.DataFrame(columns=ocp.y.label())


    def init_identity(self):
        self.I = ca.DM.eye(self.ocp.y.dim())

    def init_covars(self, **kwargs):
        self.Q = kwargs.pop("Q", self.I)
        self.R = kwargs.pop("R", self.I)
        # initialize P_0 as Q
        self.P_prev = self.Q

    def init_DMs(self): # casadi DM's for io
        ''' Numeric input to filter. '''
        for name in ("y", "u", "z", "r", "p"):
            entity = getattr(self.ocp, name)
            setattr(self, name, ca.DM(entity.dim(), 1))

        
    def init_integrators(self):
        self.F = ca.integrator('F','collocation', \
                              {'z':self.ocp.z.var(), \
                                'x':self.ocp.y.var(), \
                                'p':ca.vertcat(self.ocp.u.var(), self.ocp.r.var(), self.ocp.p.var()), \
                                'ode':self.ocp.f_fn(), \
                                'alg':self.ocp.g_fn()},
                                {'tf':self.h,
                                'grid':self.grid}) # collocation


    def set_one_step_symbolic(self):
        ''' Integrate one step ahead (symbolically). '''
        self.x_next = self.F(x0=self.ocp.y.var(), \
                             z0=self.ocp.z.var(), \
                             p=ca.vertcat(self.ocp.u.var(), self.ocp.r.var(), self.ocp.p.var()))["xf"]

    def set_h_x(self):
        self.h_x = ca.Function("h_x", \
                               [self.ocp.y.var(), \
                                self.ocp.p.var()], \
                               [self.get_h_x_expr()], \
                               ["x", "p"], \
                               ["h_x"]) 

    def get_h_x_expr(self):
        return self.ocp.h_fn()

    def get_state_jac_expr(self):
        return ca.jacobian(self.x_next, self.ocp.y.var())

    def get_meas_jac_expr(self):
        return ca.jacobian(self.get_h_x_expr(), self.ocp.y.var())      

    def set_jac_f(self):
        self.jac_f = ca.Function('jac_f', \
                                [self.ocp.y.var(), \
                                 self.ocp.z.var(), \
                                  ca.vertcat(self.ocp.u.var(), self.ocp.r.var(), self.ocp.p.var())], \
                                [self.get_state_jac_expr()], \
                                ['x', 'z', 'p'], \
                                ['jac_f']) 

    def set_jac_h(self):
        self.jac_h = ca.Function('jac_h',
                                [self.ocp.y.var()], \
                                [self.get_meas_jac_expr()], \
                                ['x'], \
                                ['jac_h']) 

    def from_labels(self, df, y_0):
        ''' Populate DMs from labels. '''
        tup = []
        
        for name in ("y", "z", "u", "r", "p"): 
            DM = getattr(self, name)
            labels = getattr(self.ocp, name).label()
            for ndx, label in enumerate(labels):
                if name == "z":
                    DM[ndx] = y_0[ndx]
                elif name == "p":
                    DM[ndx] = self.params[ndx]
                else:
                    DM[ndx] = df.loc[0, label]
          
            tup.append(DM)

        return tuple(tup)

    """
    def __iter__(self):
        yield from [self.y, self.z, self.u, self.r, self.p]
    """

    # rethink this inteface
    def step(self, df, y_0, k):
        ''' 
        Assume general non-linear structure.
        Thus, A and C have to be looked up
        at each step.
         '''
        y, z, u, r, p = self.from_labels(df, y_0)


        A = self.jac_f(y, z, ca.vertcat(u, r, p))
        C = self.jac_h(y)
        h_x = self.h_x(y, p) # evaluate measurement function
        P_apriori = ca.mtimes([A, self.P_prev, ca.transpose(A)]) + self.Q

        K = ca.mtimes( \
                ca.mtimes(P_apriori, ca.transpose(C)), \
            ca.inv( \
                ca.mtimes([C, P_apriori, ca.transpose(C)]) + self.R))

        x_post = y + ca.mtimes(K, (z - h_x))

        x_post = np.array(x_post).reshape(-1)
        # store estimation result. TODO: check ordering of states.
        self.df.loc[k] = x_post
        self.P_prev = ca.mtimes((self.I - ca.mtimes(K, C)), P_apriori)

        return x_post

    def plot_results(self, boptest_df, \
                     boptest_map: dict, \
                     origin='2020-01-01'):
        ''' 
        Plot estimation results,
        compared with measurements.
         ''' 
        dt_index = pd.to_datetime(boptest_df.index, unit="s", origin=pd.Timestamp(origin))
        
        # temp fix
        keep = list(boptest_map.values())
        boptest_df = boptest_df[[col for col in keep]]
    
        boptest_df.index = dt_index
        df_ds = boptest_df.resample(rule=str(self.h) + "S").asfreq()

        # to align, leave out last
        df_ds = df_ds.iloc[:-1]
        self.df.index = df_ds.index

        fig, axes = plt.subplots(len(self.df.columns))
        
        for meas_col, est_col, ax in zip(df_ds.columns, self.df.columns, axes):
            labels = [self.latexize_meas(meas_col), self.latexize_est(est_col)]
            ax.plot(df_ds.index, self.df[est_col], color="r")
            ax.plot(df_ds.index, df_ds[meas_col], color="b")
            ax.legend(labels, loc='upper right', prop={'size': 10}, ncol=1)

        return fig, ax


    @staticmethod
    def latexize_meas(name):
        name, typ = name.split("_") # naming convention
        typ = "{" + typ + "}"
        return f"${name}_{typ}$"

    @staticmethod
    def latexize_est(name):
        name = "{" + name + "}"
        return f"$\hat{name}$"

