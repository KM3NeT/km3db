Unreleased changes
------------------


Version 0
---------
0.11.1 / 2022-12-01
~~~~~~~~~~~~~~~~~~~
* Adds preliminary support for class B and class C cookies via
  a new ``km3netdbcookie`` command line utility

0.11.0 / 2022-11-24
~~~~~~~~~~~~~~~~~~~
* The session cookies for Lyon CC and the old Jupyter server are removed
  due to the uncontrolled traffic on the database web API. From now on
  only GitLab CI is whitelisted and you need a personal session cookie

0.10.1 / 2022-10-27
~~~~~~~~~~~~~~~~~~~
* Rename columns which are not named according to the specs when
  uploading data to runsummary numbers/strings

0.10.0 / 2022-10-26
~~~~~~~~~~~~~~~~~~~
* Added support for uploading runsummary strings

0.9.0 / 2022-10-07
~~~~~~~~~~~~~~~~~~
* Added support for direct HDF5 and CSV output: no shell-piping needed anymore:
  ``streamds get detectors -o detectors.csv``.

0.8.0 / 2022-09-26
~~~~~~~~~~~~~~~~~~
* Allow option for ``detx`` to choose the format version with ``-v``

0.7.5 / 2022-09-01
~~~~~~~~~~~~~~~~~~
* Added the updated KM3NeT DB cookie for the new GitLab CI runners

0.7.4 / 2022-01-17
~~~~~~~~~~~~~~~~~~
* Improved the behaviour when the extern IP identification fails

0.7.3 / 2021-12-01
~~~~~~~~~~~~~~~~~~
* Several stability improvements for the database access functions
* Added a catch and retry for "connection refused" in the ``DBManager``

0.7.2 / 2021-10-11
~~~~~~~~~~~~~~~~~~
* Fixed the calibset retrieval for ``detx DET_ID RUN`` since the default
  values has changed

0.7.1 / 2021-09-30
~~~~~~~~~~~~~~~~~~
* Removed ``coloredlogs`` dependency

0.7.0 / 2021-05-19
~~~~~~~~~~~~~~~~~~
* ``streamds upload`` is now available

0.6.0 / 2021-04-17
~~~~~~~~~~~~~~~~~~
* Added missing dependency ``pytc`` to the requirements
* Refactored the ``tools.detx`` and ``tools.detx_for_run`` functions
* The KM3NeT DB cookie can now also be provided via an environment variable
  ``KM3NET_DB_COOKIE``

0.5.2 / 2021-02-23
~~~~~~~~~~~~~~~~~~
* Fixed ``runinfo``

0.5.1 / 2021-02-12
~~~~~~~~~~~~~~~~~~
* Forces IPv4 for the DB Webserver since IPv6 is not supported

0.5.0 / 2020-10-25
~~~~~~~~~~~~~~~~~~
* ``wtd``, ``runtable`` and ``runinfo`` command line utilities ported
  from km3pipe
* Lots of tiny improvements
* Automatic cookie deletion and retry when authentication fails (403)

0.4.2 / 2020-10-19
~~~~~~~~~~~~~~~~~~
* Helpers to convert det ID to OID and vice versa:
  ``tools.todetid`` and ``tools.todetoid``

0.4.1 / 2020-10-19
~~~~~~~~~~~~~~~~~~
* ``detx`` command line utility has been added

0.4.0 / 2020-10-18
~~~~~~~~~~~~~~~~~~
* ``tools.detx`` and ``tools.detx_for_run`` added
* ``tools.JSONDS`` added

0.3.0 / 2020-09-23
~~~~~~~~~~~~~~~~~~
* ``tools.StreamDS`` added
* the  ``streamds`` command line utility has been added
* the ``km3db`` command line utility has been added

0.2.0 / 2020-09-22
~~~~~~~~~~~~~~~~~~
* ``DBManager`` added

0.1.0 / 2020-09-21
~~~~~~~~~~~~~~~~~~
* Project generated using the cookiecutter template from
  https://git.km3net.de/templates/python-project
