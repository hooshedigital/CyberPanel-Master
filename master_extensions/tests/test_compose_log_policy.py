import importlib.util
from pathlib import Path
import unittest
import yaml
P=Path(__file__).resolve().parents[2]/"scripts/compose_log_policy.py"
spec=importlib.util.spec_from_file_location("compose_log_policy",P)
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

class ComposeLogPolicyTests(unittest.TestCase):
    SAMPLE='''# retain comment
services:
  web:
    image: example:stage
    environment:
      VALUE: "\${VALUE:-test}"
  db:
    image: db:stage
volumes:
  storage: {}
'''
    def test_only_selected_service_changes(self):
        output=M.transform(self.SAMPLE,["web"])
        before=yaml.safe_load(self.SAMPLE)
        before["services"]["web"]["logging"]=M.POLICY
        self.assertEqual(yaml.safe_load(output),before)
        self.assertIn("# retain comment",output)
        self.assertEqual(M.transform(output,["web"]),output)
    def test_two_services(self):
        output=M.transform(self.SAMPLE,["web","db"])
        self.assertEqual(yaml.safe_load(output)["services"]["db"]["logging"],M.POLICY)
    def test_existing_policy_preserved(self):
        bad=self.SAMPLE.replace("    image: example:stage","    logging:\n      driver: local\n    image: example:stage")
        with self.assertRaises(ValueError):M.transform(bad,["web"])
    def test_duplicate_missing_alias_and_feast_rejected(self):
        for source,names in [
            (self.SAMPLE,["web","web"]),
            (self.SAMPLE,["missing"]),
            (self.SAMPLE.replace("  web:","  feast:"),["feast"]),
            (self.SAMPLE.replace("  web:","  web: &test"),["web"]),
            (self.SAMPLE.replace("    image: example:stage","    image: one\n    image: two"),["web"])]:
            with self.assertRaises(ValueError):M.transform(source,names)
