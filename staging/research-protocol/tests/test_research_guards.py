"""Disposable guard mutations must fail the intact valid-first regression."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import test_research_protocol as fixtures


class ResearchGuardTests(unittest.TestCase):
    def removal(self,module,test,source,needle,replacement,assertion='AssertionError: 0 != 1'):
        with tempfile.TemporaryDirectory(prefix='research guard ') as temp:
            root=Path(temp)/'research-protocol';shutil.copytree(fixtures.ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
            command=[sys.executable,'-B','-m','unittest',module+'.'+test,'-v']
            control=subprocess.run(command,cwd=root/'tests',capture_output=True,text=True,timeout=30)
            self.assertEqual(control.returncode,0,control.stdout+control.stderr)
            path=root/'scripts'/source;text=path.read_text();self.assertEqual(text.count(needle),1)
            path.write_text(text.replace(needle,replacement,1))
            mutant=subprocess.run(command,cwd=root/'tests',capture_output=True,text=True,timeout=30)
            self.assertEqual(mutant.returncode,1,mutant.stdout+mutant.stderr)
            self.assertIn(assertion,mutant.stderr)
            self.assertIn('FAILED (failures=',mutant.stderr)
            self.assertNotIn('ERROR:',mutant.stderr)

    def test_hardlink_refusal(self):
        self.removal('test_research_boundaries.ResearchBoundaryTests','test_target_hardlink',
                     'research_paths.py','if info.st_nlink != 1:','if False:')

    def test_same_line_provenance(self):
        self.removal('test_research_boundaries.ResearchBoundaryTests','test_public_required_fields_are_same_line_nonempty',
                     'research-doctor.py',"if not values.get(name.lower(), '').strip():",'if False:')

    def test_target_identity(self):
        self.removal('test_research_transactions.ResearchTransactionTests','test_replaced_target_identity',
                     'research_paths.py','if identity(actual) != identity(visible):','if False:')

    def test_stable_lock_lifetime(self):
        self.removal('test_research_transactions.ResearchTransactionTests','test_three_overlapping_writers_share_one_lock',
                     'research-write.py','            os.close(lock)','            os.close(lock)\n            os.unlink(lock_name, dir_fd=parent)',
                     assertion='AssertionError:')

    def test_owned_temp_cleanup(self):
        self.removal('test_research_transactions.ResearchTransactionTests','test_replaced_temp_identity_and_cleanup',
                     'research-write.py','if identity(visible) == identity(os.fstat(temp)):','if True:',
                     assertion='AssertionError: False is not true : foreign sidecar removed')

    def test_reserved_lock_target(self):
        self.removal('test_research_boundaries.ResearchBoundaryTests','test_reserved_helper_sidecar_is_not_a_write_target',
                     'research-write.py','if reserved_sidecar(name):','if False:')

    def test_ambiguous_id(self):
        self.removal('test_research_boundaries.ResearchBoundaryTests','test_duplicate_heading_in_one_record',

                     'research_records.py',
                     "        if ident in seen:\n            raise ValueError('duplicate id ' + ident)\n        seen.add(ident)\n    if len(declarations) > 1:",
                     "        seen.add(ident)\n    if False:")

    def test_shared_no_follow_barrier(self):
        # Both lstat and O_NOFOLLOW enforce this one policy. Removing just one
        # retains a safe refusal, so this semantic mutant disables both layers.
        with tempfile.TemporaryDirectory(prefix='research link guard ') as temp:
            root=Path(temp)/'research-protocol';shutil.copytree(fixtures.ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
            command=[sys.executable,'-B','-m','unittest','test_research_boundaries.ResearchBoundaryTests.test_retrieval_rejects_record_symlink_without_doctor','-v']
            control=subprocess.run(command,cwd=root/'tests',capture_output=True,text=True,timeout=30)
            self.assertEqual(control.returncode,0,control.stdout+control.stderr)
            path=root/'scripts/research_paths.py';text=path.read_text()
            self.assertEqual(text.count('follow_symlinks=False'),3)
            self.assertEqual(text.count('flags |= os.O_NOFOLLOW | os.O_NONBLOCK'),1)
            path.write_text(text.replace('follow_symlinks=False','follow_symlinks=True').replace('flags |= os.O_NOFOLLOW | os.O_NONBLOCK','flags |= os.O_NONBLOCK'))
            mutant=subprocess.run(command,cwd=root/'tests',capture_output=True,text=True,timeout=30)
            self.assertEqual(mutant.returncode,1,mutant.stdout+mutant.stderr)
            self.assertIn('AssertionError: 0 != 1',mutant.stderr)
            self.assertIn('GENERATED-OUTSIDE-MARKER',mutant.stderr)
            self.assertIn('FAILED (failures=1)',mutant.stderr)
            self.assertNotIn('ERROR:',mutant.stderr)

    def review_removal(self,test,source,needle,replacement,assertion='AssertionError: 0 != 1'):
        self.removal('test_research_review_repairs.ResearchReviewRepairTests',test,
                     source,needle,replacement,assertion)

    def test_newline_reserved_sidecar(self):
        self.review_removal('test_newline_target_generated_sidecars_are_reserved',
            'research_paths.py','name, re.DOTALL)', 'name)')

    def test_mode_application_after_write(self):
        self.review_removal('test_final_mode_is_applied_after_complete_content',
            'research-write.py',
            "            with os.fdopen(os.dup(temp), 'wb') as stream:\n                stream.write(content.encode('utf-8'))\n                stream.flush()\n                # Writing may clear set-ID bits. Apply and verify the complete\n                # original permission mask only after all content is flushed.\n                os.fchmod(temp, stat.S_IMODE(original.st_mode))",
            "            os.fchmod(temp, stat.S_IMODE(original.st_mode))\n            with os.fdopen(os.dup(temp), 'wb') as stream:\n                stream.write(content.encode('utf-8'))\n                stream.flush()",
            'final mode preceded complete content')

    def test_mode_verification(self):
        self.review_removal('test_failed_mode_setting_or_verification_preserves_target',
            'research-write.py','if stat.S_IMODE(os.fstat(temp).st_mode) != stat.S_IMODE(original.st_mode):','if False:')

    def test_complete_heading_token(self):
        self.review_removal('test_exact_id_rejects_period_and_unicode_suffixes',
            'research_records.py',r"return re.findall(r'(?m)^#[ \t]+([^\s—:]+)', body)",
            r"return re.findall(r'(?m)^#[ \t]+((?:SRC|NOTE|RQ|SYN)-[0-9]{4})', body)")

    def test_requested_id_validation(self):
        self.review_removal('test_requested_id_syntax_and_supported_titles',
            'research-index.py','if a.id is not None and not ID_RE.fullmatch(a.id):','if False:',
            "'requested id' not found")

    def test_research_containment(self):
        self.removal('test_research_scope.ResearchWriteScopeTests','test_docs_research_target_rejected',
            'research-write.py',"if below[:1] != ('research',) or len(below) < 2:",'if False:')

    def test_root_cwd_anchor(self):
        self.review_removal('test_single_root_relative_target_is_anchored_to_cwd',
            'research-write.py','path = Path.cwd() / path','path = path',
            'AssertionError: 1 != 0')

    def test_hidden_record_discovery(self):
        self.review_removal('test_ordinary_hidden_records_share_reader_boundary',
            'research_paths.py',"if name.endswith('.md') and not reserved_sidecar(name):",
            "if name.endswith('.md') and not name.startswith('.'):", 'AssertionError: 1 != 0')

    def test_helper_sidecars_excluded_from_records(self):
        self.review_removal('test_ordinary_hidden_records_share_reader_boundary',
            'research_paths.py',"if name.endswith('.md') and not reserved_sidecar(name):",
            "if name.endswith('.md'):", 'AssertionError: 1 != 0')

    def test_single_record_retrieval(self):
        self.review_removal('test_retrieval_refuses_distinct_record_declarations',
            'research_records.py','if len(declarations) > 1:','if False:')

    def test_index_link_matches_exact_record(self):
        self.removal('test_research_protocol.ResearchProtocolTests',
            'test_doctor_rejects_index_link_to_wrong_record_heading',
            'research-doctor.py','if declared.get(link) == ident:', 'if link in texts:')
