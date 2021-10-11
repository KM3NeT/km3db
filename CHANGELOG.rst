Unreleased changes
------------------

Version 0
---------
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
