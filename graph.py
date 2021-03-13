import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import glob


'''
#'/var/opt/data/elec-2020-04-28T01:03:56+01:00.log'
#f = '/var/opt/data/elec-2020-04-28T01:12:56+01:00.log'
f = '/var/opt/data/elec-2020-04-29T00:00:00+01:00.log'


df = pd.read_csv(f, delim_whitespace=True, header=None, parse_dates=True, index_col=0)

print (df.head(3))
print (df.dtypes)

df.columns = ['interval', 'Power', 'Energy' ]
print (df.head(3))
print (df.dtypes)

print (df.index)


e = '/var/opt/data/3phase-2020-04-29T00:00:00+01:00.log'
e = pd.read_csv(e, sep='\s+|=\s*', header=None, parse_dates=True, index_col=0, usecols=[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32])
e.columns = ['frequency', 'I1', 'I2', 'I3', 'I4', 'V1', 'P1', 'P2', 'P3', 'E1', 'E2', 'E3', 'T1', 'XPower', '3Energy', 'spin']

print (e.head(3))
print (e.dtypes)
print (e.index)

'''

wf = '/var/opt/data/'
#wf = wf + 'water-2020-05-05T00:00:00+01:00.log'
wf = wf + 'water-2020-05-06T00:00:00+01:00.log'
w = pd.read_csv(wf, delim_whitespace=True, header=None, parse_dates=True, index_col=0)
w.columns = ['start', 'verify', 'time_delta', 'rate', 'volume']

print (w.head(3))
print (w.dtypes)
print (w.index)

print (w['time_delta'][0])
print (w['time_delta'][1])


w['rate2'] = None

for i in range(len(w['time_delta'])):
    print (i, w['verify'][i])
    z = 1.33
    z= 1.4
    if w['verify'][i] == 1:
        w['rate2'][i] = 3600.0 * z / w['time_delta'][i]
    else:
        w['rate2'][i] = 3600.0 * (10-z) / w['time_delta'][i]


app = dash.Dash()

'''    
    dcc.Graph(
        id='example',
        figure={
            'data': [
                #{'x': [1, 2, 3, 4, 5], 'y': [9, 6, 2, 1, 5], 'type': 'line', 'name': 'Boats'},
                { 'x' : e.index,  'y': e.XPower, 'type': 'line', 'name': 'XPower'},
                { 'x' : df.index, 'y': df.Power, 'type': 'line', 'name': 'Power1'},
            ],
            'layout': {
                'title': 'Basic Dash Example'
            }
    }),
    dcc.Graph(
        id='phases',
        figure={
            'data': [
                #{'x': [1, 2, 3, 4, 5], 'y': [9, 6, 2, 1, 5], 'type': 'line', 'name': 'Boats'},
                { 'x' : e.index,  'y': e.I1, 'type': 'line', 'name': 'I1'},
                { 'x' : e.index,  'y': e.I2, 'type': 'line', 'name': 'I2'},
                { 'x' : e.index,  'y': e.I3, 'type': 'line', 'name': 'I3'},
            ],
            'layout': {
                'title': 'Current on each phase',
            },
    }),
'''
app.layout = html.Div(children=[
    html.H1(children='Dash Tutorials'),

    dcc.Graph(
        id='water',
        figure={
            'data': [
                #{'x': [1, 2, 3, 4, 5], 'y': [9, 6, 2, 1, 5], 'type': 'line', 'name': 'Boats'},
                { 'x' : w.index,  'y': w.rate, 'type': 'line', 'name': 'rate'},
                { 'x' : w.index,  'y': w.rate2, 'type': 'line', 'name': 'rate2'},
                { 'x' : w.index,  'y': w.volume, 'type': 'line', 'name': 'volume'},


            ],
            'layout': {
                'title': 'Current on each phase',
            },
        }),
    dcc.RangeSlider()
])


if __name__ == '__main__':
    app.run_server(debug=True, host= "0.0.0.0")

"""
import pandas as pd
import glob
import matplotlib.pyplot as plt


e = pd.read_csv('/var/opt/data/elec-2020-04-28T01:12:56+01:00.log', delim_whitespace=True, header=None, parse_dates=True, index_col=0)

print (e.shape)

print (e.head(3))
print (e.dtypes)

e[2].plot
"""






