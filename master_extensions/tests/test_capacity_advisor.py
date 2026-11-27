import datetime as dt
import runpy
import unittest
from pathlib import Path
M=runpy.run_path(str(Path(__file__).resolve().parents[2]/"infra/runtime/hoosh-capacity-advisor"))
NOW=dt.datetime(2026,11,26,19,0,tzinfo=dt.timezone.utc)

class CapacityTests(unittest.TestCase):
    def row(self,minutes=0,**kw):
        return dict({"ts":NOW-dt.timedelta(minutes=minutes),"ram_mib":2100,
                     "swap_free_mib":2000,"disk_free_gib":20,"cpu_psi60":15,
                     "memory_psi60":0,"io_psi60":0},**kw)
    def summarize(self,latest=None,disk=20,used=70):
        return M["summarize"](latest or self.row(),[self.row(i) for i in range(1,11)],NOW,disk,used)
    def test_thresholds_do_not_authorize(self):
        r=self.summarize()
        self.assertEqual(r["decision"],"thresholds_met")
        self.assertFalse(r["execution_authorized"])
    def test_disk_warning_and_block(self):
        self.assertEqual(self.summarize(disk=9.9,used=90)["decision"],"review_required")
        self.assertEqual(self.summarize(disk=7)["decision"],"blocked")
    def test_stale_and_cpu(self):
        self.assertIn("monitor_stale",self.summarize(self.row(4))["blockers"])
        self.assertIn("cpu_pressure_high",self.summarize(self.row(cpu_psi60=41))["blockers"])
    def test_ram(self):
        self.assertIn("ram_below_1536_mib",self.summarize(self.row(ram_mib=1400))["blockers"])

    def test_policy_under_pressure(self):
        r=self.summarize(disk=9.9,used=90)["workload_policy"]
        self.assertEqual(r["local_build"],"defer")
        self.assertEqual(r["new_runtime"],"review")
        self.assertEqual(r["retention_review"],"prioritize")
        self.assertEqual(r["existing_services"],"preserve")
        self.assertEqual(r["backup_and_health"],"preserve")
        self.assertFalse(r["execution_authorized"])
    def test_policy_block_and_healthy(self):
        r=self.summarize(self.row(cpu_psi60=41))["workload_policy"]
        self.assertEqual(r["new_runtime"],"defer")
        self.assertEqual(self.summarize()["workload_policy"]["local_build"],"review")
        self.assertFalse(self.summarize()["workload_policy"]["execution_authorized"])
