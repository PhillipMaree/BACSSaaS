from opt.debug import Debug
import casadi as ca
import numpy as np


class OCP:

    def __init__(self, cfg=None, cfg_ID='0'):

        # associated configuration ID (defualt 0)

        self.cfg_ID = cfg_ID
        if cfg is None:
            return

        # extract parameters required for MPC
        self.y0 = cfg['PLANT']['initial']['y0']

        try:
            assert( "h" in cfg['MPC']['temporal'].keys()), "MPC"
        except AssertionError as e:
            e.args += ('User need to supply sampling base time <MPC:temporal:h>')
            raise
        self.h = cfg['MPC']['temporal']['h']

        try:
            assert( "non_uniform_gain" in cfg['MPC']['temporal'].keys()), "MPC"
        except AssertionError as e:
            e.args += ('User need to spesify non-uniform gain (o for uniform) <MPC:temporal:non_uniform_gain>')
            raise
        self.non_uniform_gain = cfg['MPC']['temporal']['non_uniform_gain']

        try:
            assert( "N" in cfg['MPC']['temporal'].keys()), "MPC"
        except AssertionError as e:
            e.args += ('User need to prediction horizon <MPC:temporal:N>')
            raise

        self.N = cfg['MPC']['temporal']['N']
        self.Ts = cfg['MPC']['temporal']['h']

        # ocp variables

        hk = np.exp(np.linspace(0,self.N-1,self.N)*self.non_uniform_gain)*self.h
        tf = np.cumsum(hk)[-1]

        self.t = Mx('t')   # time
        self.t.add('t', 0, tf)

        self.y = Mx('y')   # differential equations
        self.z = Mx('z')   # algebraic equations
        self.u = Mx('u')   # control piece-wise constrant
        self.r = Mx('r')   # reference piece-wise constrant
        self.p = Mx('p')   # parameters constants

        # incorporate user defined variables
        self.n_y_label = self.y.label()
        self.n_z_label = self.z.label()
        self.n_u_label = self.u.label()
        self.n_r_label = self.r.label()
        self.n_p_label = self.p.label()

        self.init()

        # cost funcitonals

        self.l = self.l_fn()
        self.m = self.m_fn()

        # DAE equations

        self.f = self.f_fn()    # ODE's
        self.g = self.g_fn()    # equality constraints
        self.h = self.h_fn()    # in-equality constraints
        self.c = self.c_fn()    # periodical constraints

        # detect reference functionality
        self.r_fn_active = True if self.r.dim() > 0 else False

        if self.r_fn_active:
            if hasattr(self,'r_fn'):
                Debug.MOSIOP_NOTICE('Detected embedded internal reference function <{}> for class<{}>'.format('r_fn(self,k)', self.__class__.__name__))
            else:
                Debug.MOSIOP_WARNING('No internal reference function <{}> is supplied for class<{}>. Supply externally'.format('r_fn(self,k)', self.__class__.__name__))

    def l_fn(self):
        return 0

    def m_fn(self):
        return 0

    def f_fn(self):
        return ca.vertcat()

    def g_fn(self):
        return ca.vertcat()

    def h_fn(self):
        return ca.vertcat()

    def c_fn(self):
        return ca.vertcat()

class Mx:

    def __init__(self, type):

        self.mx = ca.MX()
        self.type = type
        self.disc = []
        
        self.mx0 = []
        self.min = []
        self.max = []
        self.dmx = []

        pass

    def add(self, disc, *args):

        self.mx = ca.vertcat(self.mx, ca.MX.sym(disc, 1, 1))
        self.disc.append(disc)

        if len(args) == 1:
            self.min.append(args[0])
            self.max.append(args[0])
            self.mx0.append(args[0])
            self.dmx.append(0)
        elif len(args) == 2:
            self.min.append(args[0])
            self.max.append(args[1])
            self.mx0.append((args[0]+args[1])/2)
            self.dmx.append(0)
        elif len(args) == 3:
            self.min.append(args[0])
            self.max.append(args[1])
            self.mx0.append(args[2])
            self.dmx.append(0)
        elif len(args) == 4:
            if self.type == 'u':
                self.min.append(args[0])
                self.max.append(args[1])
                self.mx0.append(args[2])
                self.dmx.append(args[3])
            else:

                Debug.MOSIOP_WARNING('Rate penalty weights not configurable for variable type {}. Support only control.'.format(self.type))
        else:
            self.min.append(0)
            self.max.append(0)
            self.mx0.append(0)
            self.dmx.append(0)

            Debug.MOSIOP_WARNING('Variable type {} supports only [min, max, mx0 (=(max-min)/2), dmx (=0)]'.format(self.type))

    def get(self, disc):
        return self.mx[self.disc.index(disc)]

    def var0(self):
        return self.mx0

    def var(self):
        return self.mx

    def name(self):
        return self.type

    def lb(self):
        return self.min

    def ub(self):
        return self.max

    # differential weight penalty
    def dw(self):
        return self.dmx

    def dim(self):
        return len(self.disc)

    def label(self):
        return self.disc