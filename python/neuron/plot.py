from api.database_api import Database
from entrypoint import Config
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
#plt.rcParams['text.usetex'] = True

 # initilize database
db = Database(Config('neuron.ini').parse()['database'])
# extract ALL data for results plotting:
df = db.read("internal", "testcase5", N=2000)

#df = df.iloc[::-1]
# reverse index:
#new_ndx = pd.date_range(start="2020-01-01 00:00", periods=2000, freq = "900s")
#f.index = new_ndx
N = 1000
df.index = range(2*N)

heater_temps_train = df[[col for col in df.columns if col.startswith("th") and col != "time" and "1" not in col]].loc[0:N]
env_temps_train = df[[col for col in df.columns if col.startswith("te") and col != "time" and "1" not in col]].loc[0:N]
int_temps_train = df[[col for col in df.columns if col.startswith("ti") and col != "time" and "1" not in col]].loc[0:N]


heater_temps_pinn = df[[col for col in df.columns if col.startswith("th") and col != "time" and "0" not in col]].iloc[N:2*N]
env_temps_pinn = df[[col for col in df.columns if col.startswith("te") and col != "time" and "0" not in col]].iloc[N:2*N]
int_temps_pinn = df[[col for col in df.columns if col.startswith("ti") and col != "time" and "0" not in col]].iloc[N:2*N]

heater_temps_pinn.index = range(N)
env_temps_pinn.index = range(N)
int_temps_pinn.index = range(N)

#heater_temps_pinn = df[[col for col in df.columns if col.startswith("th") and col != "time" and "0" not in col]].iloc[N:2*N]
#env_temps_pinn = df[[col for col in df.columns if col.startswith("te") and col != "time" and "0" not in col]].iloc[N:2*N]
#int_temps_pinn = df[[col for col in df.columns if col.startswith("ti") and col != "time" and "0" not in col]].iloc[N:2*N]


#heater_temps_pinn = df[[col for col in df.columns if col.startswith("th") and col != "time" and "0" not in col]].iloc[N:2*N]
#env_temps_pinn = df[[col for col in df.columns if col.startswith("te") and col != "time" and "0" not in col]].iloc[N:2*N]
#int_temps_pinn = df[[col for col in df.columns if col.startswith("ti") and col != "time" and "0" not in col]].iloc[N:2*N]

fig, ax = plt.subplots(3,1, figsize=(6,6))

#int_temps.plot(ax=ax[0])
#heater_temps.plot(ax=ax[1])
#env_temps.plot(ax=ax[2])

# NOTE: 0 - Kalman, 1 - PINN

name_map = {"ti_0": "$T_{i}^{Kalman}$",
            "ti_1": "$T_{i}^{PINN}$",
            "ti_ref": "$T_{i}^{ref}$",
            "ti_ext": "$T_{i}^{true}$",
            "te_0": "$T_{e}^{Kalman}$",
            "te_1": "$T_{e}^{PINN}$",
            "te_ext": "$T_{e}^{true}$",
            "te_ref": "$T_{e}^{ref}$", \
            "th_0": "$T_{h}^{Kalman}$",
            "th_1": "$T_{h}^{PINN}$",
            "th_ext": "$T_{h}^{true}$",
            "th_ref": "$T_{h}^{ref}$"}

#int_temps_train.rename(columns=name_map, inplace=True)
#env_temps_train.rename(columns=name_map, inplace=True)
#heater_temps_train.rename(columns=name_map, inplace=True)

# try to extract strings from series

#datetime = int_temps_train.index.strftime('%B-%d')


# plot first 500 time steps (training data generation)

#(int_temps_train-273.15).plot(ax=ax[0])
#(env_temps_train-273.15).plot(ax=ax[1])
#(heater_temps_train-273.15).plot(ax=ax[2])

#dfs = [int_temps_train, env_temps_train, heater_temps_train]
dfs = [int_temps_pinn, env_temps_pinn, heater_temps_pinn]


#colors = pd.DataFrame({'color1': [15], 'color2': [27], 'color3': [89], 'color4': [123],
#                       'color5': [220], 'color6': [100], 'color7': [123], 'color8': [247], 'color9': [255]})

colors = pd.DataFrame({'color1': [50], 'color7': [125], 'color9': [200]})

#fig, axes = plt.subplots(3, 3, figsize=(10, 10), sharey='row', sharex='col')
#fig.subplots_adjust(hspace=0, wspace=0)

#for ax, c in zip(axes.flat, colors.T[0].values):
#    ax.set_facecolor(str(c/255.))


# savefig
#plt.savefig("train.png")
for axis, sub in zip(ax, dfs):
    sub.rename(columns=name_map, inplace=True)
    # invert order:
    sub = sub[reversed(sub.columns)]
    for i, (color, col) in enumerate(zip(colors.T[0].values, sub)):
        if i % 2 != 0:
            linestyle = "dashed"
        else:
            linestyle = "solid"
        axis.plot(sub.index, (sub[col]-273.15).values, color=str(color/255.), linestyle=linestyle) # to Celsius
    axis.legend(sub.columns, loc="lower left")

# set label as temperature for second axis:
ax[1].set_ylabel("Temperature [\N{DEGREE SIGN}C]")
# fix datetime x-axis for better visuals

date_form = DateFormatter("%b-%d")
#date_form = DateFormatter("%Y-%m-%d")
#ax[2].xaxis.set_major_formatter(date_form)

#locator = mdates.DayLocator()
#ax[0].xaxis.set_major_locator(locator)


ax[0].xaxis.set_visible(False)
ax[1].xaxis.set_visible(False)

ax[0].set_ylim([5,35])

fig.tight_layout()
plt.show()

