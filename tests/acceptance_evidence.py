"""Schema-2 canonical observations. Expectations come from reviewed inputs.

These checks establish packet consistency and byte identity, not that a process
really ran or that an independent person reviewed it. Retain raw executions and
independent review outside the behavior manifest for those separate claims.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

try:
    from input_manifest import hashes, required_paths, tree_hash, valid_path, dirty_inputs
except ModuleNotFoundError:
    from tests.input_manifest import hashes, required_paths, tree_hash, valid_path, dirty_inputs

ROOT = Path(__file__).resolve().parents[1]
HASH = re.compile(r'[0-9a-f]{64}')


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def require(ok, diagnostic):
    if not ok:
        raise ValueError(diagnostic)


def load_json(text):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            require(k not in result, 'duplicate JSON key: ' + k)
            result[k] = v
        return result
    return json.loads(text, object_pairs_hook=unique)


def hash_map(value, diagnostic):
    require(isinstance(value, dict) and all(valid_path(k) and isinstance(v, str) and HASH.fullmatch(v)
                                           for k, v in value.items()), diagnostic)


def initial_snapshot(fixture=None, wiring=None):
    # Literal seed contract, independent of the runner's seed_register function.
    texts = {
        'docs/README.md': '*Installed via the `project-docs-protocol` skill.*\n',
        'docs/STATUS.md': '# STATUS\n\nLast updated: 2026-09-14\n\n## Current phase\n\nFixture review.\n',
        'docs/CHANGELOG.md': '# CHANGELOG\n\n## 2026-09-14 — initialized project documentation system\n\nInstalled.\n',
        'docs/DECISIONS.md': '# DECISIONS\n',
    }
    if fixture:
        texts['docs/STATUS.md'] = (ROOT / fixture).read_text(encoding='utf-8')
    if wiring:
        texts['AGENTS.md'] = (ROOT / wiring).read_text(encoding='utf-8')
    return {k: sha(v) for k, v in texts.items()}


def snapshots(record, expected, additions=(), mutable=()):
    before, after = record.get('before'), record.get('after')
    hash_map(before, 'snapshot schema: before')
    hash_map(after, 'snapshot schema: after')
    require(set(before) == set(expected), 'snapshot scope: before')
    require(before == expected, 'snapshot input hashes')
    require(set(after) == set(before) | set(additions), 'unauthorized paths in after snapshot')
    require(all(after[k] == v for k, v in before.items() if k not in mutable), 'protected state changed')
    return before, after


def stages(record, expected, root, interpreter, today):
    require('stdout' not in record and 'stderr' not in record, 'redundant diagnostic fields are forbidden')
    actual = record.get('stages')
    require(isinstance(actual, list) and len(actual) == len(expected), 'stage identity/count')
    for item, (name, code) in zip(actual, expected):
        require(isinstance(item, dict) and item.get('name') == name, 'stage identity')
        require(type(item.get('exit_code')) is int and item['exit_code'] == code, 'stage exit')
        require(isinstance(item.get('stdout'), str) and isinstance(item.get('stderr'), str), 'stage diagnostic schema')
    project = record.get('project')
    require(isinstance(project, str) and Path(project).is_absolute(), 'command contract: project')
    commands = []
    for name, code in expected:
        script = 'docs-doctor.py' if name == 'doctor' else 'docs-migrate.py'
        cmd = [interpreter, '-B', str(root / 'scripts' / script), project]
        if name == 'doctor':
            cmd += ['--today', today, '--no-git']
        else:
            cmd += ['--register-dir', 'docs', '--plan', str(Path(project) / 'plan.json'), '--today', today]
            if name == 'write':
                cmd += ['--write']
        commands.append(cmd)
    require(record.get('commands') == commands, 'command contract: argv')
    return actual


def doctor_diagnostic(stage, status):
    matches = re.findall(r'^\s*(PASS|FAIL|WARN|INFO|SKIP)\s+wiring-block(?:\s|$)', stage['stdout'], re.M)
    require(matches == [status] and not stage['stderr'], 'stage diagnostic: wiring-block=' + status)
    if status == 'PASS':
        require(not re.search(r'^\s*(FAIL|WARN)\s+', stage['stdout'], re.M), 'positive control diagnostic')

    expected = {
        'wiring-block': status, 'wiring-clauses': 'PASS' if status == 'PASS' else 'SKIP',
        'wiring-path': 'PASS' if status == 'PASS' else 'SKIP', 'readme-footer': 'PASS',
        'changelog-entries': 'INFO', 'changelog-dormancy': 'PASS', 'changelog-order': 'PASS',
        'changelog-heading-format': 'PASS', 'changelog-decision-refs': 'SKIP',
        'status-size': 'PASS', 'status-longest-line': 'PASS', 'status-headings': 'PASS',
        'status-session-stack': 'PASS', 'status-last-updated': 'PASS', 'status-past-tense': 'PASS',
        'status-template-residue': 'PASS', 'decisions-ids': 'INFO', 'decisions-template-residue': 'PASS',
        'brand-placeholders': 'INFO', 'nested-register': 'PASS', 'sibling-register': 'PASS',
        'ledger': 'SKIP', 'git-status-churn': 'SKIP'}
    observations = re.findall(r'^(PASS|FAIL|WARN|INFO|SKIP)[ \t]+([a-z][a-z-]+)[ \t]+(.+)$', stage['stdout'], re.M)
    require(len(observations) == len(expected) and {name: value for value, name, _ in observations} == expected,
            'doctor observation scope')
    counts = [sum(value == tag for value in expected.values()) for tag in ('PASS', 'WARN', 'FAIL', 'INFO', 'SKIP')]
    summary = '%d checks: %d pass, %d warn, %d fail, %d info, %d skipped — exit %d' % tuple([len(expected)] + counts + [stage['exit_code']])
    summaries = [line for line in stage['stdout'].splitlines() if re.match(r'^[0-9]+ checks:', line)]
    require(summaries == [summary], 'doctor summary does not match observations')
    require(re.match(r'^docs-doctor [0-9.]+ — register at docs/ \(relative to the project root\), today 2026-09-14\n', stage['stdout']),
            'doctor observation header')

    lines = [line for line in stage['stdout'].splitlines() if line.strip()]
    scope_notice = ('Scope: Structural health does not establish semantic accuracy, independent verification, '
                    'product acceptance, historical byte integrity or actual write order. A link/hash cannot '
                    'prove an observation happened; a final diff cannot prove write order.')
    # Account for every nonblank line. A regex search must not silently discard
    # malformed/unknown diagnostic rows or appended contradictory prose.
    complete_lines = (len(lines) == len(expected) + 3 and
                      re.fullmatch(r'[0-9]+ checks: [0-9]+ pass, [0-9]+ warn, [0-9]+ fail, [0-9]+ info, [0-9]+ skipped — exit [0-9]+', lines[-2])
                      and lines[-1] == scope_notice
                      and all(re.fullmatch(r'(PASS|FAIL|WARN|INFO|SKIP)[ \t]+[a-z][a-z-]+[ \t]+.+', line)
                              for line in lines[1:-2]))
    require(complete_lines, 'doctor line schema: unmatched or misplaced nonblank line')


def source_record(text, section, line, kind):
    # Public identity encoding; the bounded fixture inventories below are hand-authored.
    return {'key': sha('STATUS.md\n' + section + '\n' + text + '\n1'), 'path': 'STATUS.md',
            'section': section, 'line': line, 'text': text, 'kind': kind, 'status': '', 'blocked_on': ''}


def expected_inventory(record):
    name = record.get('id', record.get('name'))
    if name == 'migration-20-safe-write':
        return [source_record('- anonymised finding %02d' % i, 'in flight', i + 6, 'list')
                for i in range(1, 21)], []
    cdata = name.endswith('cdata')
    opening = '<![CDATA[' if cdata else '<?audit'
    if name.startswith('migration-split-'):
        closing = ']]\n>' if cdata else '?\n>'
        text = opening + '\n## Findings\n- Hidden\n' + closing + '\n\n- Actual finding.'
        return [], [source_record(text, 'findings', 5, 'unmapped')]
    closing = ']]>' if cdata else '?>'
    return [source_record('- Actual finding.', 'findings', 12, 'list')], [
        source_record(opening + '\n## Findings\n- Hidden\n' + closing, 'findings', 7, 'unmapped')]


def migration_diagnostics(record, counts, mapped, unmapped):
    lines = ['Selected register: ' + str((Path(record['project'])/'docs').resolve()),
             'before live STATUS findings: ' + str(counts['source_records']),
             'after proposed live ledger rows: ' + str(counts['new_rows'])]
    lines += ['LG-%04d\tSTATUS: %s [needs review]' % (i, source['text']) for i, source in enumerate(mapped, 1)]
    lines += ['unmapped: STATUS:%d: %s' % (s['line'], s['text']) for s in unmapped]
    for stage in record['stages']:
        expected = lines[:]
        if stage['name'] == 'preview':
            expected.append('Preview only. Review all new rows and unresolved records before --write --plan PATH.')
        elif stage['exit_code'] == 0:
            expected.append('Reviewed migration applied; repeat the same command to verify/replay. STATUS.md preserved.')
        require(stage['stdout'] == '\n'.join(expected) + '\n', 'stage diagnostic: migration observations')
        if stage['exit_code'] == 0:
            require(stage['stderr'] == '', 'stage diagnostic: successful migration stderr')


def plan_observation(record, expected_counts, titles, before, after, today):
    raw = record.get('plan')
    require(isinstance(raw, str) and sha(raw) == after.get('plan.json'), 'plan observation hash')
    plan = load_json(raw)
    require(isinstance(plan, dict) and type(plan.get('version')) is int and plan['version'] == 1,
            'plan observation schema')
    counts = plan.get('counts')
    require(isinstance(counts, dict) and counts == expected_counts and all(type(n) is int for n in counts.values()),
            'plan inventory')
    require(plan.get('date') == today and plan.get('register_dir') == str((Path(record['project']) / 'docs').resolve()),
            'plan provenance')
    expected_inputs = {Path(k).name: v for k, v in before.items()}
    expected_inputs.update({'LEDGER.md': None, 'LEDGER-ARCHIVE.md': None})
    require(plan.get('inputs') == expected_inputs, 'plan input hashes')
    mappings, unmapped = plan.get('mappings'), plan.get('unmapped')
    require(isinstance(mappings, list) and isinstance(unmapped, list) and
            len(mappings) == counts['mapped_records'] and len(unmapped) == counts['unmapped_records'], 'plan records')
    require(all(isinstance(m, dict) and isinstance(m.get('row'), dict) for m in mappings), 'plan mapping schema')
    require([m['row'].get('title') for m in mappings] == titles, 'plan mapped titles')
    require([m.get('id') for m in mappings] == ['LG-%04d' % i for i in range(1, len(titles) + 1)], 'plan mapped IDs')
    generic = record.get('name') == 'migration-20-safe-write'
    for mapping, title in zip(mappings, titles):
        require(mapping.get('existing') is False and mapping.get('reviewed') is generic, 'plan mapping state')
        row = {'priority': 'P2', 'status': 'OPEN', 'date': today, 'title': title, 'tags': '',
               'closes_when': 'Acceptance positive control is reviewed.' if generic else '',
               'blocked_on': '', 'touches': 'STATUS.md', 'evidence': ''}
        require(mapping['row'] == row, 'plan mapping row')
    mapped_sources, opaque_sources = expected_inventory(record)
    require([m.get('source') for m in mappings] == mapped_sources, 'plan mapped source inventory')
    expected_unmapped = [{'source': source, 'existing': False, 'disposition': '', 'reason': '', 'maps_to': ''}
                        for source in opaque_sources]
    require(unmapped == expected_unmapped, 'plan opaque source inventory')
    migration_diagnostics(record, counts, mapped_sources, opaque_sources)
    return plan


def validate_canonical(result, expected_cases):
    require(type(result.get('schema')) is int and result['schema'] == 2, 'result schema must be 2')
    contract = load_json((ROOT / 'tests/fixtures/acceptance-v2/contract.json').read_text())
    require(result.get('evidence_scope') == contract['scope'], 'canonical evidence scope is missing or untrusted')
    require(set(expected_cases) == set(contract['cases']), 'canonical case contract scope')
    root_value = result.get('runtime_root')
    require(isinstance(root_value, str) and Path(root_value).is_absolute(), 'runtime root provenance')
    root = Path(root_value).resolve()
    require(root == ROOT, 'runtime root must be the validator subject checkout')
    expected_paths = required_paths(ROOT)
    values = result['runtime_hashes']
    hash_map(values, 'runtime hashes schema')
    require(set(values) == expected_paths, 'runtime hash manifest scope is incomplete or unexpected')
    require(values == hashes(ROOT), 'runtime input hash mismatch')
    provenance = result.get('source_provenance')
    require(isinstance(provenance, dict), 'source provenance schema')
    require(provenance.get('runtime_tree_sha256') == tree_hash(values), 'runtime tree digest mismatch')
    source = result.get('source_commit')
    require(isinstance(source, str) and re.fullmatch('[0-9a-f]{40}', source), 'source commit provenance')
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'], text=True).strip()
    require(head == source and not dirty_inputs(root), 'source commit does not match a clean reviewed runtime')
    require(provenance.get('verified') is True and provenance.get('dirty') is False and
            provenance.get('git_head') == source and provenance.get('source_commit_argument') == source,
            'strict canonical runtime provenance is unverified')
    interpreter = result.get('interpreter')
    require(isinstance(interpreter, str) and Path(interpreter).is_absolute(), 'command contract: interpreter')
    today = contract['today']
    common_counts = {'existing_rows': 0, 'source_records': 1, 'mapped_records': 0, 'new_rows': 0, 'unmapped_records': 1}
    bundle = 'tests/fixtures/hardening-2026-09-12/cases/'
    for case in result['cases']:
        ident = case['id']
        rule = contract['cases'][ident]
        observed = stages(case, rule['stages'], root, interpreter, today)
        state = case.get('protected_state')
        require(isinstance(state, dict), 'snapshot schema: protected_state')
        is_doctor = ident.startswith('doctor-')
        initial = initial_snapshot(wiring=bundle + ident + '.md') if is_doctor else initial_snapshot(fixture=bundle + ident + '.md')
        before, after = snapshots(state, initial, rule['allowed_additions'])
        require(state.get('unchanged') is True and state.get('unauthorized_files') == [], 'protected state claims contradict snapshots')
        require(case.get('runtime_hashes') == values, 'case runtime hash manifest mismatch')
        if is_doctor:
            doctor_diagnostic(observed[0], 'FAIL')
            require(case.get('plan') is None, 'unexpected doctor plan')
        else:
            require(observed[1]['stderr'].strip() == contract['refusal'], 'stage diagnostic: migration refusal')
            plan_observation(case, common_counts, [], before, after, today)
        positive = case.get('positive_control')
        require(isinstance(positive, dict) and positive.get('name') == rule['positive'], 'positive control identity')
        require(type(positive.get('exit_code')) is int and positive['exit_code'] == 0, 'positive control exit')
        require(positive.get('passed') is True, 'positive control passed flag')
        pos_stages = stages(positive, rule['positive_stages'], root, interpreter, today)
        if is_doctor:
            doctor_diagnostic(pos_stages[0], 'PASS')
            snapshots(positive, initial_snapshot(wiring=bundle + rule['positive'] + '.md'))
        else:
            positive_initial = initial_snapshot(fixture='tests/fixtures/acceptance-v2/' + rule['positive_fixture'])
            b, a = snapshots(positive, positive_initial, ['plan.json'])
            counts = dict(common_counts, source_records=2, mapped_records=1, new_rows=1)
            plan_observation(positive, counts, ['Actual finding.'], b, a, today)
    generic = result.get('generic_control')
    rule = contract['generic_control']
    require(isinstance(generic, dict) and generic.get('name') == rule['name'], 'generic control identity')
    require(type(generic.get('exit_code')) is int and generic['exit_code'] == 0 and generic.get('passed') is True, 'generic control exit')
    stages(generic, rule['stages'], root, interpreter, today)
    b, a = snapshots(generic, initial_snapshot(fixture='tests/fixtures/migration-20/STATUS.md'),
                     ['plan.json', 'docs/LEDGER.md', 'docs/LEDGER-ARCHIVE.md', 'docs/.docs-migrate-journal.json'], ['docs/CHANGELOG.md'])
    counts = dict(common_counts, source_records=20, mapped_records=20, new_rows=20, unmapped_records=0)
    titles = ['anonymised finding %02d' % i for i in range(1, 21)]
    plan = plan_observation(generic, counts, titles, b, a, today)
    require(all(m.get('reviewed') is True and m['row'].get('closes_when') == 'Acceptance positive control is reviewed.'
                for m in plan['mappings']), 'generic control review observations')
    ledger = generic.get('ledger')
    require(isinstance(ledger, str) and sha(ledger) == a['docs/LEDGER.md'], 'generic ledger hash')
    rows = [line for line in ledger.splitlines() if re.match(r'^\| LG-\d{4} \|', line)]
    sources, _ = expected_inventory(generic)
    expected_rows = ['| LG-%04d | P2 | OPEN | 2026-09-14 | %s |  | Acceptance positive control is reviewed. |  | STATUS.md | migration:STATUS.md#%s |'
                     % (i, titles[i-1], sources[i-1]['key']) for i in range(1, 21)]
    require(rows == expected_rows, 'generic ledger rows')

    journal_raw = generic.get('journal')
    require(isinstance(journal_raw, str) and sha(journal_raw) == a['docs/.docs-migrate-journal.json'], 'generic journal hash')
    journal = load_json(journal_raw)
    require(isinstance(journal, dict) and type(journal.get('version')) is int and journal['version'] == 1 and
            set(journal) == {'version', 'state', 'plan_hash', 'inputs', 'order', 'targets'}, 'generic journal schema')
    require(journal.get('state') == 'complete' and journal.get('plan_hash') == sha(generic['plan']),
            'generic journal completion')
    require(journal.get('order') == ['CHANGELOG.md', 'LEDGER-ARCHIVE.md', 'LEDGER.md'], 'generic journal order')
    require(journal.get('inputs') == plan['inputs'], 'generic journal inputs')
    targets = journal.get('targets')
    require(isinstance(targets, dict) and set(targets) == {'CHANGELOG.md', 'LEDGER-ARCHIVE.md', 'LEDGER.md'}, 'generic journal targets')
    for name, target in targets.items():
        require(isinstance(target, dict) and set(target) == {'content', 'after'}, 'generic journal target schema')
        require(isinstance(target, dict) and isinstance(target.get('content'), str) and
                target.get('after') == sha(target['content']) == a['docs/' + name], 'generic journal content')

    changelog = targets['CHANGELOG.md']['content']
    original = '# CHANGELOG\n\n## 2026-09-14 — initialized project documentation system\n\nInstalled.\n'
    require(changelog.endswith(original), 'generic changelog history')
    expected_log = ['## 2026-09-14 — reviewed STATUS-to-LEDGER migration', '',
                    'Migration ' + sha(generic['plan']) + '; before source records: 20; existing live rows: 0; new rows: 20; after live rows: 20.',
                    'STATUS.md is preserved until the dashboard adoption is separately reconciled.', '', 'Reviewed source-to-ID mapping:']
    expected_log += ['- STATUS.md:%d (%s) → LG-%04d: %s' % (source['line'], source['key'], i, source['text'])
                     for i, source in enumerate(sources, 1)]
    require(changelog == '\n'.join(expected_log) + '\n\n' + original, 'generic changelog mapping')

    table_header = '| ID | P | Status | Date | Title | Tags | Closes-when | Blocked-on | Touches | Evidence |\n|---|---|---|---|---|---|---|---|---|---|\n'
    require(targets['LEDGER-ARCHIVE.md']['content'] == table_header, 'generic archive contents')
    template = (ROOT/'templates/LEDGER.md').read_text()
    original_template = '\n'.join(line for line in template.splitlines() if not line.startswith('| LG-0001 |')) + '\n'
    preserved_ledger = '\n'.join(line for line in ledger.splitlines() if line not in rows) + '\n'
    require(preserved_ledger == original_template, 'generic ledger template preservation')
