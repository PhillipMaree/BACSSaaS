from opt.debug import Debug
from opt.obs.obs import OBS
import matplotlib.pyplot as plt
import pandas as pd
import casadi as ca
import numpy as np
import warnings

np.set_printoptions(precision=5)
np.set_printoptions(threshold=np.inf)
pd.set_option('display.max_columns', None)

#
# construct the NLP from the inherited OCP problem. NLP formulation to the terminology of Betts, 2010, Ch4
#

class NLP(OBS):

    def __init__(self, cfg):
        

        # extract parameters required for NLP (circular instantiation)
        cfg['PLANT']['ocp'] = self.ocp = cfg['PLANT']['ocp'](cfg)
        
        #  instantiate oberver
        OBS.__init__(self, cfg)

        try:
            assert( "y0" in cfg['PLANT']['initial'].keys()), "PLANT"
        except AssertionError as e:
            e.args += ('Need to supply initial state conditions <PLANT:initial:y0>')
        self.y0 = {'y0':cfg['PLANT']['initial']['y0']}

        try:
            assert( "free" in cfg['PLANT']['initial'].keys()), "PLANT"
        except AssertionError as e:
            e.args += ('Need to supply if initial state conditions are free <PLANT:initial:free>')
        self.y0['fixed'] = False if cfg['PLANT']['initial']['free'] else True

        try:
            assert( "warmstart" in cfg['NLP']['options'].keys()), "NLP"
        except AssertionError as e:
            e.args += ('User need to spesify warmstart requirements <NLP:options:warmstart>')
            raise
        self.ipopt_warmstart = cfg['NLP']['options']['warmstart']

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

        try:
            assert( "method" in cfg['NLP']['collocation'].keys()), "NLP"
        except AssertionError as e:
            e.args += ('User need to spesify collocation method <NLP:collocation:method>')
            raise
        self.method = cfg['NLP']['collocation']['method']

        try:
            assert( "order" in cfg['NLP']['collocation'].keys()), "NLP"
        except AssertionError as e:
            e.args += ('User need to spesify collocation order <NLP:collocation:order>')
            raise
        self.K = cfg['NLP']['collocation']['order']

        try:
            assert( "max_iter" in cfg['NLP']['options'].keys()), "NLP"
            self.max_iter = cfg['NLP']['options']['max_iter']
        except AssertionError as e:
            self.max_iter = 3000

        try:
            assert( "linear_solver" in cfg['NLP']['options'].keys()), "NLP"
        except AssertionError as e:
            e.args += ('User need to linear solve to be used <NLP:options:linear_solver>')
            raise
        self.linear_solver = cfg['NLP']['options']['linear_solver']

        try:
            assert( "verbose" in cfg['NLP']['options'].keys()), "NLP"
        except AssertionError as e:
            e.args += ('User need to spesify verbose level <NLP:options:verbose>')
            raise
        self.ipopt_verbose = cfg['NLP']['options']['verbose']

        try:
            assert( "warmstart" in cfg['NLP']['options'].keys()), "NLP"
        except AssertionError as e:
            e.args += ('User need to spesify warmstart requirements <NLP:options:warmstart>')
            raise
        self.ipopt_warmstart = {'enabled':True if cfg['NLP']['options']['warmstart'] else False}

        # collocation and sampling horizon setup
        self.hk = np.exp(np.linspace(0,self.N-1,self.N)*self.non_uniform_gain)*self.h
        self.tk = np.concatenate([np.array([0]),np.cumsum(self.hk)])
        self.B, self.C, self.D, self.tau, self.debug = Collocation({'K':self.K, 'method':self.method}).coef()

        # nlp spesific equation dim
        self.l_n = 1                             # lagrange term dimension
        self.m_n = 1                             # mayer term dimension

        self.f_n = self.ocp.f.shape[0]           # ODE term dimension
        self.g_n = self.ocp.g.shape[0]           # equality term dimension
        self.h_n = self.ocp.h.shape[0]           # in-equality term dimension
        self.c_n = self.ocp.c.shape[0]           # periodical constraiself.P = ca.DM(np.diag(np.ones(cfg['ocp'].y.dim())))t

        # nlp specific variables dim
        self.var = self.extract()

        # construct casadi function handlers
        self.ca_f = ca.Function('f', [self.ocp.t.var(), self.ocp.y.var(), self.ocp.u.var(), self.ocp.z.var(), self.ocp.r.var(), self.ocp.p.var()], [self.ocp.f], ['t', 'y', 'u', 'z', 'r', 'p'], ['f'])
        self.ca_g = ca.Function('g', [self.ocp.t.var(), self.ocp.y.var(), self.ocp.u.var(), self.ocp.z.var(), self.ocp.r.var(), self.ocp.p.var()], [self.ocp.g], ['t', 'y', 'u', 'z', 'r', 'p'], ['g'])
        self.ca_h = ca.Function('h', [self.ocp.t.var(), self.ocp.y.var(), self.ocp.u.var(), self.ocp.z.var(), self.ocp.r.var(), self.ocp.p.var()], [self.ocp.h], ['t', 'y', 'u', 'z', 'r', 'p'], ['h'])
        self.ca_c = ca.Function('c', [self.ocp.y.var()], [self.ocp.c], ['y'], ['c'])

        self.ca_l = ca.Function('l', [self.ocp.t.var(), self.ocp.y.var(), self.ocp.u.var(), self.ocp.z.var(), self.ocp.r.var(), self.ocp.p.var()], [self.ocp.l], ['t', 'y', 'u', 'z', 'r', 'p'], ['l'])
        self.ca_m = ca.Function('m', [self.ocp.t.var(), self.ocp.y.var(), self.ocp.u.var(), self.ocp.z.var(), self.ocp.r.var(), self.ocp.p.var()], [self.ocp.m], ['t', 'y', 'u', 'z', 'r', 'p'], ['m'])

        # integration handler for simulations
        self.grid = self.h*self.tau
        self.ca_i = ca.integrator( 'F','collocation',
                                  {'x':self.ocp.y.var(),
                                   'p':ca.vertcat(self.ocp.u.var(),self.ocp.r.var(),self.ocp.p.var()) if self.ocp.r_fn_active else ca.vertcat(self.ocp.u.var(),self.ocp.p.var()),
                                   'ode':self.ocp.f },
                                  {'tf':self.h,
                                   'grid':self.grid})

        #
        # NLP problem formulation
        #

        # create nlp variable

        self.create_nlp_framework()

        # instantiate nlp problem

        self.init_nlp()

        # object to extract NLP optimal solution

        self.parse = Parse(self.var)

        # initialize parameters if supplied

        if "parameters" in cfg['PLANT'].keys():
            self.set_parameter(np.array(cfg['PLANT']['parameters']))

        # update config with NLP var info
        cfg['var_info'] = self.var_info()

    #
    # helper function to add to nlp structure
    #

    def add_time(self, t_i_j):
        self.nlp_struct['t'].append(t_i_j)

    def add_nlp_var(self, var, lb, ub, var0):
        self.nlp_struct['z'].append(var)
        self.nlp_struct['lbz'].append(lb)
        self.nlp_struct['ubz'].append(ub)
        self.nlp_struct['z0'].append(var0)

    def add_nlp_res(self, res, lbg, ubg):
        self.nlp_struct['g'].append(res)
        self.nlp_struct['lbg'].append(lbg)
        self.nlp_struct['ubg'].append(ubg)

    def add_cost(self, cost):
        self.nlp_struct['J'] += cost

    #
    # setup solver structure
    #

    def init_solver(self):

        self.nlp_struct['z'] = ca.vertcat(*self.nlp_struct['z'])
        self.nlp_struct['g'] = ca.vertcat(*self.nlp_struct['g'])
        self.nlp_struct['z0'] = np.concatenate(self.nlp_struct['z0'])
        self.nlp_struct['lbz'] = np.concatenate(self.nlp_struct['lbz'])
        self.nlp_struct['ubz'] = np.concatenate(self.nlp_struct['ubz'])
        self.nlp_struct['lbg'] = np.concatenate(self.nlp_struct['lbg'])
        self.nlp_struct['ubg'] = np.concatenate(self.nlp_struct['ubg'])

        prob = {'f': self.nlp_struct['J'], 'x': self.nlp_struct['z'],'g': self.nlp_struct['g']}
        if self.ipopt_warmstart['enabled']:
            opts = {'print_time':0,
                    'ipopt':{'linear_solver':self.linear_solver,
                             'print_level':self.ipopt_verbose,
                             'sb':'yes',
                             'warm_start_init_point':'yes',
                             'max_iter':self.max_iter}}
                             #'print_timing_statistics':'yes'}}
        else:
            opts = {'print_time':0,
                    'ipopt':{'linear_solver':self.linear_solver,
                             'print_level':self.ipopt_verbose,
                             'sb':'yes',
                             'max_iter':self.max_iter }}

        self.nlp_struct['solver'] = ca.nlpsol('solver', 'ipopt', prob, opts)

    #
    # initialize nlp skeleton
    #

    def create_nlp_framework(self):

        # nlp structure

        self.nlp_struct = {'t': [], 'J': 0, 'z': [], 'z0': [], 'lbz': [], 'ubz': [], 'g': [], 'lbg': [], 'ubg': [], 'solver': lambda z0, lbz, ubz, lbg, ubg: ()}

        # construct empty NLP variable structure
        for i in range(self.N):

            # add time on phase boundary

            self.add_time(self.tk[i])

            # add time on collocation points

            for j in range(1, self.K+1):
                self.add_time(self.tk[i] + self.tau[j]*self.hk[i])

            if self.var['y']['dim']:

                # add differential variable on phase boundary

                self.add_nlp_var(ca.MX.sym( self.ocp.y.name() + '_' + str(i), self.var['y']['dim'] ), self.ocp.y.lb(), self.ocp.y.ub(), self.ocp.y.lb())

                # add differential collocation variables

                for j in range(1, self.K+1):
                    self.add_nlp_var(ca.MX.sym( self.ocp.y.name() + '_' + str(i) + '_' + str(j), self.var['y']['dim'] ), self.ocp.y.lb(), self.ocp.y.ub(), self.ocp.y.lb())

            if self.var['u']['dim']:

                # add control variable

                self.add_nlp_var(ca.MX.sym( self.ocp.u.name() + '_' + str(i), self.var['u']['dim'] ), self.ocp.u.lb(), self.ocp.u.ub(), self.ocp.u.lb())

            if self.var['z']['dim']:

                # add algebraic variable on phase boundary

                self.add_nlp_var(ca.MX.sym( self.ocp.z.name() + '_' + str(i), self.var['z']['dim'] ), self.ocp.z.lb(), self.ocp.z.ub(), self.ocp.z.lb())

                # add algebraic collocation variables

                for j in range(1, self.K+1):
                    self.add_nlp_var(ca.MX.sym( self.ocp.z.name() + '_' + str(i) + '_' + str(j), self.var['z']['dim'] ), self.ocp.z.lb(), self.ocp.z.ub(), self.ocp.z.lb())

            if self.var['r']['dim']:

                # add reference variable

                self.add_nlp_var(ca.MX.sym( self.ocp.r.name() + '_' + str(i), self.var['r']['dim'] ), self.ocp.r.lb(), self.ocp.r.ub(), self.ocp.r.lb())

        #
        # add terminal variables
        #

        # terminal time

        self.add_time(self.tk[self.N])

        if self.var['y']['dim']:

            # terminal differential variable

            self.add_nlp_var(ca.MX.sym( self.ocp.y.name() + '_' + str(self.N), self.var['y']['dim']), self.ocp.y.lb(), self.ocp.y.ub(), self.ocp.y.lb())

        if self.var['z']['dim']:

            # terminal algebraic variable

            self.add_nlp_var(ca.MX.sym( self.ocp.z.name() + '_' + str(self.N), self.var['z']['dim']), self.ocp.z.lb(), self.ocp.z.ub(), self.ocp.z.lb())

        if self.var['p']['dim']:

            # add constant parameters

            self.add_nlp_var(ca.MX.sym( self.ocp.p.name(), self.var['p']['dim'] ), self.ocp.p.lb(), self.ocp.p.ub(), self.ocp.p.lb())

    def init_nlp(self):

        t = self.get_t
        y = self.get_y
        yc = self.get_yc
        u = self.get_u
        z = self.get_z
        zc = self.get_zc
        r = self.get_r
        p = self.get_p

        for i in range(self.N):
   
            #
            # differential equations
            #

            if self.f_n:
                # continuity boundary constraints for differential variables

                y_i_end = self.D[0]*y(i)
                for tau_j in range(1,self.K+1):
                    y_i_end += self.D[tau_j]*yc(i, tau_j)
                self.add_nlp_res( y_i_end - y(i+1), np.zeros(self.var['y']['dim']), np.zeros(self.var['y']['dim']))

                # residual constraints on collocation points for differential variables
    
                for tau_k in range(1, self.K+1):
    
                    y_i_p = self.C[0, tau_k]*y(i)
    
                    for tau_j in range(1, self.K+1):
    
                        y_i_p += self.C[tau_j, tau_k]*yc(i,tau_j)
    
                    f_tau_k = self.ca_f(t(i,tau_k), yc(i, tau_k), u(i), zc(i, tau_k),  r(i), p())
                    self.add_nlp_res(self.hk[i]*f_tau_k - y_i_p, np.zeros(self.f_n), np.zeros(self.f_n))

            #
            # algebraic equations
            #

            if self.g_n:
                # residual constraints on for algebraic variables
                g_tau_k = self.ca_g(t(i), y(i), u(i), z(i),  r(i), p())
                self.add_nlp_res(g_tau_k, np.zeros(self.g_n), np.zeros(self.g_n))

            if self.h_n:
                # residual constraints for in-equality constraints
                h_tau_k = self.ca_h(t(i), y(i), u(i), z(i),  r(i), p())
                self.add_nlp_res(h_tau_k, -np.Inf*np.ones(self.h_n), np.zeros(self.h_n))

            #
            # cost
            #

            # add legrange cost
            for tau_k in range(self.K+1):
                l_tau_k = self.ca_l(t(i,tau_k), yc(i, tau_k), u(i), zc(i, tau_k),  r(i), p())
                self.add_cost(self.B[tau_k]*l_tau_k*self.hk[i])

            # rate on change for controls
            if i and max(self.ocp.u.dw()):
                self.add_cost( ca.sum1(self.ocp.u.dw()*(u(i)-u(i-1))**2) )

        # terminal cost on differential variable

        m_tau_N = self.ca_m(t(self.N), y(self.N), u(self.N-1), z(self.N), r(self.N-1), p())
        self.add_cost( m_tau_N )

        # periodical constraints y(0) = y(N)
        if self.c_n:
            self.add_nlp_res(self.ca_c(y(self.N)) - self.ca_c(y(0)), np.zeros(self.c_n), np.zeros(self.c_n))

        #
        # pipe NLP arguments and construct solver

        self.init_solver()

        # print user statistics on creation
        self.nlp_info()

    def solve_ocp(self,y_0, r_0, t_k):

        # initilize using observer, if active
        self.set_y0( self.observer.sample() if self.use_observer else y_0 )
        
        # enforce reference value
        if isinstance(r_0,np.ndarray) is False:
            Debug.MOSIOP_WARNING('Supplied reference not of type:{}. Will be casted'.format(np.array))
            r_0 = np.array(r_0)

        self.set_reference(r_0)

        # call defined solver
        if self.ipopt_warmstart['enabled'] and ('init' in self.ipopt_warmstart.keys()):
            solution = self.nlp_struct['solver'](x0=self.ipopt_warmstart['init']['x0'],
                                                 lam_x0=self.ipopt_warmstart['init']['lam_x0'],
                                                 lam_g0=self.ipopt_warmstart['init']['lam_g0'],
                                                 lbx=self.nlp_struct['lbz'],
                                                 ubx=self.nlp_struct['ubz'],
                                                 lbg=self.nlp_struct['lbg'],
                                                 ubg=self.nlp_struct['ubg'])
        else:
            solution = self.nlp_struct['solver'](x0=self.nlp_struct['z0'],
                                                 lbx=self.nlp_struct['lbz'],
                                                 ubx=self.nlp_struct['ubz'],
                                                 lbg=self.nlp_struct['lbg'],
                                                 ubg=self.nlp_struct['ubg'])

        nlp_stats = self.nlp_struct['solver'].stats()

        if (nlp_stats['success'] != True) or (nlp_stats['return_status'] != 'Solve_Succeeded'):
            print('Success: {}; Iter. cnt: {}; Return Status: {}'.format(nlp_stats['success'],nlp_stats['iter_count'],nlp_stats['return_status']))

        if self.debug['debug']:

            df = self.parse.process(self.nlp_struct['t'], solution)

            time = df[0]['time']
            x=df[0].iloc[:,self.debug['state']]
            plt.plot(time[0::self.K+1],x[0::self.K+1],  linestyle='-', linewidth=0.5, marker='o', markersize=5, color='green', label='$t_i$')
            plt.plot(time,x,  linestyle='-', linewidth=0.5, marker='x', markersize=5, color='blue', label=r'$\tau _i$' )

            for k in range(self.N):

                tk = np.array(time[k*(self.K+1)])
                zk = np.array(x[k*(self.K+1):(k+1)*(self.K+1)])

                t = tk + self.hk[k]*self.debug['tau_i']
                y = np.zeros(t.shape)

                for i in range(len(y)):
                    for j in range(self.K+1):
                        y[i] += self.debug['D_i'][j,i]*zk[j]

                plt.plot(t,y,  linestyle='-', linewidth=0.3,  markersize=5, color='red', label=r'$z^{K}(t)$' if k==0 else "" )

            plt.legend(loc='upper right',prop={'size': 10},ncol=1,frameon=False)
            plt.title( 'Collocation debugging for {}'.format(self.debug['disc']))
            plt.xlabel('time')
            plt.ylabel('x')
            plt.savefig('../lib/debug/collocation_debug_'+self.debug['disc']+'.png', dpi=600)
            plt.show()

            warnings.warn('Disable collocation debugging to continue')

        # extract data from optimal solution
        parsed = self.parse.process(self.nlp_struct['t'], solution)
    
        # update state estimator
        if self.use_observer:
            self.observer.update({'y_meas':y_0, 'var':parsed['var'], 'p':self.get_parameter()})

        return parsed['ol'], parsed['var']['u0'], parsed['var']['x1']

    def solve_sim(self, y0, u):

        # solve only from one time-step ahead

        if u.ndim == 1:
            return np.array(self.ocp.sim(y0, u)).flatten()

        # solve for multiple time-steps ahead

        y = y0
        for k in range(len(u)):
            print('u=[{}]'.format(u[k]))
            y0 = self.grid, np.append(y0, self.F(x0=y0, p=u[k])['xf'])
            y = np.append(y, y0)

        return y

    #
    # extract OCP related variables
    #

    def extract(self):

        var = {self.ocp.y.name(): {'dim': self.ocp.y.dim(),
                                   'col': self.K,
                                   'N': (self.N + 1) * self.ocp.y.dim(),
                                   'c_N': self.N * self.K * self.ocp.y.dim(),
                                   'off': 0,
                                   'c_off': 1 if self.ocp.y.dim() else 0,
                                   'range': {'a': 0, 'b': self.ocp.y.dim() * (1 + self.K)},
                                   'label': self.ocp.n_y_label}}

        var[self.ocp.u.name()] = {'dim':self.ocp.u.dim(),
                                  'col':0,
                                  'N':self.N*self.ocp.u.dim(),
                                  'c_N':0,
                                  'off':  var['y']['c_off'] + (self.K if self.ocp.y.dim() else 0),
                                  'c_off':var['y']['c_off'] + (self.K if self.ocp.y.dim() else 0) + (1 if self.ocp.u.dim() else 0),
                                  'range':{  'a':var['y']['range']['b'], 'b':var['y']['range']['b'] + self.ocp.u.dim() },
                                  'label':self.ocp.n_u_label }

        var[self.ocp.z.name()] = {'dim':self.ocp.z.dim(),
                                  'col':self.K,
                                  'N':(self.N+1)*self.ocp.z.dim(),
                                  'c_N':self.N*self.K*self.ocp.z.dim(),
                                  'off':  var['u']['c_off'],
                                  'c_off':var['u']['c_off'] + (1 if self.ocp.z.dim() else 0),
                                  'range':{  'a':var['u']['range']['b'], 'b':var['u']['range']['b'] + self.ocp.z.dim()*(1+self.K) },
                                  'label':self.ocp.n_z_label }

        var[self.ocp.r.name()] = {'dim':self.ocp.r.dim(),
                                  'col':0,
                                  'N':self.N*self.ocp.r.dim(),
                                  'c_N':0,
                                  'off':  var['z']['c_off'] + (self.K if self.ocp.z.dim() else 0),
                                  'c_off':var['z']['c_off'] + (self.K if self.ocp.z.dim() else 0) + (1 if self.ocp.r.dim() else 0),
                                  'range':{  'a':var['z']['range']['b'], 'b':var['z']['range']['b'] + self.ocp.r.dim() },
                                  'label':self.ocp.n_r_label }

        var[self.ocp.p.name()] = {'dim':self.ocp.p.dim(),
                                  'col':0,
                                  'N':self.ocp.p.dim(),
                                  'c_N':0,
                                  'off':  self.N*var['r']['c_off'] + (1 if self.ocp.y.dim() else 0) + (1 if self.ocp.z.dim() else 0),
                                  'c_off':self.N*var['r']['c_off'] + (1 if self.ocp.y.dim() else 0) + (1 if self.ocp.z.dim() else 0) + (1 if self.ocp.p.dim() else 0) ,
                                  'range':{ 'a':self.N*var['r']['range']['b'] + self.ocp.y.dim()+ self.ocp.z.dim(), 'b':self.N*var['r']['range']['b'] + self.ocp.y.dim()+ self.ocp.z.dim() + self.ocp.p.dim() },
                                  'label':self.ocp.n_p_label}

        var['k']               = {'off':var['r']['c_off'],'range':self.ocp.y.dim()*(1+self.K)+self.ocp.u.dim()+self.ocp.z.dim()*(1+self.K)+self.ocp.r.dim() }
        var['nlp']             = {'K':self.K,'N':self.N}

        return var

    #
    # retrieve variables from created NLP framework
    #

    def get_t(self, k, j=0):

        if k<0 or k>self.N:
            warnings.warn('chosen stage k={} outside of bounds [0,{}]'.format(k,self.N))

        return self.nlp_struct['t'][k*(1+self.K)+j]

    def get_y(self, k):

        if k<0 or k>self.N:
            warnings.warn('chosen stage k={} outside of bounds [0,{}]'.format(k,self.N))

        if self.var['y']['dim']:
            return self.nlp_struct['z'][k*self.var['k']['off']]
        return self.ocp.y.var()

    def get_yc(self, k, j):

        if k<0 or k>self.N-1:
            warnings.warn('chosen stage k={} outside of bounds [0,{}]'.format(k,self.N-1))

        if j<0 or j>self.K:
            warnings.warn('chosen collocation point j={} for y outside of bounds [0,{}]'.format(j,self.K))

        if self.var['y']['dim']:
            return self.nlp_struct['z'][k*self.var['k']['off'] + self.var['y']['c_off'] +j -1]
        return self.ocp.y.var()

    def get_u(self, k):

        if k<0 or k>self.N-1:
            warnings.warn('chosen stage k={} outside of bounds [0,{}]'.format(k,self.N-1))

        if self.var['u']['dim']:
            return self.nlp_struct['z'][k*self.var['k']['off'] + self.var['u']['off']]
        return self.ocp.u.var()

    def get_z(self, k):

        if k<0 or k>self.N:
            warnings.warn('chosen stage k={} outside of bounds [0,{}]'.format(k,self.N))

        if self.var['z']['dim']:
            if k<self.N:
                return self.nlp_struct['z'][k*self.var['k']['off'] + self.var['z']['off']]
            return self.nlp_struct['z'][k*self.var['k']['off'] + 1]
        return self.ocp.z.var()

    def get_zc(self, k, j):

        if k<0 or k>self.N-1:
            warnings.warn('chosen stage k={} outside of bounds [0,{}]'.format(k,self.N-1))

        if j<0 or j>self.K:
            warnings.warn('chosen collocation point j={} for z outside of bounds [0,{}]'.format(j,self.K))

        if self.var['z']['dim']:
            return self.nlp_struct['z'][k*self.var['k']['off'] + self.var['z']['c_off'] + j -1]
        return self.ocp.z.var()

    def get_r(self, k):

        if k<0 or k>self.N-1:
            warnings.warn('chosen stage k={} outside of bounds [0,{}]'.format(k,self.N-1))

        if self.var['r']['dim']:
            return self.nlp_struct['z'][k*self.var['k']['off'] + self.var['r']['off']]
        return self.ocp.r.var()

    def get_p(self):

        if self.var['p']['dim']:
            return self.nlp_struct['z'][self.var['p']['off']]
        return self.ocp.p.var()

    def set_y0(self, y0):

        # enforce reference value
        if isinstance(y0,np.ndarray) is False:
            Debug.MOSIOP_WARNING('Supplied reference not of type:{}. Will be casted'.format(np.array))
            y0 = np.array(y0)

        try:
     
            assert(np.array(y0).size==self.var['y']['dim'])

            if self.y0['fixed']:

                self.nlp_struct['z0'][0:self.var['y']['dim']] = y0
                self.nlp_struct['lbz'][0:self.var['y']['dim']] = y0
                self.nlp_struct['ubz'][0:self.var['y']['dim']] = y0

            else:

                Debug.MOSIOP_NOTICE('Ignore initial conditions for fixed config')

        except:

            Debug.MOSIOP_WARNING('Cannot evaluate intial conditions {}. Set to default initial conditions {}'.format(y0, self.ocp.y0))

            self.nlp_struct['z0'][0:self.var['y']['dim']] = self.ocp.y0
            self.nlp_struct['lbz'][0:self.var['y']['dim']] = self.ocp.y0
            self.nlp_struct['ubz'][0:self.var['y']['dim']] = self.ocp.y0

            return
            
    def get_y0(self):
        return self.nlp_struct['z0'][0:self.var['y']['dim']]

    def set_reference(self, r):

        if r.shape[0] == 0:
            return

        for k in range(0,self.N):
            self.nlp_struct['z0'][k*self.var['k']['range'] + self.var['r']['range']['a']:k*self.var['k']['range'] + self.var['r']['range']['b']] = r[k]
            self.nlp_struct['lbz'][k*self.var['k']['range'] + self.var['r']['range']['a']:k*self.var['k']['range'] + self.var['r']['range']['b']] = r[k]
            self.nlp_struct['ubz'][k*self.var['k']['range'] + self.var['r']['range']['a']:k*self.var['k']['range'] + self.var['r']['range']['b']] = r[k]

    def set_parameter(self, p):

        assert(p.shape[0]==(self.var['p']['range']['b']-self.var['p']['range']['a']))

        self.nlp_struct['z0'][self.var['p']['range']['a']:self.var['p']['range']['b']] = p
        self.nlp_struct['lbz'][self.var['p']['range']['a']:self.var['p']['range']['b']] = p
        self.nlp_struct['ubz'][self.var['p']['range']['a']:self.var['p']['range']['b']] = p

    def get_parameter(self):
        return self.nlp_struct['z0'][self.var['p']['range']['a']:self.var['p']['range']['b']]

    def get_labels(self):
        return self.parse.labels()

    def nlp_info(self):

        columns = ['Dimension:','Boundary variables:','Collocation points:','Total variables:', 'Variable range:']
        index = ['y', 'u', 'z', 'r', 'p']
        data = []
        for i in index:
            data.append((self.var[i]['dim'], self.var[i]['N'], self.var[i]['c_N'], self.var[i]['N']+self.var[i]['c_N'], '[' + str(self.var[i]['range']['a'])+', ' + str(self.var[i]['range']['b']) + ')'))
        df = pd.DataFrame(data, columns=columns, index=index).transpose()
        df.style.set_caption('NLP variable structure for N={} and K={}'.format(self.N,self.K))
        print( df )

    def var_info(self):

        index = ['y', 'u', 'z', 'r', 'p']
        data = {}
        for i in index:
            data[i] = {'dim': self.var[i]['dim'], 'labels': self.var[i]['label']}
        return data


#
# collocation clasee
#

class Collocation:

    def __init__(self, cfg):
        self.cfg = cfg

    def coef(self, debug=False):

        K = self.cfg['K']
        B = np.zeros(K + 1)
        C = np.zeros((K + 1, K + 1))
        D = np.zeros(K + 1)

        tau_root = np.append(0,ca.collocation_points(K, self.cfg['method']))

        # For debugging, plot a over sampled polynomial approximation

        if debug:

            N=100
            tau_i = np.linspace(0,1,N)
            D_i = np.zeros((K + 1,N))

        for j in range(K+1):

            # construct polynomial for j-th collocation point
            lj = np.poly1d([1])
            for k in range(K+1):
                if k != j:
                    lj *= np.poly1d( [1, -tau_root[k]] ) / ( tau_root[j] -tau_root[k] )

            # coefficients continuity equations
            D[j] = lj(1.0)

            if debug:
                for k in range(N):
                    D_i[j,k]= lj(tau_i[k])  # see 10.4 in Bieglers book to subsample

            # coefficients for collocation equations

            dlj = np.polyder(lj)
            for k in range(K+1):
                C[j, k] = dlj(tau_root[k])

            # coefficients for
            ilj = np.polyint(lj)
            B[j] = ilj(1.0)

        return B, C, D, tau_root, {'debug':debug, 'N':N,'tau_i':tau_i,'D_i':D_i,'state':2, 'disc':self.cfg['method']+' K='+str(K)} if debug else {'debug':debug}
#
# parse the ipopt solution data into sensible blocks of {y,z,u,r}
#

class Parse:

    def __init__(self, var):
        self.var = var
        self.label = {'df':np.hstack(('time', var['y']['label'], var['u']['label'], var['z']['label'], var['r']['label'])),'t':'time', 'y':var['y']['label'],'u':var['u']['label'], 'z':var['z']['label'],  'r':var['r']['label']}

    def process(self, time, solution):

        t = time                          # time vector for open loop simulation
        f = solution['f'].toarray()       # objective function

        g = solution['g'].toarray()       # general non-linear constraints
        lam_g = solution['lam_g'].toarray()

        x = solution['x'].toarray()       # optimization variables
        lam_x = solution['lam_x'].toarray()


        xk = x[0:self.var['k']['range']*self.var['nlp']['N']].reshape(self.var['nlp']['N'],self.var['k']['range'])
        xN = x[self.var['k']['range']*self.var['nlp']['N']:-self.var['p']['dim']]

        df = pd.DataFrame(columns=self.label['df'])

        for k in range(self.var['nlp']['N']):
            yk = xk[k][self.var['y']['range']['a']:self.var['y']['range']['b']].reshape(1+self.var['nlp']['K'],self.var['y']['dim'])
            uk = xk[k][self.var['u']['range']['a']:self.var['u']['range']['b']].reshape(1,self.var['u']['dim'])
            zk = xk[k][self.var['z']['range']['a']:self.var['z']['range']['b']].reshape(1+self.var['nlp']['K'],self.var['z']['dim'])
            rk = xk[k][self.var['r']['range']['a']:self.var['r']['range']['b']].reshape(1,self.var['r']['dim'])

            for j in range(1+self.var['nlp']['K']):
                df.loc[k*(1+self.var['nlp']['K'])+j] = np.hstack((t[k*(1+self.var['nlp']['K'])+j], yk[j], uk.flatten(), zk[j],  rk.flatten()))

        # append terminal points (repeat for {u,r})

        yk = xN[0:self.var['y']['dim']]
        zk = xN[self.var['y']['dim']:,]

        df.loc[self.var['nlp']['N']*(1+self.var['nlp']['K'])] = np.hstack((t[self.var['nlp']['N']*(1+self.var['nlp']['K'])], yk.flatten(), uk.flatten(), zk.flatten(),  rk.flatten()))

        ol  = df
        var = {'x0':df.iloc[0,1:1+self.var['y']['dim']],
               'u0':df.iloc[0,1+self.var['y']['dim']:1+self.var['y']['dim']+self.var['u']['dim']],
               'z0':df.iloc[0,1+self.var['y']['dim']+self.var['u']['dim']:1+self.var['y']['dim']+self.var['u']['dim']+self.var['z']['dim']],
               'r0':df.iloc[0,1+self.var['y']['dim']+self.var['u']['dim']+self.var['z']['dim']:1+self.var['y']['dim']+self.var['u']['dim']+self.var['z']['dim']+self.var['r']['dim']],
               'x1':df.iloc[1+self.var['nlp']['K'],1:1+self.var['y']['dim']]}
        warmstart = {'x0':x, 'lam_x0':lam_x, 'lam_g0':lam_g}
        
        ret = {'ol':ol, 'var':var, 'warmstart':warmstart } 
                       
        return ret

    def labels(self):
        return self.label
