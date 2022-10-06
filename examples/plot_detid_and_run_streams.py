"""
Access detector IDs and run tables
==================================

This example shows how to retrieve a detector version, and the list of
runs for this detector configuration.

author: Valentin Pestel (vpestel@nikhef.nl)
"""


import km3db
import pandas as pd

#####################################################
# First, we declare the sds client. This object will take care of the
# DB connection. ``container`` is set to `pd`, which means the sds
# will return ``pandas.DataFrame``.

sds = km3db.tools.StreamDS(container="pd")


#####################################################
# Getting the detectors list
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# The detectors list is available in the `detectors` stream.

print(sds.detectors())

#####################################################
# We can see that the list of detectors is quite long, because it
# includes also testing setup in several laboratories.
# The actual detectors, ORCA and ARCA, are respectively associated to
# France and Italy as `CITY`. We can use these selectors to narrow
# down the selection:

print(sds.detectors(city="France"))
print(sds.detectors(city="Italy"))

#####################################################
# Often, we want to look at a specific detector, for which we have the
# serial number, e.g. ORCA6 with the serial number 49. It is possible
# to use that as a selector too:

print(sds.detectors(serialnumber=49))

#####################################################
# Getting the run list for a given detector
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Now that we have access to the detector list, we can look at the
# list of runs for a given setup. This is contained in the `runs`
# stream. We will use the last detector from the ARCA list as an
# example. Note that `detid` is the `runs` tables is the `OID` from
# the detector stream.  Let's look at the list of run for this
# configuration:

# Take the last detector config for ARCA
det = sds.detectors(city="Italy").iloc[-1]
print(det)

runs = sds.runs(detid=det["OID"])
print(runs)

#####################################################
# This table contains information relative to the job settings:

print(list(runs.columns))

#####################################################
# We can see that the start/stop time of the run is provide with
# `UNIXJOBSTART`/`UNIXJOBEND`. Using ``pandas.to_datetime``, we create
# new variable in datetime format, allowing an easier usage.

runs["datetime_start"] = pd.to_datetime(runs["UNIXJOBSTART"], unit="ms")
runs["datetime_stop"] = pd.to_datetime(runs["UNIXJOBEND"], unit="ms")

print(runs)


#####################################################
# Access individual run
# ~~~~~~~~~~~~~~~~~~~~~
#
# It is often necessary to access the information run per run, or for
# a set of runs. A good option for that is to use the indexing of dataframe.
# First, we set the `RUN` to be the index:

runs = runs.set_index("RUN")

#####################################################
# The first column is now containing the run number, and each row can
# be accessed with this index, using the `loc` getter:

run_id = runs.sample(1).index[0]  # Get a random run number from the frame
print(f"For this example, we will be using {run_id}.")

#####################################################
# Now, to access the information for this run:
print(runs.loc[run_id])

#####################################################
# And accessing a specific information for this run:
print(f"The run setup name for run {run_id} was: {runs.loc[run_id]['RUNSETUPNAME']}")
