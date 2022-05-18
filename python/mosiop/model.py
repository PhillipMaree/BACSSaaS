import numpy as np

from opt.mpc.ocp import OCP
import casadi as ca

#
# Author: JP Maree
# See https://www.overleaf.com/project/5ffef15ed7828da255f3797d
#


class TestCase1(OCP):

    def __init__(self, ocp_cfg=None):
        OCP.__init__(self, ocp_cfg, '1')

    def init(self):

        # differential states:
        self.y.add('Ti',293.15, 296.15)                 # interior temperature [K]

        # controls
        self.u.add('phi_h', -1e5, 1e5)            # heat input to zone [W]

        # parameters
        self.p.add('R_ie',1e-2)                   # resistance [K/W]
        self.p.add('C_i', 1e6)                    # heat cap [J/K]
        self.p.add('Ti_ref',294.15)               # Temperature reference setpoint [K]
        self.p.add('alpha_phi_h',0)               # Penalty weight on heat applied
        self.p.add('alpha_T_i',1)                 # Penalty weight temperature tracking

        # references
        self.r.add('Tout', 250, 310)              # outdoor temp [K]

    def l_fn(self):

        Ti = self.y.get('Ti')
        phi_h = self.u.get('phi_h')
        Ti_ref = self.p.get('Ti_ref')
        alpha_phi_h = self.p.get('alpha_phi_h')
        alpha_T_i = self.p.get('alpha_T_i')

        return alpha_phi_h*phi_h**2 + alpha_T_i*(Ti-Ti_ref)**2

    def f_fn(self):

        Ti = self.y.get('Ti')
        phi_h = self.u.get('phi_h')
        R_ie = self.p.get('R_ie')
        C_i = self.p.get('C_i')
        Tout = self.r.get('Tout')

        return (Tout-Ti)/(R_ie*C_i) + phi_h/C_i

    def r_fn(self,k):

        # Create some periodic biased cosine external Tout reference
        # k       current index of simulation with k=0,1,....
        # Ts      sampling time
        # Toffset temperature offset in range [-1,1]
        # Tscale  symmetric temperature scale
        Tout = lambda k,Ts, Toffset, Tscale: Tscale*(Toffset-np.cos(2*np.pi/3600*Ts*k))
        return [ Tout(k,self.Ts,1,5) +273.15 for k in range(k, k + self.N) ] # in Kelvin


class TestCase2(OCP):

    def __init__(self, ocp_cfg=None):
        OCP.__init__(self, ocp_cfg, '2')

    def init(self):

        # differential states:
        self.y.add('Ti',250, 310)                 # interior temperature [K]

        # controls
        self.u.add('phi_h', -1e5, 1e5)            # heat input to zone [W]

        # parameters
        self.p.add('R_ie',1e-2)                   # resistance [K/W]
        self.p.add('C_i', 1e6)                    # heat cap [J/K]
        self.p.add('Ti_ref',294.15)               # Temperature reference setpoint [K]
        self.p.add('alpha_phi_h',0)               # Penalty weight on heat applied
        self.p.add('alpha_T_i',1)                 # Penalty weight temperature tracking

        # references
        self.r.add('Tout', 250, 310)              # outdoor temp [K]

    def l_fn(self):

        Ti = self.y.get('Ti')
        phi_h = self.u.get('phi_h')
        Ti_ref = self.p.get('Ti_ref')
        alpha_phi_h = self.p.get('alpha_phi_h')
        alpha_T_i = self.p.get('alpha_T_i')

        return alpha_phi_h*phi_h**2 + alpha_T_i*(Ti-Ti_ref)**2

    def f_fn(self):

        Ti = self.y.get('Ti')
        phi_h = self.u.get('phi_h')
        R_ie = self.p.get('R_ie')
        C_i = self.p.get('C_i')
        Tout = self.r.get('Tout')

        return (Tout-Ti)/(R_ie*C_i) + phi_h/C_i

    def r_fn(self,k):

        # Create some periodic biased cosine external Tout reference
        # k       current index of simulation with k=0,1,....
        # Ts      sampling time
        # Toffset temperature offset in range [-1,1]
        # Tscale  symmetric temperature scale
        Tout = lambda k,Ts, Toffset, Tscale: Tscale*(Toffset-np.cos(2*np.pi/3600*Ts*k))
        return [ Tout(k,self.Ts,1,5) +273.15 for k in range(k, k + self.N) ] # in Kelvin

class TestCase3(OCP):

    def __init__(self, ocp_cfg=None):
        OCP.__init__(self, ocp_cfg, '3')

    def init(self):
        
        # differential states:
        self.y.add('TZonNor',20+273.15, 23+273.15)     # zone temp
        self.y.add('TZonSou',20+273.15, 23+273.15)     # zone temp

        # inputs / pådrag
        self.r.add('Tout', 230, 330) # -np.inf, np.inf)         # outdoor temp

        self.u.add('preHeaNor', -10000, 10000) # -np.inf, np.inf)         # heat input to zone [W]
        self.u.add('preHeaSou', -10000, 10000) # -np.inf, np.inf)         # heat input to zone [W]


        # parameters
        self.p.add('resNor', 0.01)       # resistance [K/W]
        self.p.add('resSou', 0.01)       # resistance [K/W]
        self.p.add('capNor', 1E6)        # heat cap [J/K]
        self.p.add('capSou', 1E6)        # heat cap [J/K]
        
        self.p.add('TZonNor_ref',294.15)               # Temperature reference setpoint [K]
        self.p.add('TZonSou_ref',294.15)               # Temperature reference setpoint [K]
        
        self.p.add('alpha_phi_h',1)               # Penalty weight on heat applied
        self.p.add('alpha_T_i',0)                 # Penalty weight temperature tracking


    def l_fn(self):
        ''' Stage cost. '''
        preHeaNor = self.u.get('preHeaNor')
        preHeaSou = self.u.get('preHeaSou')

        TZonNor = self.y.get('TZonNor')
        TZonSou = self.y.get('TZonSou')

        TZonNor_ref = self.p.get('TZonNor_ref')
        TZonSou_ref = self.p.get('TZonSou_ref')

        alpha_phi_h = self.p.get('alpha_phi_h')
        alpha_T_i = self.p.get('alpha_T_i')
        
        return alpha_phi_h*(preHeaNor**2 + preHeaSou**2) + \
               alpha_T_i*((TZonNor-TZonNor_ref)**2 + (TZonSou-TZonSou_ref)**2)

    def f_fn(self):
        ''' Differential functions. '''
        TZonNor = self.y.get('TZonNor')
        TZonSou = self.y.get('TZonSou')

        resNor = self.p.get('resNor')
        resSou = self.p.get('resSou')
        capNor = self.p.get('capNor')
        capSou = self.p.get('capSou')

        Tout = self.r.get('Tout')

        preHeaNor = self.u.get('preHeaNor')
        preHeaSou = self.u.get('preHeaSou')
        
        return ca.vertcat((Tout - TZonNor)/(resNor*capNor) + \
                         (1/capNor)*preHeaNor, \
                         (Tout - TZonSou)/(resSou*capSou) + \
                         (1/capSou)*preHeaSou)


    def r_fn(self,k):
        # Create some periodic biased cosine external Tout reference
        # k       current index of simulation with k=0,1,....
        # Ts      sampling time
        # Toffset temperature offset in range [-1,1]
        # Tscale  symmetric temperature scale
        Tout = lambda k,Ts, Toffset, Tscale: Tscale*(Toffset-np.cos(2*np.pi/3600*Ts*k))
        return [ Tout(k,self.Ts,1,5) +273.15 for k in range(k, k + self.N) ] # in Kelvin



class TestCase4(OCP):

    def __init__(self, ocp_cfg=None):
        OCP.__init__(self, ocp_cfg, '4')

    def init(self):
        
        # differential states:
        self.y.add('TZonNor',20+273.15, 23+273.15)     # zone temp
        self.y.add('TZonSou',20+273.15, 23+273.15)     # zone temp

        # algebraic states, measurements.
        self.z.add('TZonNor_meas', 273.15+18, 25+273.15)
        self.z.add('TZonSou_meas', 273.15+18, 25+273.15)     # zone temp

        # measurement noise
        self.p.add('v1', 0, 0)
        self.p.add('v2', 0, 0)     # zone temp

        # inputs / pådrag
        self.r.add('Tout', 230, 330) # -np.inf, np.inf)         # outdoor temp

        self.u.add('preHeaNor', -10000, 10000) # -np.inf, np.inf)         # heat input to zone [W]
        self.u.add('preHeaSou', -10000, 10000) # -np.inf, np.inf)         # heat input to zone [W]


        # parameters
        self.p.add('resNor', 0.01)       # resistance [K/W]
        self.p.add('resSou', 0.01)       # resistance [K/W]
        self.p.add('capNor', 1E6)        # heat cap [J/K]
        self.p.add('capSou', 1E6)        # heat cap [J/K]
        
        self.p.add('TZonNor_ref',294.15)               # Temperature reference setpoint [K]
        self.p.add('TZonSou_ref',294.15)               # Temperature reference setpoint [K]
        
        self.p.add('alpha_phi_h',1)               # Penalty weight on heat applied
        self.p.add('alpha_T_i',0)                 # Penalty weight temperature tracking


    def l_fn(self):
        ''' Stage cost. '''
        preHeaNor = self.u.get('preHeaNor')
        preHeaSou = self.u.get('preHeaSou')

        TZonNor = self.y.get('TZonNor')
        TZonSou = self.y.get('TZonSou')

        TZonNor_ref = self.p.get('TZonNor_ref')
        TZonSou_ref = self.p.get('TZonSou_ref')

        alpha_phi_h = self.p.get('alpha_phi_h')
        alpha_T_i = self.p.get('alpha_T_i')
        
        return alpha_phi_h*(preHeaNor**2 + preHeaSou**2) + \
               alpha_T_i*((TZonNor-TZonNor_ref)**2 + (TZonSou-TZonSou_ref)**2)

    def f_fn(self):
        ''' Differential functions. '''
        TZonNor = self.y.get('TZonNor')
        TZonSou = self.y.get('TZonSou')

        resNor = self.p.get('resNor')
        resSou = self.p.get('resSou')
        capNor = self.p.get('capNor')
        capSou = self.p.get('capSou')

        Tout = self.r.get('Tout')

        preHeaNor = self.u.get('preHeaNor')
        preHeaSou = self.u.get('preHeaSou')
        
        return ca.vertcat((Tout - TZonNor)/(resNor*capNor) + \
                         (1/capNor)*preHeaNor, \
                         (Tout - TZonSou)/(resSou*capSou) + \
                         (1/capSou)*preHeaSou)


    def g_fn(self):
        ''' Algebraic functions. '''
        TZonNor = self.y.get('TZonNor')
        TZonSou = self.y.get('TZonSou')

        # measurements:
        TZonNor_meas = self.z.get('TZonNor_meas')
        TZonSou_meas = self.z.get('TZonSou_meas')

        # noise vars:
        v1 = self.p.get('v1')
        v2 = self.p.get('v2')

        return ca.vertcat(TZonNor_meas - TZonNor - v1, \
                          TZonSou_meas - TZonSou - v2)


    def h_fn(self):
        ''' Measurement functions (for filtering) '''
        TZonNor = self.y.get('TZonNor')
        TZonSou = self.y.get('TZonSou')

        # noise vars:
        v1 = self.p.get('v1')
        v2 = self.p.get('v2')

        return ca.vertcat(TZonNor + v1, \
                          TZonSou + v2)

    def r_fn(self,k):
        # Create some periodic biased cosine external Tout reference
        # k       current index of simulation with k=0,1,....
        # Ts      sampling time
        # Toffset temperature offset in range [-1,1]
        # Tscale  symmetric temperature scale
        Tout = lambda k,Ts, Toffset, Tscale: Tscale*(Toffset-np.cos(2*np.pi/3600*Ts*k))
        return [ Tout(k,self.Ts,1,5) +273.15 for k in range(k, k + self.N) ] # in Kelvin


class TestCase5(OCP):

    def __init__(self, ocp_cfg=None):
        OCP.__init__(self, ocp_cfg, '5')

    def init(self):
        
        # differential states:
        self.y.add('Ti',200, 350)        # interior temperature
        self.y.add('Te',200, 350)        # envelope temperature
        self.y.add('Th',200, 350)        # heater temperature
        
        # control inputs
        self.u.add('phi_h', 0, 5000,0,0)   # heat input to zone [W]

        # external references
        self.r.add('Ta', 230, 330)       # ambients outdoor temp
        self.r.add('phi_s', 0, 100)    # horizontal  solar global irraidance

        # parameters
        self.p.add('Rie', 4.81e-5)       # Thermal resistance, interior and envelope [K/W]
        self.p.add('Rea', 1.63e-3)       # Thermal resistance, envelope and ambient [K/W]
        self.p.add('Rih', 1.33e-4)       # Thermal resistance, interior and heaterp [K/W]
        self.p.add('Ria', 0.1e-1)        # Thermal resistance, interior and ambient [K/W]
        self.p.add('Ci', 2.82e7)         # Thermal capacitance of interior [J/W]
        self.p.add('Ch', 9.40e6)         # Thermal capacitance of heater [J/W]
        self.p.add('Ce', 6.87e8)         # Thermal capacitance of envelope (inf.) [J/W]
        self.p.add('Ai', 50)             # Equivalent window area of interior [m2]
        self.p.add('Ae', 50)             # Equivalent window area of envelope [m2]
        
        # tracking set-points
        self.p.add('Ti_ref',295)      # Temperature reference setpoint [K]
        
        # objective penalty weights
        self.p.add('alpha_phi_h',1)      # Penalty weight on heat applied
        self.p.add('alpha_Ti',1)         # Penalty weight temperature tracking

    def l_fn(self):

        Ti = self.y.get('Ti')
        Ti_ref = self.p.get('Ti_ref')
        
        phi_h = self.u.get('phi_h')
        phi_max = self.u.max

        alpha_phi_h = self.p.get('alpha_phi_h')
        alpha_Ti = self.p.get('alpha_Ti')

        # normalized
        return alpha_phi_h*(phi_h/phi_max)**2 + alpha_Ti*((Ti-Ti_ref)/Ti_ref)**2
        
    def f_fn(self):

        Ti = self.y.get('Ti')
        Te = self.y.get('Te')
        Th = self.y.get('Th')

        phi_h = self.u.get('phi_h')

        Ta = self.r.get('Ta')
        phi_s = self.r.get('phi_s')

        Rie = self.p.get('Rie')
        Rea = self.p.get('Rea')
        Rih = self.p.get('Rih')
        Ria = self.p.get('Ria')
        Ci = self.p.get('Ci')
        Ch = self.p.get('Ch')
        Ce = self.p.get('Ce')
        Ai = self.p.get('Ai')
        Ae = self.p.get('Ae')

        dTidt = (Te - Ti)/(Rie*Ci) + (Th - Ti)/(Rih*Ci) + (Ta - Ti)/(Ria*Ci) + Ai*phi_s/Ci
        dTedt = (Ti - Te)/(Rie*Ce) + (Ta - Te)/(Rea*Ce) + Ae*phi_s/Ce
        dThdt = (Ti - Th)/(Rih*Ch) + phi_h/Ch

        return ca.vertcat(dTidt, dTedt, dThdt)