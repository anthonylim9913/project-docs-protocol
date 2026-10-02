import hashlib, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCTOR = ROOT / "scripts/research-doctor.py"
INDEX = ROOT / "scripts/research-index.py"
WRITE = ROOT / "scripts/research-write.py"

class ResearchProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); research=self.root/"research"
        for name in ("sources", "notes", "questions", "synthesis"): (research/name).mkdir(parents=True)
        (research/"INDEX.md").write_text("# Research index\n- RQ-0001 naming — `questions/RQ-0001.md` — `SRC-0001`, `NOTE-0001`, `SYN-0001`\n- SRC-0001 — `sources/SRC-0001.md`\n- NOTE-0001 — `notes/NOTE-0001.md`\n- SYN-0001 — `synthesis/SYN-0001.md`\n", encoding="utf-8")
        (self.root/"research/SRC-0001.md").write_text("# SRC-0001 — primary\nURL: https://example.test/source\nAccessed: 2026-09-15\nContent-SHA256: " + "a"*64 + "\nPassage: exact text\nStatus: current\n", encoding="utf-8")
        (self.root/"research/SRC-0001.md").replace(self.root/"research/sources/SRC-0001.md")
        (self.root/"research/notes/NOTE-0001.md").write_text("# NOTE-0001 — claim\nSource: SRC-0001\n", encoding="utf-8")
        (self.root/"research/questions/RQ-0001.md").write_text("# RQ-0001 — naming\nEvidence: NOTE-0001\n", encoding="utf-8")
        (self.root/"research/synthesis/SYN-0001.md").write_text("# SYN-0001 — recommendation\nClaim: NOTE-0001\nDecision: owner supplied\n", encoding="utf-8")
    def tearDown(self): self.tmp.cleanup()
    def test_doctor_accepts_complete_index(self):
        p=subprocess.run([sys.executable, str(DOCTOR), str(self.root)], capture_output=True, text=True); self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_doctor_rejects_missing_source(self):
        (self.root/"research/sources/SRC-0001.md").unlink(); p=subprocess.run([sys.executable,str(DOCTOR),str(self.root)],capture_output=True,text=True); self.assertEqual(p.returncode,1); self.assertIn("missing references",p.stdout)
    def test_doctor_rejects_bad_digest_and_short_id(self):
        path=self.root/"research/sources/SRC-0001.md"; path.write_text(path.read_text().replace("a"*64, "z"), encoding="utf-8")
        (self.root/"research/notes/NOTE-0001.md").write_text("# NOTE-001 — malformed\n", encoding="utf-8")
        p=subprocess.run([sys.executable,str(DOCTOR),str(self.root)],capture_output=True,text=True); self.assertEqual(p.returncode,1); self.assertIn("invalid Content-SHA256",p.stdout); self.assertIn("malformed id NOTE-001",p.stdout)
    def test_index_retrieves_topic(self):
        p=subprocess.run([sys.executable,str(INDEX),str(self.root),"--topic","naming"],capture_output=True,text=True); self.assertEqual(p.returncode,0); self.assertIn("RQ-0001",p.stdout)
        p=subprocess.run([sys.executable,str(INDEX),str(self.root),"--id","SRC-0001"],capture_output=True,text=True); self.assertEqual(p.returncode,0); self.assertIn("Passage: exact text",p.stdout)
    def test_write_rejects_intervening_edit(self):
        target=self.root/"research/notes/NOTE-0001.md"; expected=hashlib.sha256(target.read_bytes()).hexdigest(); target.write_text("# changed\n",encoding="utf-8")
        p=subprocess.run([sys.executable,str(WRITE),str(target),"# replacement","--expected-sha256",expected,"--root",str(self.root)],capture_output=True,text=True)
        self.assertEqual(p.returncode,1); self.assertIn("stale target hash",p.stderr); self.assertEqual(target.read_text(),"# changed\n")
        self.assertTrue((target.parent / ".NOTE-0001.md.lock").is_file())
    def test_write_rejects_target_outside_research(self):
        target=self.root/"STATUS.md"; target.write_text("safe\n",encoding="utf-8")
        p=subprocess.run([sys.executable,str(WRITE),str(target),"# replacement","--expected-sha256",hashlib.sha256(target.read_bytes()).hexdigest(),"--root",str(self.root)],capture_output=True,text=True)
        self.assertEqual(p.returncode,1); self.assertIn("inside research",p.stderr); self.assertEqual(target.read_text(),"safe\n")
    def test_doctor_rejects_malformed_index_suffix(self):
        index = self.root / "research/INDEX.md"
        index.write_text(index.read_text().replace("`SRC-0001`, `NOTE", "`SRC-0001-extra`, `NOTE"), encoding="utf-8")
        p = subprocess.run([sys.executable, str(DOCTOR), str(self.root)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertIn("malformed id SRC-0001-extra", p.stdout)
    def test_doctor_rejects_index_link_to_wrong_record_heading(self):
        index = self.root / "research/INDEX.md"
        command = [sys.executable, str(DOCTOR), str(self.root)]
        control = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(control.returncode, 0, control.stdout + control.stderr)
        # Both records are valid. Change only this source's INDEX address.
        index.write_text(index.read_text().replace('`sources/SRC-0001.md`', '`notes/NOTE-0001.md`'), encoding="utf-8")
        changed = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(changed.returncode, 1)
        self.assertIn("SRC-0001 has unresolved INDEX.md link", changed.stdout)
        self.assertNotIn("malformed id", changed.stdout)
    def test_doctor_rejects_symlinked_research_root(self):
        outside = self.root / "outside"; outside.mkdir(); (outside / "INDEX.md").write_text("# empty\n", encoding="utf-8")
        research = self.root / "research"; research.rename(self.root / "research-real"); research.symlink_to(outside, target_is_directory=True)
        p = subprocess.run([sys.executable, str(DOCTOR), str(self.root)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertIn("symlinked research path: research", p.stdout)
    def test_write_rejects_symlinked_research_root(self):
        target = self.root / "research/notes/NOTE-0001.md"; outside = self.root / "outside"; outside.mkdir()
        real = self.root / "research"; real.rename(self.root / "research-real"); real.symlink_to(self.root / "research-real", target_is_directory=True)
        target = real / "notes/NOTE-0001.md"
        p = subprocess.run([sys.executable, str(WRITE), str(target), "# replacement", "--expected-sha256", "0"*64, "--root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertIn("symlinked research path", p.stderr)
    def test_absent_research_is_supported(self):
        empty=Path(self.tmp.name)/"empty"; empty.mkdir(); p=subprocess.run([sys.executable,str(DOCTOR),str(empty)],capture_output=True,text=True); self.assertEqual(p.returncode,0); self.assertIn("SKIP research",p.stdout)

if __name__ == "__main__": unittest.main()
