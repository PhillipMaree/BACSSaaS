from api.database_api import Database

from flask import Flask, render_template

from plotly.subplots import make_subplots
import plotly.graph_objs as go
import plotly

from threading import Thread
import json, requests

class Dashboard():

    global app
    app = Flask(__name__)

    def __init__(self, cfg):
        global emu, db
        
        emu = json.loads(str(requests.get(cfg['boptest']['endpoint']).content, encoding='utf-8'))['name']
        db = Database(cfg['database'])

    @app.route('/show',defaults={'N': 100})
    @app.route('/show/<N>')
    def show(N): 
        global emu, db

        df = db.read('internal',emu,N=int(N))

        fig = make_subplots(rows=6, cols=1, shared_xaxes=True,vertical_spacing=0.1,subplot_titles=('Interior Temperature', 
        'Building Envelope Temperature', 'Heater Temperature', 'Heater Energy Flux','Ambient Temperature','Solar Radiation'))
    
        # populate sub figures
        fig.append_trace(go.Scatter(y=df['ti_ext'] - 273.15,name=r'Ti (ext)',line = dict(width=1,dash='dot')), row=1, col=1)
        fig.append_trace(go.Scatter(y=df['ti_0'] - 273.15,name='Ti (mpc)'), row=1, col=1)
        fig.append_trace(go.Scatter(y=df['ti_ref'] - 273.15,name='Ti (ref)',line = dict(width=1,dash='dash')), row=1, col=1)
        fig.append_trace(go.Scatter(y=df['te_ext'] - 273.15,name='Te (ext)',line = dict(width=1,dash='dot')), row=2, col=1)
        fig.append_trace(go.Scatter(y=df['te_0'] - 273.15,name='Te (mpc)'), row=2, col=1)
        fig.append_trace(go.Scatter(y=df['th_ext'] - 273.15,name='Th (ext)',line = dict(width=1,dash='dot')), row=3, col=1)
        fig.append_trace(go.Scatter(y=df['th_0'] - 273.15,name='Th (mpc)'), row=3, col=1)
        fig.append_trace(go.Scatter(y=df['phi_h_0']/1000,name='phih (mpc)'), row=4, col=1)
        fig.append_trace(go.Scatter(y=df['ta_0'] - 273.15,name='Ta (ref)'), row=5, col=1)
        fig.append_trace(go.Scatter(y=df['phi_s_0'],name='phis (ref)'), row=6, col=1)

        # Update yaxis properties
        fig.update_yaxes(title_text="[C]", showgrid=True, row=1, col=1)
        fig.update_yaxes(title_text="[C]", showgrid=True, row=2, col=1)
        fig.update_yaxes(title_text="[C]", showgrid=True, row=3, col=1)
        fig.update_yaxes(title_text="[kW]", showgrid=True, row=4, col=1)
        fig.update_yaxes(title_text="[C]", showgrid=True, row=5, col=1)
        fig.update_yaxes(title_text="[W/m2]", showgrid=True, row=6, col=1)
        fig.update_xaxes(title_text="index", showgrid=True, row=6, col=1)

        fig.update_layout(title_text="BACSSaaS for emulator case <{}>".format(emu), height=1000)

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('index.html', plot=graphJSON)

    def run(self):
        Thread(target = app.run,kwargs={'host':'0.0.0.0', 'port':5000}).start()
   
if __name__ == '__main__':
    Dashboard().run()