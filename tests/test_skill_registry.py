import hashlib, re, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).parents[1]; CHECK = ROOT / "scripts" / "skill-registry.py"
HEADER = "| Name | Trigger | Lifecycle | Workflow stages | Inputs | Outputs/Evidence | Reviewer/Gate | Required | Location | Version | Content-ID | Missing-capability |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
def digest(path):
    h=hashlib.sha256()
    for child in sorted(path.rglob("*")):
        rel=child.relative_to(path)
        if {"__pycache__", ".git"} & set(rel.parts) or rel.name in {".DS_Store", "Thumbs.db"}: continue
        if child.is_file():
            h.update(str(rel).encode()); h.update(b"\0"); h.update(child.read_bytes()); h.update(b"\0")
    return h.hexdigest()
class SkillRegistryTests(unittest.TestCase):
    def run_check(self, root, *extra): return subprocess.run([sys.executable,str(CHECK),str(root),*extra],text=True,capture_output=True)
    def make_registry(self, root, location="staging/research-protocol", name="research-protocol", register="docs"):
        target=root/location; target.mkdir(parents=True); (target/"SKILL.md").write_text(f"---\nname: {name}\n---\n",encoding="utf-8")
        row=f"| `{name}` | explicit request | staged | Bootstrap, Close | records | doctor output | independent review | optional | `{location}` | 0.1.0 | sha256:{digest(target)} | use primary protocol |\n"
        (root/register).mkdir(exist_ok=True); (root/register/"SKILL-REGISTRY.md").write_text(HEADER+row,encoding="utf-8")
    def test_absent_registry_is_optional(self):
        with tempfile.TemporaryDirectory() as d: r=self.run_check(Path(d))
        self.assertEqual(r.returncode,0); self.assertIn("SKIP skill-registry",r.stdout)
    def test_valid_registry_passes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.make_registry(root); r=self.run_check(root)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_stale_content_identity_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.make_registry(root); (root/"staging/research-protocol/SKILL.md").write_text("changed",encoding="utf-8"); r=self.run_check(root)
        self.assertEqual(r.returncode,1); self.assertIn("stale content-id",r.stdout)
    def test_stale_message_withholds_current_digest(self):
        # Printing the edited tree's digest would let an agent paste it into
        # the row and "re-approve" a skill no reviewer has seen.
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.make_registry(root); target=root/"staging/research-protocol"
            (target/"SKILL.md").write_text("---\nname: research-protocol\n---\nunreviewed edit\n",encoding="utf-8")
            current=digest(target); r=self.run_check(root)
        self.assertEqual(r.returncode,1,r.stdout+r.stderr)
        self.assertIn("FAIL skill-registry: line 3: stale content-id: research-protocol changed since review",r.stdout)
        self.assertIn("unavailable until its reviewer gate re-passes and the owner records the newly reviewed digest",r.stdout)
        self.assertNotIn(current,r.stdout+r.stderr)
        self.assertIsNone(re.search(r"[0-9a-f]{64}",r.stdout+r.stderr),"a digest was printed")
    def test_register_dir_selects_non_default_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.make_registry(root,register="records")
            default=self.run_check(root); relative=self.run_check(root,"--register-dir","records")
            absolute=self.run_check(root,"--register-dir",str(root/"records"))
            (root/"staging/research-protocol/SKILL.md").write_text("changed",encoding="utf-8"); stale=self.run_check(root,"--register-dir","records")
        self.assertEqual(default.returncode,0); self.assertIn("SKIP skill-registry",default.stdout)
        for r in (relative,absolute):
            self.assertEqual(r.returncode,0,r.stdout+r.stderr); self.assertIn("PASS skill-registry",r.stdout); self.assertIn("records",r.stdout)
        self.assertEqual(stale.returncode,1,stale.stdout+stale.stderr); self.assertIn("changed since review",stale.stdout)
    def test_register_dir_without_registry_is_optional(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/"records").mkdir(); r=self.run_check(root,"--register-dir","records")
        self.assertEqual(r.returncode,0,r.stdout+r.stderr); self.assertIn("SKIP skill-registry",r.stdout)
    def test_register_dir_must_exist(self):
        with tempfile.TemporaryDirectory() as d: r=self.run_check(Path(d),"--register-dir","records")
        self.assertEqual(r.returncode,1); self.assertIn("register directory not found",r.stdout)
    def test_symlink_target_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); outside=Path(d)/"outside"; outside.mkdir(); (outside/"SKILL.md").write_text("---\nname: research-protocol\n---\n"); (root/"staging").mkdir(); (root/"staging/research-protocol").symlink_to(outside, target_is_directory=True)
            (root/"docs").mkdir(); (root/"docs/SKILL-REGISTRY.md").write_text(HEADER+"| `research-protocol` | x | staged | Bootstrap | x | x | x | optional | `staging/research-protocol` | 0.1.0 | sha256:"+"0"*64+" | x |\n")
            r=self.run_check(root)
        self.assertEqual(r.returncode,1); self.assertIn("must not be a symlink",r.stdout)
    def test_missing_capability_column_is_required(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/"docs").mkdir(); (root/"docs/SKILL-REGISTRY.md").write_text("| Name | Path | Version | Status | Owner |\n| --- | --- | --- | --- | --- |\n| x | y | 1 | staged | o |\n"); r=self.run_check(root)
        self.assertEqual(r.returncode,1); self.assertIn("canonical registry header",r.stdout)
    def test_digest_mode_labels_its_output_unreviewed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.make_registry(root)
            r=self.run_check(root,"--digest","staging/research-protocol")
            expected=digest(root/"staging/research-protocol")
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn("sha256:"+expected,r.stdout); self.assertIn("unreviewed",r.stdout)
    def test_digest_mode_refuses_a_missing_location(self):
        with tempfile.TemporaryDirectory() as d: r=self.run_check(Path(d),"--digest","nowhere")
        self.assertEqual(r.returncode,1); self.assertIn("not a real directory",r.stdout)
    def test_desktop_metadata_and_git_internals_do_not_make_a_skill_stale(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.make_registry(root); skill=root/"staging/research-protocol"
            (skill/".DS_Store").write_bytes(b"finder"); (skill/".git").mkdir(); (skill/".git/HEAD").write_text("ref: x\n")
            r=self.run_check(root)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
if __name__ == "__main__": unittest.main()
