"""
Access run summary numbers stream
=================================

The following example shows how to use the run summary numbers stream
to access summary information per run.

- The first part shows the content of the Stream.
- The second part explore the usage to get detector-related summary
  number, like the overall HRV fraction or the DAQ event rate.
- The third part shows how to access DOM related information, like the
  average rate of a specific PMT during the run.

author: Valentin Pestel (vpestel@nikhef.nl)
"""

import km3db
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

#####################################################
# First, we declare the sds client. This object will take care of the
# DB connection. ``container`` is set to `pd`, which means the sds
# will return ``pandas.DataFrame``.

sds = km3db.tools.StreamDS(container="pd")

#####################################################
# What contains runsummarynumbers stream ?
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# To explore what contains this Stream, we will first query few runs
# from ORCA6 and print the resulting dataframe.

df = sds.runsummarynumbers(detid="D_ORCA006", minrun=8000, maxrun=8000)
print(df)

#####################################################
# Let's take a look in the `SOURCE_NAME` column :

print(df["SOURCE_NAME"].unique())

#####################################################
# We can already see 2 categories of `SOURCE_NAME':
#
# - Some corresponding to DOM module ID. These values are representing
#   summary information per DOM.
# - Some corresponding to version numbers. These values are
#   representing summary information for the whole detector. The
#   version number correspond to the JPP version used to compute these
#   meta-variables.


#####################################################
# Exploit detector-related summary information
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# This time we will get a much larger set of runs, but we will only
# get the information from `SOURCE_NAME == 14.4.1` (last JPP version
# when this example was wrote).

run_min = 8000
run_max = 8500
detid = "D_ORCA006"

df = sds.runsummarynumbers(
    detid=detid, minrun=run_min, maxrun=run_max, source_name="14.4.1"
)

#####################################################
#
# We will use the `pivot` function to re-arrange the dataframe
# shape in a more practical way.

df = df.pivot(index="RUN", columns="PARAMETER_NAME", values="DATA_VALUE")
print(df)

#####################################################
#
# Now let's look at what is available in the columns :
print(list(df.columns))

#####################################################
#
# One can notice two time-related variables: `UTCMin_s` and
# `UTCMax_s`.  These two variables contains the start and stop time of
# the run, in seconds. In python, it's often more convenient to
# convert the time object to datetime-objects. Pandas is having a very
# convenient function for that: ``pandas.to_datetime``.  In the
# following lines, we are defining 3 new columns, respectively
# containing the start, mean and stop time of the run:

df["t_start"] = pd.to_datetime(df["UTCMin_s"], unit="s")
df["t_stop"] = pd.to_datetime(df["UTCMax_s"], unit="s")
df["t_mean"] = pd.to_datetime(np.mean(df[["UTCMin_s", "UTCMax_s"]], axis=1), unit="s")

print(df)

#####################################################
#
# As a first example, we can look at the evolution of HRV and mean PMT
# rate in function of time.  For the mean PMT rate, we also represent
# its +/- standard variation.

fig, axe = plt.subplots(figsize=[12, 4])

axeb = axe.twinx()

axe.plot(df["t_start"], df["MEAN_Rate_Hz"], color="C0")
ymin = df["MEAN_Rate_Hz"] - df["RMS_Rate_Hz"]
ymax = df["MEAN_Rate_Hz"] + df["RMS_Rate_Hz"]
axe.fill_between(df["t_start"], ymin, ymax, color="C0", alpha=0.5)

axeb.plot(df["t_start"], df["HRV"], color="C1")

axe.set_ylabel("PMT rate [kHz]")
axe.yaxis.label.set_color("C0")

axeb.set_ylabel("High rate veto fraction")
axeb.yaxis.label.set_color("C1")

#####################################################
#
# We can also look at the events rate, with a break down of the
# different trigger rates

triggers_name = ["JTrigger3DMuon", "JTrigger3DShower", "JTriggerMXShower"]

fig, axe = plt.subplots(figsize=[12, 4])
axe.set_yscale("log")

axe.plot(
    df["t_start"],
    df["JDAQEvent"] / df["livetime_s"],
    color="gray",
    label="DAQ events",
    zorder=0,
)

for name in triggers_name:
    axe.plot(df["t_start"], df[name] / df["livetime_s"], label=name, zorder=1)

axe.set_ylabel("Rate [kHz]")
axe.legend()

plt.tight_layout()


#####################################################
# Exploit DOM-related summary information
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# First, we will remove the detector-related information from the
# dataframe. For this, we only keep the `SOURCE_NAME` starting by
# `80`. As all the `SOURCE_NAME` are now an integer, we convert them
# to int.

df = sds.runsummarynumbers(detid="D_ORCA006", minrun=8000, maxrun=8050)
df = df[df["SOURCE_NAME"].str.contains("^80.*")]
df = df.astype({"SOURCE_NAME": int})

#####################################################
# We will use the `pivot` function to re-arrange the dataframe
# shape in a more practical way.
# We would like a dataframe with the columns name being
# `PARAMETER_NAME`, each rows being the showing the `VALUES` for a
# given module (`SOURCE_NAME`) during a given `RUN`.
# This is done with the following line :

df = df.pivot(
    index=["SOURCE_NAME", "RUN"], columns="PARAMETER_NAME", values="DATA_VALUE"
)
print(df)

#####################################################
# We can look at the list of available columns :

print(list(df.columns))

#####################################################
# Finally, let's plot the evolution of the rate per PMT for a given
# module ID. Here, we randomly pick `806451572`.

mID = 806451572

fig, axe = plt.subplots(figsize=[8, 4])
axe.set_yscale("log")

cmap = mpl.cm.get_cmap("viridis")

for i in range(31):
    colName = "pmt_{}_mean_rate".format(i)
    color = cmap(i / 30.0)
    axe.plot(df.loc[mID].index, df.loc[mID][colName], color=color)

axe.set_xlabel("Run ID")
axe.set_ylabel("Mean rate [kHz]")
plt.tight_layout()


plt.show()
