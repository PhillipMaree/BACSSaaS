from opt.mpc.ocp import OCP
import casadi as ca

class Cstr(OCP):

    def __init__(self, ocp_cfg=None):
        OCP.__init__(self, ocp_cfg)

    def init(self):

        self.y.add('C2H2',1e-3, 1.0)     # concentration ofacetylene
        self.y.add('H',1e-3, 1.0)        # concentration hydrogen
        self.y.add('C2H4',1e-3, 1.0)     # concentration of ethylene

        self.u.add('Hc', 1e-3,5,1e-3,0)         # hydrogen concentration feed
        self.u.add('Hc2', 1e-3,5,1e-3,100)         # hydrogen concentration feed

        self.p.add('sigma1',1000)       # cost on battery usage [NOK/kWh] See [berg2021economic]
        self.p.add('sigma2',472)        # battery charge coefficient
        self.p.add('beta',23)          # battery dis-charge coefficient

    def l_fn(self):

        C2H4 = self.y.get('C2H4')

        return -C2H4

    def f_fn(self):

        C2H2 = self.y.get('C2H2')
        H = self.y.get('H')
        C2H4 = self.y.get('C2H4')

        sigma1 = self.p.get('sigma1')
        sigma2 = self.p.get('sigma2')
        beta = self.p.get('beta')

        Hc = self.u.get('Hc')
        Hc2 = self.u.get('Hc2')

        a = sigma1*C2H2*H/(1+beta*C2H2)
        b = sigma2*H**0.5*C2H4/(1+beta*C2H2)

        return ca.vertcat(1-C2H2-a,
                          Hc2+Hc-H-a-b,
                          -C2H4+a-b)
