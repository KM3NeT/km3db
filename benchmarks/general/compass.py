#!/usr/bin/env python3

import km3db

assert '3.4.3.4/AHRS/1.551'    == km3db.tools.clbupi2compassupi('3.4.3.2/V2-2-1/2.551')
assert '3.4.3.4/AHRS/1.76'     == km3db.tools.clbupi2compassupi('3.4.3.2/V2-2-1/2.76')
assert '3.4.3.4/LSM303/3.1106' == km3db.tools.clbupi2compassupi('3.4.3.2/V2-2-1/3.1013')
assert '3.4.3.4/LSM303/3.948'  == km3db.tools.clbupi2compassupi('3.4.3.2/V2-2-1/3.855')


