import casadi as ca
import numpy as np

class KF():
    def __init__(self, cfg):

        self.y_hat = ca.DM(np.array(cfg['initial']['y0']))
        self.y_meas_n = np.count_nonzero(cfg['observer']['param']['H'])

        self.A = ca.Function('A', [cfg['ocp'].y.var(), cfg['ocp'].u.var(), cfg['ocp'].z.var(), cfg['ocp'].r.var(), cfg['ocp'].p.var()], [ca.jacobian(cfg['ocp'].f, cfg['ocp'].y.var())], ['y', 'u', 'z', 'r', 'p'], ['A'])
        self.Q = ca.DM(np.diag(cfg['observer']['param']['Q']))
        self.R = ca.DM(np.diag(cfg['observer']['param']['R']))
        self.H = ca.DM(np.diag(cfg['observer']['param']['H']))
        self.P = ca.DM(np.diag(np.ones(cfg['ocp'].y.dim())))

    def update(self, args):

        A = self.A(args['var']['x0'],args['var']['u0'],args['var']['z0'],args['var']['r0'], args['p'])
        y_meas = args['y_meas']
        
        # kalman prediction
        x_0 = args['var']['x1'].values
        P_0 = A*self.P*A.T + self.Q

        # kalman update
        
        y_err = y_meas - self.H*x_0 if len(y_meas) == self.y_meas_n else self.H*0
        K = P_0*self.H.T/(self.R + self.H*P_0*self.H.T)
        self.y_hat = ca.diag(x_0 + K*y_err).T
        self.P = (ca.DM_eye(self.P.size(1)) - K*self.H)*P_0
        
        # conditioning of diagonal matrix
        if min(np.diag(self.P)) < 1e-7:
           self.P += 1e-7*np.eye(self.P.shape)

    def sample(self):
        return np.array(self.y_hat).flatten()

class OBS():
    def __init__(self, cfg):
            self.use_observer, self.cfg = (True, cfg['PLANT']['observer']) if ('observer' in cfg['PLANT'] and cfg['PLANT']['observer']['enable']) else (False, None)

            if self.use_observer and self.cfg['name'] == 'kf':
                self.observer = KF(cfg['PLANT']) 
