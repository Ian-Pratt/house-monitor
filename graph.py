import pandas as pd
import glob
import matplotlib.pyplot as plt


e = pd.read_csv('elec-2020-04-21T15:13:20+01:00.log', delim_whitespace=True, header=None, parse_dates=True, index_col=0)

print (e.shape)

print (e.head(3))
print (e.dtypes)

e[2].plot





