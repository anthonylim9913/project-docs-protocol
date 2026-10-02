"""R1/R4: each corruption starts from a passing complete public CLI packet."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tests.acceptance_support import copy_subject, generate, validate


class AcceptanceCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='acceptance cli ')
        cls.directory = Path(cls.temp.name)
        cls.root = cls.directory / 'subject'
        copy_subject(cls.root)
        cls.packet, cls.hashes = generate(cls.root, cls.directory)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def check(self, packet):
        return validate(self.root, self.directory, packet, self.hashes)

    def rejected(self, mutation, diagnostic):
        positive = self.check(self.packet)
        self.assertEqual(positive.returncode, 0, positive.stderr)
        changed = copy.deepcopy(self.packet)
        mutation(changed)
        result = self.check(changed)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_complete_real_cli_packet_passes(self):
        p = self.check(self.packet)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout), {'accepted': True, 'cases': 4})

    def test_reduced_positive_control(self):
        self.rejected(lambda p: p['cases'][0].update(positive_control={'passed': True}), 'positive control identity')

    def test_wrong_positive_identity(self):
        self.rejected(lambda p: p['cases'][0]['positive_control'].update(name='wrong'), 'positive control identity')

    def test_wrong_positive_exit(self):
        self.rejected(lambda p: p['cases'][0]['positive_control'].update(exit_code=99), 'positive control exit')

    def test_contradictory_protected_state(self):
        self.rejected(lambda p: p['cases'][0]['protected_state']['after'].update({'docs/STATUS.md': '0'*64}), 'protected state changed')

    def test_canonical_rejects_unauthorized_file_evidence(self):
        self.rejected(lambda p: p['cases'][0]['protected_state']['after'].update({'unexpected.txt': '0'*64}), 'unauthorized paths')

    def test_deleted_protected_path(self):
        self.rejected(lambda p: p['cases'][0]['protected_state']['after'].pop('docs/STATUS.md'), 'unauthorized paths')

    def test_empty_snapshot(self):
        self.rejected(lambda p: p['cases'][0]['protected_state'].update(before={}), 'snapshot scope')

    def test_missing_snapshot(self):
        self.rejected(lambda p: p['cases'][0]['protected_state'].pop('before'), 'snapshot schema')

    def test_wrong_snapshot_type(self):
        self.rejected(lambda p: p['cases'][0]['protected_state'].update(before=[]), 'snapshot schema')

    def test_wrong_stage_name(self):
        self.rejected(lambda p: p['cases'][0]['stages'][0].update(name='unexpected'), 'stage identity')

    def test_wrong_stage_exit(self):
        self.rejected(lambda p: p['cases'][0]['stages'][0].update(exit_code=99), 'stage exit')

    def test_forged_diagnostic_keywords(self):
        self.rejected(lambda p: p['cases'][0]['stages'][0].update(stdout='wiring-block unmapped', reason='wiring-block unmapped'), 'stage diagnostic')

    def test_missing_commands(self):
        self.rejected(lambda p: p['cases'][0].pop('commands'), 'command contract')

    def test_false_tree_digest(self):
        self.rejected(lambda p: p['source_provenance'].update(runtime_tree_sha256='0'*64), 'runtime tree digest')

    def test_duplicate_case(self):
        self.rejected(lambda p: p['cases'].__setitem__(1, copy.deepcopy(p['cases'][0])), 'duplicate case')

    def test_unknown_case(self):
        self.rejected(lambda p: p['cases'][0].update(id='unknown'), 'unexpected case')

    def test_omitted_case(self):
        self.rejected(lambda p: p['cases'].pop(), 'discovery total')

    def test_wrong_scope(self):
        self.rejected(lambda p: p.update(evidence_scope='arbitrary'), 'canonical evidence scope')

    def test_schema_downgrade(self):
        self.rejected(lambda p: p.update(schema=1), 'result schema')

    def test_boolean_case_exit(self):
        self.rejected(lambda p: p['cases'][0].update(exit_code=True), 'wrong exit')

    def test_stale_runtime_hash(self):
        self.rejected(lambda p: p['runtime_hashes'].update({'SKILL.md': '0'*64}), 'runtime hash manifest mismatch')

    def test_missing_schema(self):
        self.rejected(lambda p: p.pop('schema'), 'result schema')

    def test_missing_positive_observation(self):
        self.rejected(lambda p: p['cases'][0]['positive_control'].pop('stages'), 'stage identity')

    def test_wrong_command_role(self):
        self.rejected(lambda p: p['cases'][0]['commands'][0].append('--write'), 'command contract')

    def test_invented_positive_diagnostic(self):
        self.rejected(lambda p: p['cases'][0]['positive_control']['stages'][0].update(stdout='PASS'), 'stage diagnostic')

    def test_missing_delimiter_plan(self):
        self.rejected(lambda p: p['cases'][2]['positive_control'].pop('plan'), 'plan observation hash')

    def test_reduced_generic_control(self):
        self.rejected(lambda p: p.update(generic_control={'passed': True}), 'generic control identity')

    def test_generic_control_wrong_exit(self):
        self.rejected(lambda p: p['generic_control'].update(exit_code=99), 'generic control exit')

    def test_generic_ledger_content_mismatch(self):
        self.rejected(lambda p: p['generic_control'].update(ledger=''), 'generic ledger hash')

    def test_generic_journal_content_mismatch(self):
        self.rejected(lambda p: p['generic_control'].update(journal='{}'), 'generic journal hash')

    def test_failed_child(self):
        self.rejected(lambda p: p.update(successful=False), 'failed acceptance child')

    def test_skipped_child(self):
        self.rejected(lambda p: p.update(skips=['a required check']), 'unexpected skips')

    def test_case_assertion(self):
        self.rejected(lambda p: p['cases'][0].update(assertion='not the claim'), 'required behavioral assertion')

    def test_empty_hash_scope(self):
        self.rejected(lambda p: p.update(runtime_hashes={}), 'runtime hash manifest mismatch')

    def test_redundant_case_diagnostic(self):
        self.rejected(lambda p: p['cases'][0].update(stdout='FAIL unrelated check'), 'redundant diagnostic fields')

    def test_redundant_positive_diagnostic(self):
        self.rejected(lambda p: p['cases'][0]['positive_control'].update(stdout='FAIL wiring-block'), 'redundant diagnostic fields')

    def test_preview_success_with_failure_stderr(self):
        self.rejected(lambda p: p['cases'][2]['stages'][0].update(stderr='fatal: failed to generate plan'), 'successful migration stderr')

    def test_generic_success_with_failure_stderr(self):
        self.rejected(lambda p: p['generic_control']['stages'][1].update(stderr='fatal: write failed'), 'successful migration stderr')

    def test_opaque_record_schema(self):
        def corrupt(p):
            case = p['cases'][2]
            plan = json.loads(case['plan'])
            plan['unmapped'] = [None]
            case['plan'] = json.dumps(plan)
            # The hash is derived evidence of the one changed observation, not a second defect.
            case['protected_state']['after']['plan.json'] = hashlib.sha256(case['plan'].encode()).hexdigest()
        self.rejected(corrupt, 'plan opaque source inventory')

    @staticmethod
    def change_plan(record, mutation, generic=False):
        plan = json.loads(record['plan'])
        mutation(plan)
        record['plan'] = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
        after = record['after'] if 'after' in record else record['protected_state']['after']
        after['plan.json'] = hashlib.sha256(record['plan'].encode()).hexdigest()
        if generic:
            journal = json.loads(record['journal'])
            journal['plan_hash'] = after['plan.json']
            AcceptanceCliTests.change_journal(record, lambda j: j.update(plan_hash=after['plan.json']))

    @staticmethod
    def change_journal(record, mutation):
        journal = json.loads(record['journal'])
        mutation(journal)
        record['journal'] = json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
        record['after']['docs/.docs-migrate-journal.json'] = hashlib.sha256(record['journal'].encode()).hexdigest()

    @staticmethod
    def change_target(record, name, content):
        digest = hashlib.sha256(content.encode()).hexdigest()
        record['after']['docs/' + name] = digest
        if name == 'LEDGER.md':
            record['ledger'] = content
        AcceptanceCliTests.change_journal(record, lambda j: j['targets'][name].update(content=content, after=digest))

    def test_truncated_doctor_positive(self):
        self.rejected(lambda p: p['cases'][0]['positive_control']['stages'][0].update(stdout='PASS wiring-block\n'), 'doctor observation scope')

    def test_contradictory_doctor_summary(self):
        def corrupt(p):
            stage = p['cases'][0]['stages'][0]
            stage['stdout'] += '0 checks: 0 fail — exit 0\n'
        self.rejected(corrupt, 'doctor summary')

    def test_journal_schema_downgrade(self):
        self.rejected(lambda p: self.change_journal(p['generic_control'], lambda j: j.update(version=0)), 'generic journal schema')

    def test_existing_mapping_contradicts_inventory(self):
        self.rejected(lambda p: self.change_plan(p['generic_control'], lambda j: j['mappings'][0].update(existing=True), True), 'plan mapping state')

    def test_delimiter_mapped_row_state(self):
        self.rejected(lambda p: self.change_plan(p['cases'][2]['positive_control'], lambda j: j['mappings'][0]['row'].update(status='CLOSED')), 'plan mapping row')

    def test_ledger_row_state(self):
        self.rejected(lambda p: self.change_target(p['generic_control'], 'LEDGER.md', p['generic_control']['ledger'].replace('| OPEN |', '| CLOSED |', 1)), 'generic ledger rows')

    def test_changelog_history_erasure(self):
        self.rejected(lambda p: self.change_target(p['generic_control'], 'CHANGELOG.md', ''), 'generic changelog history')

    def test_truncated_doctor_negative(self):
        self.rejected(lambda p: p['cases'][0]['stages'][0].update(stdout='FAIL wiring-block\n'), 'doctor observation scope')

    def test_omitted_doctor_observation(self):
        def corrupt(p):
            stage=p['cases'][0]['positive_control']['stages'][0]
            stage['stdout']='\n'.join(line for line in stage['stdout'].split('\n') if not line.startswith('PASS  status-size'))
        self.rejected(corrupt, 'doctor observation scope')

    def test_duplicated_doctor_observation(self):
        def corrupt(p):
            stage=p['cases'][0]['positive_control']['stages'][0]
            stage['stdout']+='PASS  status-size 7 lines\n'
        self.rejected(corrupt, 'doctor observation scope')

    def test_contradictory_doctor_observation(self):
        def corrupt(p):
            stage=p['cases'][0]['positive_control']['stages'][0]
            stage['stdout']=stage['stdout'].replace('PASS  status-size', 'FAIL  status-size')
        self.rejected(corrupt, 'positive control diagnostic')

    def test_malformed_extra_doctor_warning(self):
        def corrupt(p):
            p['cases'][0]['stages'][0]['stdout']+='WARN status-size\n'
        self.rejected(corrupt, 'doctor line schema')

    def test_malformed_duplicate_positive_doctor_check(self):
        def corrupt(p):
            p['cases'][0]['positive_control']['stages'][0]['stdout']+='PASS status-size\n'
        self.rejected(corrupt, 'doctor line schema')

    def test_unrecognized_extra_doctor_failure(self):
        def corrupt(p):
            p['cases'][0]['stages'][0]['stdout']+='FAIL unexpected_check detected a protocol violation\n'
        self.rejected(corrupt, 'doctor line schema')

    def test_variable_doctor_info_description_remains_valid(self):
        positive=self.check(self.packet)
        self.assertEqual(positive.returncode,0,positive.stderr)
        p=copy.deepcopy(self.packet)
        stage=p['cases'][0]['stages'][0]
        lines=stage['stdout'].splitlines()
        stage['stdout']='\n'.join('INFO  changelog-entries  independently observed explanatory wording' if line.startswith('INFO  changelog-entries') else line for line in lines)+'\n'
        result=self.check(p)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_doctor_description_with_summary_words_remains_valid(self):
        positive=self.check(self.packet)
        self.assertEqual(positive.returncode,0,positive.stderr)
        p=copy.deepcopy(self.packet)
        stage=p['cases'][0]['stages'][0]
        stage['stdout']='\n'.join('INFO  changelog-entries  source checks: retained as descriptive information' if line.startswith('INFO  changelog-entries') else line for line in stage['stdout'].splitlines())+'\n'
        result=self.check(p)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_doctor_description_with_complete_summary_remains_valid(self):
        positive=self.check(self.packet)
        self.assertEqual(positive.returncode,0,positive.stderr)
        p=copy.deepcopy(self.packet)
        stage=p['cases'][0]['positive_control']['stages'][0]
        stage['stdout']='\n'.join('INFO  changelog-entries  23 checks: 17 pass, 0 warn, 0 fail, 3 info, 3 skipped — exit 0' if line.startswith('INFO  changelog-entries') else line for line in stage['stdout'].splitlines())+'\n'
        result=self.check(p)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_journal_extra_target_key(self):
        self.rejected(lambda p: self.change_journal(p['generic_control'], lambda j: j['targets']['LEDGER.md'].update(unexpected=True)), 'generic journal target schema')

    def test_wrong_doctor_summary_counts(self):
        def corrupt(p):
            stage=p['cases'][0]['stages'][0]
            stage['stdout']=stage['stdout'].replace('23 checks: 14 pass', '23 checks: 13 pass')
        self.rejected(corrupt, 'doctor summary')

    def test_indented_extra_doctor_check(self):
        def corrupt(p):
            p['cases'][0]['stages'][0]['stdout']+='  WARN  status-size extra contradictory observation\n'
        self.rejected(corrupt, 'doctor line schema')


if __name__ == '__main__':
    unittest.main()
