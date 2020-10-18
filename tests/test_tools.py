#!/usr/bin/env python3

import unittest
from mock import patch

from km3db import StreamDS, CLBMap
from km3db.tools import (
    clbupi2compassupi,
    tonamedtuples,
    show_compass_calibration,
    detx,
    detx_for_run,
    todetid,
    todetoid,
)
from km3net_testdata import data_path


class TestStreamDSOnline(unittest.TestCase):
    def setUp(self):
        self.sds = StreamDS()

    def test_print_streams(self):
        self.sds.print_streams()

    def test_get(self):
        detectors = self.sds.detectors()
        assert (
            "OID\tSERIALNUMBER\tLOCATIONID\tCITY\tFIRSTRUN\tLASTRUN\nD_DU1CPPM\t2\tA00070004"
            in detectors
        )

    def test_pandas_as_container(self):
        detectors = self.sds.detectors(container="pd")
        assert 35 <= len(detectors)

    def test_namedtuple_as_container(self):
        detectors = self.sds.detectors(container="nt")
        assert 35 <= len(detectors)
        assert detectors[2].oid == "D_DU2NAPO"


class TestStreamDSOffline(unittest.TestCase):
    @patch("km3db.core.DBManager")
    def setUp(self, db_manager_mock):
        with open(data_path("db/streamds_output.txt"), "r") as fobj:
            streamds_meta = fobj.read()
        db_manager_mock_obj = db_manager_mock.return_value
        db_manager_mock_obj.get.return_value = streamds_meta
        self.sds = StreamDS()

    def test_streams(self):
        assert len(self.sds.streams) == 30
        assert "ahrs" in self.sds.streams
        assert "clbmap" in self.sds.streams
        assert "datalogevents" in self.sds.streams
        assert "datalognumbers" in self.sds.streams

    def test_getattr(self):
        assert hasattr(self.sds, "t0sets")
        assert hasattr(self.sds, "vendorhv")

    def test_attr_are_callable(self):
        self.sds.runs()
        self.sds.runsetupparams()
        self.sds.upi()

    def test_mandatory_selectors(self):
        assert "-" == self.sds.streams["productloc"].mandatory_selectors
        assert "detid" == self.sds.streams["runs"].mandatory_selectors
        assert (
            "detid,minrun,maxrun"
            == self.sds.streams["datalognumbers"].mandatory_selectors
        )

    def test_optional_selectors(self):
        self.assertEqual(
            "upi,city,locationid,operation,operationid",
            self.sds.streams["productloc"].optional_selectors,
        )
        self.assertEqual(
            "run,runjobid,jobtarget,jobpriority",
            self.sds.streams["runs"].optional_selectors,
        )
        self.assertEqual(
            "source_name,parameter_name",
            self.sds.streams["datalognumbers"].optional_selectors,
        )

    def test_print_streams(self):
        self.sds.print_streams()


class TestCLBMapOffline(unittest.TestCase):
    @patch("km3db.tools.StreamDS")
    def setUp(self, streamds_mock):
        streamds_mock_obj = streamds_mock.return_value
        with open(data_path("db/clbmap.txt"), "r") as fobj:
            streamds_mock_obj.get.return_value = tonamedtuples(
                "CLB", fobj.read(), renamemap=CLBMap.renamemap
            )
        self.clbmap = CLBMap("a")

    def test_length(self):
        assert 57 == len(self.clbmap)

    def test_clb_by_upi(self):
        print(self.clbmap.upis)
        assert 806487231 == self.clbmap.upis["3.4.3.2/V2-2-1/2.570"].dom_id
        assert 808964852 == self.clbmap.upis["3.4.3.2/V2-2-1/2.100"].dom_id
        assert 808982547 == self.clbmap.upis["3.4.3.2/V2-2-1/2.121"].dom_id
        assert 808961480 == self.clbmap.upis["3.4.3.2/V2-2-1/2.94"].dom_id
        assert 13 == self.clbmap.upis["3.4.3.2/V2-2-1/2.570"].floor
        assert 3 == self.clbmap.upis["3.4.3.2/V2-2-1/2.100"].du
        assert 121 == self.clbmap.upis["3.4.3.2/V2-2-1/2.121"].serial_number
        assert "D_ORCA003" == self.clbmap.upis["3.4.3.2/V2-2-1/2.94"].det_oid
        for upi in self.clbmap.upis.keys():
            assert upi == self.clbmap.upis[upi].upi

    def test_clb_by_dom_id(self):
        assert "3.4.3.2/V2-2-1/2.570" == self.clbmap.dom_ids[806487231].upi
        assert "3.4.3.2/V2-2-1/2.100" == self.clbmap.dom_ids[808964852].upi
        assert "3.4.3.2/V2-2-1/2.121" == self.clbmap.dom_ids[808982547].upi
        assert "3.4.3.2/V2-2-1/2.94" == self.clbmap.dom_ids[808961480].upi
        assert 13 == self.clbmap.dom_ids[806487231].floor
        assert 3 == self.clbmap.dom_ids[808964852].du
        assert 121 == self.clbmap.dom_ids[808982547].serial_number
        assert "D_ORCA003" == self.clbmap.dom_ids[808961480].det_oid
        for dom_id in self.clbmap.dom_ids.keys():
            assert dom_id == self.clbmap.dom_ids[dom_id].dom_id

    def test_get_base(self):
        assert 0 == self.clbmap.base(1).floor
        assert 0 == self.clbmap.base(3).floor
        assert 0 == self.clbmap.base(4).floor
        assert 808476701 == self.clbmap.base(1).dom_id
        assert 808981515 == self.clbmap.base(3).dom_id
        assert 808967761 == self.clbmap.base(4).dom_id


class TestCLBUPI2CompassUPI(unittest.TestCase):
    def test_ahrs(self):
        assert "3.4.3.4/AHRS/1.551" == clbupi2compassupi("3.4.3.2/V2-2-1/2.551")
        assert "3.4.3.4/AHRS/1.76" == clbupi2compassupi("3.4.3.2/V2-2-1/2.76")

    def test_lsm(sefl):
        assert "3.4.3.4/LSM303/3.1106" == clbupi2compassupi("3.4.3.2/V2-2-1/3.1013")
        assert "3.4.3.4/LSM303/3.948" == clbupi2compassupi("3.4.3.2/V2-2-1/3.855")


class TestShowCompassCalibration(unittest.TestCase):
    def test_function(self):
        show_compass_calibration("3.4.3.2/V2-2-1/2.551")


class TestDetxHelpersOnline(unittest.TestCase):
    def test_detx(self):
        det_id = 49
        detx_string = detx(49)
        assert detx_string is not None
        split_lines = detx_string.split("\n")
        assert str(det_id) in split_lines[0]
        assert 3461 == len(split_lines)
        assert float(split_lines[6].split()[-1]) == 0.0  # t0 is not set

    def test_detx_for_run(self):
        det_id = 49
        detx_string = detx_for_run(49, 8220)
        assert detx_string is not None
        split_lines = detx_string.split("\n")
        assert str(det_id) in split_lines[0]
        assert 3461 == len(split_lines)
        assert float(split_lines[6].split()[-1]) != 0.0  # check a single PMT t0


class TestDetIDandOIDConversionsOnline(unittest.TestCase):
    def test_todetid(self):
        assert 49 == todetid("D_ORCA006")

    def test_todetoid(self):
        assert "D_ORCA006" == todetoid(49)
