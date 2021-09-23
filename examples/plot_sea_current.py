"""
Retrieve and exploit sea current data
=====================================

The following example shows how to retrieve sea current data and
reduce them to a run per run scale.
"""

import km3db
import pandas as pd
import numpy as np

#####################################################
# Get a list of runs
# ~~~~~~~~~~~~~~~~~~
# To start, we will get a list of runs for which we later want to get
# the sea data.
#
# In this example, ORCA6 is used (det OID = "D_ORCA006") with runs 8500 to 8600

sds = km3db.tools.StreamDS(container="pd")

run_min = 8500
run_max = 8600
detid = "D_ORCA006"

runs = sds.runs(detid=detid)
runs = runs.set_index("RUN")
runs = runs[(runs.index >= run_min) & (runs.index <= run_max)]

# Add human-readable datetime object for the start and the stop of
# each run

runs["start"] = pd.to_datetime(runs["UNIXJOBSTART"], unit="ms")
runs["end"] = pd.to_datetime(runs["UNIXJOBEND"], unit="ms")

print(runs)

#####################################################
# Preparing the request
# ~~~~~~~~~~~~~~~~~~~~~
#
# The sea data are retrieved from this website:
# https://erddap.osupytheas.fr/erddap/tabledap/Emso_Ligure_Ouest_MII_Aquadopp_CSV.html
# Here we are downloading the data in csv format, then import them
# with pandas. The query is constructed in the following way:
#
# * <url>: base of the query
# * <sensor>: name of the sensor on which we query the
#   data. 'Emso_Ligure_Ouest_MII_Aquadopp_CSV' is the one close to
#   km3net ORCA.
# * <filetype>: specify the return format you want.
# * <variables>: list of variables you want to retrieve, coma
#   separated without spaces. Return everything if empty.
# * <selection>: selection criteria. In this example, we use this to
#   specify a time range.
#
# At the end, the html query should looks like :
# <url>/<sensor>.<filetype>?<variables>&<selection>

import urllib, urllib.request

# Determine the time boundary of the runs list
mindate = runs["start"].min()
maxdate = runs["end"].max()

# Prepare the query content
queryInf = {
    "url": "https://erddap.osupytheas.fr/erddap/tabledap/",
    "sensor": "Emso_Ligure_Ouest_MII_Aquadopp_CSV",
    "filetype": "csv",
    "variables": "",
    "selection": "time>={}&time<={}".format(
        mindate.strftime("%Y-%m-%dT%H:%M:%SZ"), maxdate.strftime("%Y-%m-%dT%H:%M:%SZ")
    ),
}

# Data are temporally downloaded in a csv file, in the work directory
tmp_csv_file = "tmp.csv"

# Format the query
query = "{url}{sensor}.{filetype}?".format(**queryInf)
query += urllib.request.quote("{variables}&{selection}".format(**queryInf), safe="")

# Do the query and store the returned file
urllib.request.urlretrieve(query, tmp_csv_file)

# Open the csv file with pandas.
df = pd.read_csv(open(tmp_csv_file), header=[0, 1])
# Small trick to avoid having ugly column names
df.columns = np.stack(df.columns)[:, 0]

# Add a datetime columns, based on the time string
df["datetime"] = pd.to_datetime(df["time"]).dt.tz_localize(None)

print(df)

#####################################################
# Simple plot of sea current
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# To check what we have downloaded, let's do simple plots.
#
# In the first figure, we are plotting the sea current direction and
# speed, both in Cartesian coordinates (left) and polar coordinates
# (right).
#
# The left plot shows the X (pointing east) vs Y (pointing north)
# speed components of the sea current. The color scale indicate the
# angle, and shows that 0° is north, 90° is east.
#
# The right plot shows the direction vs speed in polar
# coordinates. Following left plot hints, we also tune the plot to
# display the data in the natural cardinal points orientation.

import matplotlib.pyplot as plt

fig = plt.figure(figsize=[7, 4])

ax1 = plt.subplot(121)
ax2 = plt.subplot(122, projection="polar")

ax1.set_xlabel("X east [m.s$^-1$]")
ax1.set_ylabel("Y north [m.s$^-1$]")

# Small trick to get x and y having the same scale and same boundaries
ax1.set_aspect("equal")
max_abs = 1.2 * np.max(np.abs(df[["X_East", "Y_North"]].values))
ax1.set_xlim(-max_abs, max_abs)
ax1.set_ylim(-max_abs, max_abs)

ax1.scatter(
    df["X_East"], df["Y_North"], c=df["Direction"], vmin=0, vmax=360, marker="."
)

# Replace the ticks (in rad) by cardinal points
card_angles = np.linspace(2 * np.pi, 0.0, 9)
card_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
ax2.set_xticks(card_angles)
ax2.set_xticklabels(card_labels)
ax2.set_theta_zero_location("N")
ax2.set_xlabel("Sea current direction")

ax2.scatter(df["Direction"] / 180.0 * np.pi, df["Speed"], marker=".")

plt.tight_layout()

#####################################################
# Another useful thing to look at is the time evolution of the sea
# current, separately the speed and the direction :

fig, axes = plt.subplots(2, 1, sharex=True, figsize=[7, 4])

axes[0].scatter(df["datetime"], df["Direction"] / 180.0 * np.pi, marker=".")
axes[1].scatter(df["datetime"], df["Speed"], marker=".")

axes[0].set_yticks(card_angles)
axes[0].set_yticklabels(card_labels)

axes[0].set_ylabel("Direction")
axes[1].set_ylabel("Speed [m.s$^-1$]")

for ax in axes:
    ax.grid()

plt.tight_layout()


#####################################################
# Reduce to per run information
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# In this part, we will produce a new dataframe, that will contains
# the average value of the sea current, as well as the standard
# deviation, per data run.
#
# First, we are attaching each of the measurement to a run.


# Creating a new columns to store the run_id
df["run_id"] = np.zeros(df.shape[0], dtype=int)

for run, row in runs.iterrows():
    # Select the sea current measurements corresponding to the given run
    df_tmp = df[(df["datetime"] > row["start"]) & (df["datetime"] < row["end"])]

    # Loop over the measurements to attribute them the run_id
    for ind in df_tmp.index:
        df.at[ind, "run_id"] = run

print(df)

#####################################################
# The last columns is now showing the run_id for each measurement. Now
# let's use some pandas magic, to group the measurement per run.


df_runs = df.groupby("run_id").mean()

# the averaging process doesn't work for the angles, we therefor have
# to recompute the direction from the X and Y component of speed:
df_runs["Direction"] = np.arctan2(df_runs["X_East"], df_runs["Y_North"]) % (2 * np.pi)
df_runs["Direction"] *= 180.0 / np.pi

# Remove the orphan points
df_runs = df_runs[df_runs.index != 0]

print(df_runs)


#####################################################
# Plotting per run information
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# And finally, we want to check how look the per run information
# compare to the single measurement points.


# Determine the common index list between runs and df.
# Take the runs available in df_runs
ind = df_runs.index
# Then keep only the one also in runs
ind = ind.intersection(runs.index)


runDuration = runs.loc[ind]["end"] - runs.loc[ind]["start"]
runCenter = runs.loc[ind]["start"] + runDuration / 2.0

direction = df_runs.loc[ind]["Direction"] / 180.0 * np.pi
speed = df_runs.loc[ind]["Speed"]

fig, axes = plt.subplots(2, 1, sharex=True, figsize=[7, 4])

axes[0].scatter(
    df["datetime"], df["Direction"] / 180.0 * np.pi, marker=".", color="gray"
)
axes[1].scatter(df["datetime"], df["Speed"], marker=".", color="gray")

axes[0].errorbar(runCenter, direction, xerr=runDuration / 2.0, fmt=".")
axes[1].errorbar(runCenter, speed, xerr=runDuration / 2.0, fmt=".")

axes[0].set_yticks(card_angles)
axes[0].set_yticklabels(card_labels)

axes[0].set_ylabel("Direction")
axes[1].set_ylabel("Speed [m.s$^-1$]")

for ax in axes:
    ax.grid()

plt.tight_layout()
plt.show()
