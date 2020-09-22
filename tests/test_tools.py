#!/usr/bin/env python3

import unittest
from mock import patch

from km3db import StreamDS
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

    def test_pandas_as_library(self):
        detectors = self.sds.detectors(library="pd")
        assert 35 >= len(detectors)


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


# class TestCLBMapOffline(TestCase):
#     @patch("km3db.tools.StreamDS")
#     def test_call_with_det_oid(self, streamds_mock):
#         streamds_mock_obj = streamds_mock.return_value
#         with open(data_path("db/clbmap.txt"), "r") as fobj:
#             streamds_mock_obj.clbmap.return_value = read_csv(fobj.read())
#         self.clbmap = CLBMap("a")
#         streamds_mock_obj.clbmap.assert_called_with(detoid="a")

#     @patch("km3db.core.DBManager")
#     @patch("km3db.tools.StreamDS")
#     def test_call_with_det_id(self, streamds_mock, dbmanager_mock):
#         streamds_mock_obj = streamds_mock.return_value
#         dbmanager_mock_obj = dbmanager_mock.return_value
#         dbmanager_mock_obj.get_det_oid.return_value = "a"
#         with open(data_path("db/clbmap.txt"), "r") as fobj:
#             streamds_mock_obj.clbmap.return_value = read_csv(fobj.read())
#         self.clbmap = CLBMap(1)
#         streamds_mock_obj.clbmap.assert_called_with(detoid="a")

#     @patch("km3db.tools.StreamDS")
#     def setUp(self, streamds_mock):
#         streamds_mock_obj = streamds_mock.return_value
#         with open(data_path("db/clbmap.txt"), "r") as fobj:
#             streamds_mock_obj.clbmap.return_value = read_csv(fobj.read())
#         self.clbmap = CLBMap("a")

#     def test_length(self):
#         assert 57 == len(self.clbmap)

#     def test_clb_by_upi(self):
#         assert 806487231 == self.clbmap.upis["3.4.3.2/V2-2-1/2.570"].dom_id
#         assert 808964852 == self.clbmap.upis["3.4.3.2/V2-2-1/2.100"].dom_id
#         assert 808982547 == self.clbmap.upis["3.4.3.2/V2-2-1/2.121"].dom_id
#         assert 808961480 == self.clbmap.upis["3.4.3.2/V2-2-1/2.94"].dom_id
#         assert 13 == self.clbmap.upis["3.4.3.2/V2-2-1/2.570"].floor
#         assert 3 == self.clbmap.upis["3.4.3.2/V2-2-1/2.100"].du
#         assert 121 == self.clbmap.upis["3.4.3.2/V2-2-1/2.121"].serial_number
#         assert "D_ORCA003" == self.clbmap.upis["3.4.3.2/V2-2-1/2.94"].det_oid
#         for upi in self.clbmap.upis.keys():
#             assert upi == self.clbmap.upis[upi].upi

#     def test_clb_by_dom_id(self):
#         assert "3.4.3.2/V2-2-1/2.570" == self.clbmap.dom_ids[806487231].upi
#         assert "3.4.3.2/V2-2-1/2.100" == self.clbmap.dom_ids[808964852].upi
#         assert "3.4.3.2/V2-2-1/2.121" == self.clbmap.dom_ids[808982547].upi
#         assert "3.4.3.2/V2-2-1/2.94" == self.clbmap.dom_ids[808961480].upi
#         assert 13 == self.clbmap.dom_ids[806487231].floor
#         assert 3 == self.clbmap.dom_ids[808964852].du
#         assert 121 == self.clbmap.dom_ids[808982547].serial_number
#         assert "D_ORCA003" == self.clbmap.dom_ids[808961480].det_oid
#         for dom_id in self.clbmap.dom_ids.keys():
#             assert dom_id == self.clbmap.dom_ids[dom_id].dom_id

#     def test_get_base(self):
#         assert 0 == self.clbmap.base(1).floor
#         assert 0 == self.clbmap.base(3).floor
#         assert 0 == self.clbmap.base(4).floor
#         assert 808476701 == self.clbmap.base(1).dom_id
#         assert 808981515 == self.clbmap.base(3).dom_id
#         assert 808967761 == self.clbmap.base(4).dom_id
