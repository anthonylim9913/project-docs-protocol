import hashlib, importlib.util, os, random, re, shutil, stat, struct, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).parents[1]; CHECK = ROOT / "scripts" / "skill-registry.py"
HEADER = "| Name | Trigger | Lifecycle | Workflow stages | Inputs | Outputs/Evidence | Reviewer/Gate | Required | Location | Version | Content-ID | Missing-capability |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
def oracle_files(path):
    entries=[]
    def walk(directory):
        for child in directory.iterdir():
            relative=child.relative_to(path)
            mode=child.lstat().st_mode
            if stat.S_ISLNK(mode): raise ValueError('symlinked oracle input')
            if '__pycache__' in relative.parts or relative.name in {'.DS_Store','Thumbs.db'} or relative==Path('.git'): continue
            if stat.S_ISDIR(mode): walk(child)
            elif stat.S_ISREG(mode): entries.append((relative.as_posix().encode('utf-8','strict'),child.read_bytes()))
            else: raise ValueError('nonregular oracle input')
    walk(path)
    return sorted(entries)

def v2_stream(entries):
    framed=bytearray(b'project-docs-protocol skill-tree v2\n')
    for name,content in sorted(entries):
        framed.extend(struct.pack('>Q',len(name)))
        framed.extend(name)
        framed.extend(struct.pack('>Q',len(content)))
        framed.extend(content)
    return bytes(framed)

def digest(path):
    return hashlib.sha256(v2_stream(oracle_files(path))).hexdigest()

def legacy_digest(path):
    legacy=hashlib.sha256()
    for name,content in sorted(oracle_files(path),key=lambda entry: Path(entry[0].decode('utf-8'))):
        legacy.update(name+b'\0'+content+b'\0')
    return legacy.hexdigest()

def implementation():
    spec=importlib.util.spec_from_file_location('registry_under_test',CHECK)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
class SkillRegistryTests(unittest.TestCase):
    def run_check(self, root, *extra): return subprocess.run([sys.executable,'-B',str(CHECK),str(root),*extra],text=True,capture_output=True)
    def make_registry(self, root, location="staging/research-protocol", name="research-protocol", register="docs"):
        target=root/location; target.mkdir(parents=True); (target/"SKILL.md").write_text(f"---\nname: {name}\n---\n",encoding="utf-8")
        row=f"| `{name}` | explicit request | staged | Bootstrap, Close | records | doctor output | independent review | optional | `{location}` | 0.1.0 | sha256v2:{digest(target)} | use primary protocol |\n"
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
        self.assertIn("sha256v2:"+expected,r.stdout); self.assertIn("unreviewed",r.stdout)
    def test_digest_mode_refuses_a_missing_location(self):
        with tempfile.TemporaryDirectory() as d: r=self.run_check(Path(d),"--digest","nowhere")
        self.assertEqual(r.returncode,1); self.assertIn("not a real directory",r.stdout)
    def test_desktop_metadata_and_git_internals_do_not_make_a_skill_stale(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.make_registry(root); skill=root/"staging/research-protocol"
            (skill/".DS_Store").write_bytes(b"finder"); (skill/".git").mkdir(); (skill/".git/HEAD").write_text("ref: x\n")
            r=self.run_check(root)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_invalid_project_roots_fail_instead_of_skipping(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); regular=root/'file'; regular.write_text('not a directory')
            for target in (root/'missing',regular):
                with self.subTest(target=target.name):
                    result=self.run_check(target)
                    self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                    self.assertIn('project root',result.stdout)
    def test_existing_invalid_registry_is_not_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'docs').mkdir(); registry=root/'docs/SKILL-REGISTRY.md'
            for kind in ('dangling link','directory'):
                with self.subTest(kind=kind):
                    if kind=='dangling link': registry.symlink_to(root/'missing')
                    else: registry.mkdir()
                    result=self.run_check(root)
                    if kind=='dangling link': registry.unlink()
                    else: registry.rmdir()
                    self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                    self.assertIn('FAIL skill-registry',result.stdout)
    def test_ignored_metadata_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); skill=root/'staging/research-protocol'
            for name in ('.DS_Store','Thumbs.db','__pycache__','.git'):
                with self.subTest(name=name):
                    link=skill/name; link.symlink_to(root/'missing')
                    result=self.run_check(root)
                    self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                    self.assertIn('symlinked registry target',result.stdout)
                    link.unlink()
    def test_nested_git_contents_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); skill=root/'staging/research-protocol'
            nested=skill/'scripts/.git'; nested.mkdir(parents=True); (nested/'payload.py').write_text('changed')
            result=self.run_check(root)
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertIn('stale content-id',result.stdout)
    def test_unreadable_digest_subtree_fails_closed(self):
        if hasattr(os,'geteuid') and os.geteuid()==0: self.skipTest('permission bits do not bind the superuser')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); skill=root/'staging/research-protocol'
            locked=skill/'locked'; locked.mkdir(); (locked/'payload.py').write_text('unreviewed')
            locked.chmod(0)
            try:
                result=self.run_check(root)
                printed=self.run_check(root,'--digest','staging/research-protocol')
            finally: locked.chmod(0o755)
            for outcome in (result,printed):
                self.assertEqual(outcome.returncode,1,outcome.stdout+outcome.stderr)
                self.assertIn('FAIL skill-registry',outcome.stdout)
                self.assertNotIn('Traceback',outcome.stderr)
    def test_v2_known_answer_vector(self):
        expected='ed4b0a372f463ce0d364e2f8fb144604580c5a3893a23e3ed274113bf21ed06a'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root)
            self.assertEqual(digest(root/'staging/research-protocol'),expected)
            result=self.run_check(root,'--digest','staging/research-protocol')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('sha256v2:'+expected,result.stdout)

    def framing_pair(self,root):
        first=root/'first'; second=root/'second'
        for tree in (first,second):
            tree.mkdir(); (tree/'SKILL.md').write_bytes(b'---\nname: research-protocol\n---\n')
        (first/'a.bin').write_bytes(b'x\0b.py\0code')
        (second/'a.bin').write_bytes(b'x'); (second/'b.py').write_bytes(b'code')
        return first,second

    def test_framing_pair_has_distinct_v2_digests(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); first,second=self.framing_pair(root)
            self.assertEqual(legacy_digest(first),legacy_digest(second))
            self.assertEqual(implementation()._tree_digest(first),implementation()._tree_digest(second))
            self.assertNotEqual(digest(first),digest(second))
            outputs=[self.run_check(root,'--digest',tree.name) for tree in (first,second)]
            for tree,result in zip((first,second),outputs):
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('sha256v2:'+digest(tree),result.stdout)

    def test_framing_forgery_rejected_after_v2_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root)
            target=root/'staging/research-protocol'; registry=root/'docs/SKILL-REGISTRY.md'
            previous=digest(target); (target/'a.bin').write_bytes(b'x\0b.py\0code')
            registry.write_text(registry.read_text().replace(previous,digest(target)))
            accepted=self.run_check(root)
            self.assertEqual(accepted.returncode,0,accepted.stdout+accepted.stderr)
            before=legacy_digest(target)
            (target/'a.bin').write_bytes(b'x'); (target/'b.py').write_bytes(b'code')
            self.assertEqual(before,legacy_digest(target))
            rejected=self.run_check(root)
        self.assertEqual(rejected.returncode,1,rejected.stdout+rejected.stderr)
        self.assertIn('stale content-id',rejected.stdout)

    def test_v2_injectivity_fuzz(self):
        generator=random.Random(52); seen={}
        cases=[{}, {'a':b''}, {'a-b':b'x'}, {'a/b':b'x'}, {'a':struct.pack('>Q',1)+b'b\0'}]
        names=['a.bin','a-b','a/b','z','nested/.git/HEAD','nested/data','\u00e9','e\u0301']
        for unused in range(1995):
            cases.append({name:generator.choice([b'',b'\0',b'x\0b.py\0code',struct.pack('>Q',8),generator.randbytes(generator.randrange(32))])
                          for name in generator.sample(names,generator.randrange(len(names)+1))})
        actual_digest=implementation()._tree_digest_v2
        with tempfile.TemporaryDirectory() as directory:
            tree=Path(directory)/'tree'
            for entries in cases:
                if tree.exists(): shutil.rmtree(tree)
                tree.mkdir()
                for name,content in entries.items():
                    child=tree/name; child.parent.mkdir(parents=True,exist_ok=True); child.write_bytes(content)
                canonical=tuple(oracle_files(tree)); expected=digest(tree)
                if expected in seen: self.assertEqual(seen[expected],canonical)
                seen[expected]=canonical
                self.assertEqual(actual_digest(tree),expected)
        self.assertGreater(len(seen),1500)

    def test_path_sort_is_byte_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); tree=root/'staging/research-protocol'
            (tree/'a').mkdir(); (tree/'a/z').write_bytes(b'nested'); (tree/'a-b').write_bytes(b'flat')
            (tree/'\u00e9').write_bytes(b'utf8')
            entries=oracle_files(tree)
            self.assertEqual([name for name,content in entries],[b'SKILL.md',b'a-b',b'a/z','\u00e9'.encode()])
            result=self.run_check(root,'--digest','staging/research-protocol')
            self.assertIn('sha256v2:'+digest(tree),result.stdout)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_non_utf8_name_fails_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); tree=root/'staging/research-protocol'
            try:
                with open(os.fsencode(tree)+b'/bad-\xff','wb') as output: output.write(b'payload')
            except (OSError,UnicodeError): self.skipTest('filesystem refuses non-UTF-8 names')
            for result in (self.run_check(root),self.run_check(root,'--digest','staging/research-protocol')):
                self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertIn('FAIL skill-registry',result.stdout)
                self.assertIn('UTF-8',result.stdout)
                self.assertNotIn('Traceback',result.stderr)
                self.assertIsNone(re.search(r'[0-9a-f]{64}',result.stdout+result.stderr))

    def test_legacy_id_refused_on_active_and_staged(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); tree=root/'staging/research-protocol'
            registry=root/'docs/SKILL-REGISTRY.md'; original=registry.read_text()
            for lifecycle in ('active','staged'):
                registry.write_text(original.replace('| staged |','| '+lifecycle+' |').replace('sha256v2:'+digest(tree),'sha256:'+legacy_digest(tree)))
                result=self.run_check(root)
                self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertIn('legacy content-id: research-protocol uses the ambiguous sha256: encoding; unavailable until its reviewer gate re-passes and the owner records a sha256v2: digest',result.stdout)
                self.assertIsNone(re.search(r'[0-9a-f]{64}',result.stdout+result.stderr))

    def test_legacy_id_on_retired_row_not_compared(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); tree=root/'staging/research-protocol'
            registry=root/'docs/SKILL-REGISTRY.md'
            registry.write_text(registry.read_text().replace('| staged |','| retired |').replace('sha256v2:'+digest(tree),'sha256:'+'0'*64))
            (tree/'changed').write_bytes(b'not reviewed')
            result=self.run_check(root)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_malformed_v2_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); registry=root/'docs/SKILL-REGISTRY.md'
            original=registry.read_text(); identity='sha256v2:'+digest(root/'staging/research-protocol')
            for malformed in ('sha256v2:'+'a'*63,'sha256v2:'+'a'*65,'sha256v2:'+'A'*64,'sha256v2:'+'g'*64,'sha256v3:'+'a'*64):
                registry.write_text(original.replace(identity,malformed)); result=self.run_check(root)
                self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertIn('content-id must be sha256v2:<64 lowercase hex>',result.stdout)

    def test_v2_id_on_retired_row_not_compared(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root); registry=root/'docs/SKILL-REGISTRY.md'
            registry.write_text(registry.read_text().replace('| staged |','| retired |'))
            (root/'staging/research-protocol/changed').write_bytes(b'not reviewed')
            result=self.run_check(root)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_scope_ignores_empty_directories_and_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            tree=Path(directory); (tree/'data').write_bytes(b'content')
            original=implementation()._tree_digest_v2(tree)
            (tree/'empty').mkdir(); (tree/'data').chmod(0o755)
            self.assertEqual(implementation()._tree_digest_v2(tree),original)
            self.assertEqual(digest(tree),original)

    def test_v2_stream_keeps_unicode_normalizations_distinct(self):
        self.assertNotEqual(v2_stream([('\u00e9'.encode(),b'x')]),v2_stream([('e\u0301'.encode(),b'x')]))

    def test_digest_mode_prints_v2_and_label(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_registry(root)
            result=self.run_check(root,'--digest','staging/research-protocol')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('sha256v2:'+digest(root/'staging/research-protocol'),result.stdout)
            self.assertIn('(unreviewed: record it only after the reviewer gate passes)',result.stdout)

if __name__ == "__main__": unittest.main()
