KM3NeT database library
=======================

.. image:: https://git.km3net.de/km3py/km3db/badges/master/pipeline.svg
    :target: https://git.km3net.de/km3py/km3db/pipelines

.. image:: https://git.km3net.de/km3py/km3db/badges/master/coverage.svg
    :target: https://km3py.pages.km3net.de/km3db/coverage

.. image:: https://git.km3net.de/examples/km3badges/-/raw/master/docs-latest-brightgreen.svg
    :target: https://km3py.pages.km3net.de/km3db


``km3db`` is a lightweight library to access the web API of the KM3NeT Oracle
database (https://km3netdbweb.in2p3.fr). It only requires Python 3.8 or later and
comes with a small set of command line utilities which can be used in
shell scripts.

Installation
------------

Tagged releases are available on the Python Package Index repository (https://pypi.org)
and can easily be installed with the ``pip`` command::

  pip install km3db

Database Access with Cookies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The KM3NeT DB credentials should be used to obtain a session cookie which is
then passed to the database web API for all future requests. The cookie file
can be stored as a file and the default location is ``~/.km3netdb_cookie``.
If you want to use a different file, set the ``KM3NET_DB_COOKIE_FILE`` to the
desired file and each request made with ``km3db`` will use that cookie. You
can also specify ``KM3NET_DB_COOKIE`` as a string value, which then will be used
as a session ID cookie. This is useful if you work in environments where you can't
or don't want to store files.

See the section below how to use the ``km3dbcookie`` command line tool explicity
to obtain a session cookie from the command line. Notice that cookies are
automatically handled behind the scenes if you use any of the ``km3db``
functionality.

Python Classes
--------------

The three important classes are ``DBManager``, ``StreamDS`` and ``CLBMap``.

``DBManager``
~~~~~~~~~~~~~
The ``DBManager`` class manages the authentication and cookie management and
low level access to the database::

  >>> import km3db
  >>> db = km3db.DBManager()

It tries to figure out the easiest way to authenticate with the database gateway.
If launched on the Lyon CC, GitLab CI or the KM3NeT JupyterHub service, it will
automatically use the corresponding session cookies.
If not operating on whitelisted hosts, the environment variables ``KM3NET_DB_USERNAME``
and ``KM3NET_DB_PASSWORD`` will be used. If those are not set, it will look for a
cookie in ``~/.km3netdb_cookie``. As a last resort, it will prompt the user to
enter the username and password manually.
After a successful authentication, a cookie file with the session cookie will be
stored in the above mentioned file for future authentications.

``StreamDS``
~~~~~~~~~~~~
The ``StreamDS`` class is specifically designed to access the Stream Data Service
entrypoint of the database, which is meant to provide large datasets, potentially
exceeding multiples of GB::

  >>> import km3db
  >>> sds = km3db.StreamDS()
  >>> print(sds.detectors())
  OID	SERIALNUMBER	LOCATIONID	CITY	FIRSTRUN	LASTRUN
  D_DU1CPPM	2	A00070004	Marseille	2	10
  A00350276	3	A00070003	Napoli	0	0
  ...
  ...
  D1DU039CT	59	A02181273	Catania	408	480
  D0DU040CE	60	A01288502	Caserta	0	0
  >>> print(sds.get("detectors"))  # alternative way to call it
  ...

In km3pipe v8 and below, the `StreamDS` class always returned `pandas.DataFrames`
by default. This has been changed in `km3db` and by default, only the raw ASCII
output is returned, as delivered by the database.

One can however change the output container type back to `pandas.DataFrame` by
passing `container="pd"` to either the `StreamDS()` constructor or to the
`.get()` function itself. Another supported container type is `namedtuple` from
the Python standard library (`collections.namedtuple`), available via
`container="nt"`::

   >>> sds = km3db.StreamDS(container="pd")
   >>> type(sds.detectors())
   pandas.core.frame.DataFrame

   # pandas DataFrame only on a specific call
   >>> sds = km3db.StreamDS()
   >>> type(sds.get("detectors", container="pd"))
   pandas.core.frame.DataFrame

   # namedtuple
   >>> sds.get("detectors", container="nt")[0]
   Detectors(oid='D_DU1CPPM', serialnumber=2, locationid='A00070004', city='Marseille', firstrun=2, lastrun=10)

``CLBMap``
~~~~~~~~~~
The ``CLBMap`` is a powerful helper class which makes it easy to query detector
configurations and CLB::

  >>> import km3db
  >>> clbmap = km3db.CLBMap("D_ORCA003")
  >>> clb = clbmap.omkeys[(1, 13)]
  >>> clb
  Clbmap(det_oid='D_ORCA003', du=1, floor=13, serial_number=374, upi='3.4.3.2/V2-2-1/2.374', dom_id=808949902)
  >>> clb.dom_id
  808949902
  >>> clb.upi
  '3.4.3.2/V2-2-1/2.374'

Command Line Utilities
----------------------

The following command line utilities will be accessible after installing ``km3db``.

``km3dbcookie``
~~~~~~~~~~~~~~~~~~

The ``km3netdbcookie`` command can be used to obtain a session cookie using the
KM3NeT DB credentials::

    $ km3dbcookie -h
    Generate a cookie for the KM3NeT Oracle Web API.

    Usage:
        km3dbcookie [-B | -C]
        km3dbcookie (-h | --help)
        km3dbcookie --version

    Options:
        -B             Request the cookie for a class B network (12.23.X.Y).
        -C             Request the cookie for a class C network (12.23.45.Y).
        -h --help   Show this screen.

    Example:

        $ km3dbcookie -B
        Please enter your KM3NeT DB username: tgal
        Password:
        Cookie saved as '/Users/tamasgal/.km3netdb_cookie'
        $ cat /Users/tamasgal/.km3netdb_cookie
        .in2p3.fr	TRUE	/	TRUE	0	sid	_tgal_131.188_70b78042c03a434594b041073484ce23

``detx``
~~~~~~~~~~~~

The ``detx`` command can be used to retrieve calibration information from the
database formatted as DETX, which is its main offline representation format::

  $ detx -h
  Retrieves DETX files from the database.

  Usage:
      detx [options] DET_ID
      detx DET_ID RUN
      detx (-h | --help)
      detx --version

  Options:
      DET_ID        The detector ID (e.g. 49)
      RUN           The run ID.
      -c CALIBR_ID  Geometrical calibration ID (eg. A01466417)
      -t T0_SET     Time calibration ID (eg. A01466431)
      -o OUT        Output folder or filename.
      -h --help     Show this screen.

  Example:

      detx 49 8220  # retrieve the calibrated DETX for run 8220 of ORCA6

``streamds``
~~~~~~~~~~~~

The ``streamds`` command provides access to the "Stream Data Service" which was
designed to deal with large datasets potentially exceeding multiple GB in size.
The help output explains all the available functionality of the tool::

  $ streamds -h
  Access the KM3NeT StreamDS DataBase service.

  Usage:
      streamds
      streamds list
      streamds info STREAM
      streamds get [-f FORMAT -o OUTFILE -g GROUPBY] STREAM [PARAMETERS...]
      streamds upload [-q -x] CSV_FILE
      streamds (-h | --help)
      streamds --version

  Options:
      STREAM      Name of the stream.
      PARAMETERS  List of parameters separated by space (e.g. detid=29).
      CSV_FILE    Whitespace separated data for the runsummary tables.
      -f FORMAT   Usually 'txt' for ASCII or 'text' for UTF-8 [default: txt].
      -o OUTFILE  Output file: supported formats '.csv' and '.h5'.
      -g COLUMN   Group dataset by the name of the given row when writing HDF5.
      -q          Test run! When uploading, a TEST_ prefix will be added to the data.
      -x          Do not verify the SSL certificate.
      -h --help   Show this screen.

For example, a list of available detectors::

  > streamds get detectors
  OID	SERIALNUMBER	LOCATIONID	CITY	FIRSTRUN	LASTRUN
  D_DU1CPPM	2	A00070004	Marseille	2	10
  A00350276	3	A00070003	Napoli	0	0
  D_DU2NAPO	5	A00070003	Napoli	98	428
  D_TESTDET	6	A00070002	Fisciano	3	35
  D_ARCA001	7	A00073795	Italy	1	2763
  FR_INFRAS	8	A00073796	France	1600	3202
  D_DU003NA	9	A00070003	Napoli	1	242
  D_DU004NA	12	A00070003	Napoli	243	342
  D_DU001MA	13	A00070004	Marseille	1	1922
  D_ARCA003	14	A00073795	Italy	1	6465

To write the database output to a file, use the ``-o`` option, e.g.
``streamds get detectors -o detectors.csv``. The currently supported
filetypes are ``.csv`` and ``.h5``. In case of ``.h5``, the data can
be grouped by providing ``-g COLUMN``, which will split up the
output and write distinct HDF5 dataset. It's useful to group large
datasets by e.g. ``RUN``, however, only numerical datatypes are supported
currently::

  > streamds get toashort detid=D0ORCA010 minrun=13000 maxrun=13005 -g RUN -o KM3NeT_00000100_toashort.h5
  Database output written to 'KM3NeT_00000100_toashort.h5'.


``km3db``
~~~~~~~~~

The ``km3db`` command gives direct access to database URLs and is mainly a
debugging tool::

  $ km3db -h
  Command line access to the KM3NeT DB web API.

  Usage:
      km3db URL
      km3db (-h | --help)
      km3db --version

  Options:
      URL         The URL, starting from the database website's root.
      -h --help   Show this screen.

  Example:

      km3db "streamds/runs.txt?detid=D_ARCA003"

The URL parameter is simply the string which comes right after
``https://km3netdbweb.in2p3.fr/``.
