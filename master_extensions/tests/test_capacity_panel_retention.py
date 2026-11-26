import datetime as dt
import runpy
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
M=runpy.run_path(str(ROOT/"infra/runtime/hoosh-docker-retention"))
from master_extensions import capacity_panel as P

class RetentionTests(unittest.TestCase):
    def test_all_tags_and_refs_are_distinct(self):
        a,b,c=["sha256:"+x*64 for x in "abc"]
        row=lambda i,r,t:{"ID":i,"Repository":r,"Tag":t}
        r=M["classify"]([row(a,"a","v1"),row(b,"<none>","<none>"),row(b,"b","v2"),row(c,"<none>","<none>")],{a})
        self.assertEqual((r["referenced"],r["tagged_unreferenced"],r["untagged_unreferenced"],r["deletion_approved"]),(1,1,1,0))
        with self.assertRaises(ValueError):M["classify"]([], {a})
    def test_missing_reports(self):
        with patch.object(P,"read_report",return_value={}):
            self.assertFalse(P.capacity_context()["ready"])
            self.assertFalse(P.capacity_context()["retention"]["ready"])
    def test_unknown_reason_fails_closed(self):
        d={"decision":"thresholds_met","blockers":[],"warnings":["unknown_code"]}
        with patch.object(P,"read_report",side_effect=[d,{}]):
            self.assertFalse(P.capacity_context()["ready"])
    def test_valid_summary(self):
        d={"decision":"review_required","warnings":["disk_headroom_warning"],"blockers":[]}
        r={"status":"review_only","deletion_approved":0,"unique_images":3,"referenced":1,"tagged_unreferenced":1,"untagged_unreferenced":1,"containers":2}
        with patch.object(P,"read_report",side_effect=[d,r]):
            p=P.capacity_context("fa")
            self.assertTrue(p["ready"])
            self.assertTrue(p["retention"]["ready"])
