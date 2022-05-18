"""
Created on Sun Nov 14 22:01:17 2021

@author: mariusb
"""
import requests
from opt.mpc.mpc import ConfigJson
from opt.mpc.mpc import MPC
from opt.mpc.ocp import OCP
import numpy as np
import pandas as pd
import pdb
import matplotlib.pyplot as plt

class Forecaster(object):
    ''' 
    BOPTEST Forecaster object. A forecast is retrieved from BOPTEST,
    it should be set as reference in the MOSIOP MPC object.
    Only one operation is necessary in this case:
        - cast from dict to np.array, keeping 
          the order as defined in OCP-formulation.
          
    '''
    def __init__(self, cfg):

        self.ocp_names =  cfg['mosiop_map']['r']['labels'] #self.get_names_from_MX(ocp.r.mx) # in order # TODO This is bad coding pracice as it is hardcoded for 'r' only. Should be generalized
        self.forecast_map = cfg['boptest_map'] # TODO Boptest map only refer to reference. Should be more generic to cater for other signals

    def to_np_array(self, forecast):
        ''' 
        Add the forecast to the MPC problem of interest. 
        There should be no dependance on the ordering of references,
        only (possibly) on a mapping between BOPTEST names and MOSIOP names.
        '''
        # cut out current timestep?
        sorted_forecast = {k: forecast[self.forecast_map[k]][1:] for k in self.ocp_names}
        return np.array(list(sorted_forecast.values())).transpose()

    @staticmethod
    def get_names_from_MX(mx):
        ''' Get names in order from concatenated MX objects. '''
        return str(mx).lstrip("MX(vertcat(").rstrip("))").replace(" ", "").split(",")  

        
# BOPTEST subclass of RESTApi

class RestApi(object):
    ''' Abstract class. '''
    def __init__(self):
        self.url = 'http://bacssaas_boptest:5000'
        self.name = self.get_name()['name']

    def initialize(self):
        return requests.put('{0}/initialize'.format(self.url), data={'start_time':0, 'warmup_period':0})
        
    def get_name(self) -> dict:
        return requests.get('{0}/name'.format(self.url)).json()
    
    def get_forecast(self) -> dict:
        return requests.get('{0}/forecast'.format(self.url)).json()
    
    def set_forecast_params(self, u={}):
        return requests.put('{0}/forecast_parameters'.format(self.url), data=u)
    
    def get_measurement_info(self):
        return requests.get('{0}/measurements'.format(self.url)).json()
    
    def get_input_info(self):
        return requests.get('{0}/inputs'.format(self.url)).json()
         
    def set_step(self, step):
        return requests.put('{0}/step'.format(self.url), data={'step':step})
        
    def get_step(self, step):
        return requests.get('{0}/step'.format(self.url)).json()
    
    def get_kpis(self) -> dict:
        return requests.get('{0}/kpi'.format(self.url)).json()
   
    def advance(self, u={}) -> dict:
        return requests.post('{0}/advance'.format(self.url), data=u).json()
    

class Boptest(RestApi):
    ''' Wrapper for Restful-API to BOPTEST. '''
    def __init__(self, cfg):
        RestApi.__init__(self)
        
        self.cfg = cfg['boptest']
        self.var = cfg['mosiop']['var_info']

        h = cfg['mosiop']['MPC']['temporal']['h']
        N = cfg['mosiop']['MPC']['temporal']['N']

        self.set_step(h)
        self.set_forecast_params({"horizon": h*N, "interval": h})

        
        ''' 
        Takes config-file + desc. of ocp. 
        
        Description of maps from BOPTEST to Modelica-model.
        OCP-description should conform with Modelica naming:
            - <name_of_mapping> = {<Modelica/OCP_name>:<BOPTEST_name>, ...}    
            
        Example for controls:
            - control_map = {"preHea": "oveAct"}
            
        which means that the overwrite-block the Modelica-model is named 
        "oveAct", while the actual variable that is overwritten by this 
        block is named "preHea".
        '''

        for k, v in self.cfg.items():
            setattr(self, k, v) # maps accessed by self.maps[<name_of_map>]
        self.initialize()

        cfg = {'boptest_map':self.maps["r"], 'mosiop_map':self.var} # TODO to make this more generic boptest_map should have similar variables maps for y,u,z,r,p (latter empty if not applicable)
        self.forecaster = Forecaster(cfg)

    def evolve(self, u={}):
        ''' 
        Advances simulation one step forward.
        Then forecast is retrieved.
        '''
        y = self.advance(u=self.get_control(u))

        ### get in correct order:
        # what are we measuring? 
        # differential or algebraic variables?
        #pdb.set_trace()

        # "outside" of ocp, "y" refers to measurement
        # this corresponds to "z" in the ocp
        
        try:
            y_sorted = self.to_np_array(y, self.cfg["maps"]["z"], self.var["z"]["labels"])
        except KeyError:
            y_sorted = self.to_np_array(y, self.cfg["maps"]["y"], self.var["y"]["labels"])

        return self.forcast(), y_sorted

    def forcast(self):
        return self.to_np_array(self.get_forecast(), self.cfg["maps"]["r"], self.var["r"]["labels"])
    
    @staticmethod
    def to_np_array(y, mapping, var_labels):
        ''' 
        For retrieving, sorting algrebraic, differential variables (e.g. "y", "z")
        y: dict
            - results from advancing emulator one step.
        mapping: dict 
            - known mapping between emulator result and OCP-names 
              (should be one-to-one with Modelica names..)
        labels: list
            - ordering of variables in OCP.
        '''
        # y or z?
        
        vars_sorted = { k: y[mapping[k]] for k in var_labels if k in mapping.keys()}

        return np.array(list(vars_sorted.values())).transpose()

    def get_control(self, u_0) -> dict:
        '''
        Parse the control law from mpc for boptest-usage.
        '''
        u_map = self.maps["u"]
        
        u_values = {v + "_u": u_0.loc[k] \
                    for k, v in u_map.items()}           
        u_active = {v + "_activate": \
                    1 if u_values[v + "_u"] else 0 \
                    for k, v in u_map.items()}     
            
        return {**u_values, **u_active}
    
    def construct_y0(self, y): 
        ''' 
        For this, a mapping between state and measurements.
        Assume we have the order of the differential states.
        
        This assumes we have measurements for all states,
        hence it needs to be generalized at some point
        for working with filters etc.
        '''
        return [y[meas] for state, meas in self.maps["state_map"].items()]
       
    def get_results(self, tf, ts=0):
        ''' Get results. '''
        measurements, inputs = self.get_measurement_info(), self.get_input_info()
        points = list(measurements.keys()) + list(inputs.keys())
        df_res = pd.DataFrame()
        
        for point in points:
            res = requests.put('{0}/results'.format(self.url), data={'point_name':point,'start_time':ts, 'final_time':tf}).json()
            df_res = pd.concat((df_res,pd.DataFrame(data=res[point], index=res['time'],columns=[point])), axis=1)
     
        # pdb.set_trace()     
        df_res.index.name = 'time'
        # df_res.index = df_res.index.values/3600 # convert s --> hr
        
        return df_res

    def plot_results(self, tf, ts=0, cols_to_plot=None):
        ''' Plot results of boptest-interaction. '''
        res = self.get_results(tf, ts=ts)
        if cols_to_plot is None:
            cols_to_plot = list(filter(lambda x: x != "time" \
                                       and not x.endswith("activate"), \
                                res.columns))
        if len(cols_to_plot) > 5:
            nrows, ncols = int(len(cols_to_plot)/2), 2
        else:
            nrows, ncols = len(cols_to_plot), 1

        fig, axes = plt.subplots(nrows, ncols)
        
        for col, ax in zip(cols_to_plot, axes.flatten()):
            latex_col = self.latexize(col)
            ax.plot(res.index, res[col], label=latex_col)
            ax.legend(loc='upper right', prop={'size': 10}, ncol=1)

        return fig, axes

    @staticmethod
    def latexize(name):
        name, typ = name.split("_") # naming convention
        typ = "{" + typ + "}"
        return f"${name}_{typ}$"