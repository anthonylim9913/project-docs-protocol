"""Independent same-line provenance and historical-reference cases."""
import hashlib
from pathlib import Path
import unittest
import test_research_boundaries as boundaries


class ResearchProvenanceTests(unittest.TestCase):
    setUp=boundaries.ResearchBoundaryTests.setUp
    tearDown=boundaries.ResearchBoundaryTests.tearDown
    cli=boundaries.ResearchBoundaryTests.cli
    doctor=boundaries.ResearchBoundaryTests.doctor
    accepted=boundaries.ResearchBoundaryTests.accepted
    rejected=boundaries.ResearchBoundaryTests.rejected

    def source(self):return self.root/'research/sources/SRC-0001.md'

    def test_version_and_digest_alternatives(self):
        source=self.source();original=source.read_text();self.accepted(self.doctor())
        version=original.replace('Content-SHA256: '+'a'*64,'Version: edition 3')
        source.write_text(version);self.accepted(self.doctor())
        for field,value in [('Version',''),('Version',' \t'),('Content-SHA256',''),('Content-SHA256','xyz'),('Content-SHA256','a'*63)]:
            with self.subTest(field=field,value=value):
                source.write_text(version if field=='Version' else original);self.accepted(self.doctor())
                source.write_text('\n'.join(field+': '+value if line.startswith(field+':') else line for line in source.read_text().splitlines())+'\n')
                self.rejected(self.doctor(),'missing nonempty Version' if field=='Version' else 'invalid Content-SHA256')
        source.write_text(original.replace('Content-SHA256: '+'a'*64+'\n',''))
        self.rejected(self.doctor(),'missing nonempty Version or Content-SHA256')

    def test_duplicate_provenance_fields(self):
        source=self.source();original=source.read_text()
        for field,value in [('URL','https://example.test/other'),('Accessed','2026-09-22'),('Status','current'),('Content-SHA256','b'*64),('Accessibility','public')]:
            with self.subTest(field=field):
                valid=original+('Accessibility: public\n' if field=='Accessibility' else '')
                source.write_text(valid);self.accepted(self.doctor())
                source.write_text(valid+field+': '+value+'\n')
                self.rejected(self.doctor(),'duplicate field '+field.lower())

    def test_unknown_accessibility_and_type_only_downgrades(self):
        source=self.source();original=source.read_text()
        for value,diagnostic in [('public-ish','unknown Accessibility'),('','unknown Accessibility'),('private','missing nonempty Private-Reference'),('unavailable','missing nonempty Attempted-Access')]:
            with self.subTest(value=value):
                source.write_text(original);self.accepted(self.doctor())
                source.write_text(original+'Accessibility: '+value+'\n')
                self.rejected(self.doctor(),diagnostic)

    def test_private_legacy_flag_cannot_bypass_public_provenance(self):
        source=self.source();original=source.read_text()+'Private: yes\n'
        source.write_text(original);self.accepted(self.doctor())
        source.write_text(original.replace('Passage: exact text','Passage: \t'))
        self.rejected(self.doctor(),'missing nonempty Passage')

    def test_lifecycle_alternative_is_nonempty(self):
        source=self.source();original=source.read_text().replace('Status: current','Lifecycle: current')
        source.write_text(original);self.accepted(self.doctor())
        source.write_text(original.replace('Lifecycle: current','Lifecycle: \t'))
        self.rejected(self.doctor(),'missing nonempty Status or Lifecycle')

    def test_status_lifecycle_aliases_are_one_field(self):
        source=self.source();original=source.read_text();self.accepted(self.doctor())
        source.write_text(original+'Lifecycle: current\n')
        self.rejected(self.doctor(),'duplicate lifecycle field')

    def test_old_and_changed_conflicting_sources_keep_attribution(self):
        source=self.source();old=source.read_text().replace('Status: current','Status: superseded by SRC-0002')
        new=source.with_name('SRC-0002.md')
        new.write_text(source.read_text().replace('SRC-0001','SRC-0002').replace('exact text','Conflicting updated statement').replace('a'*64,'b'*64))
        source.write_text(old)
        index=self.root/'research/INDEX.md';index.write_text(index.read_text()+'- SRC-0002 — `sources/SRC-0002.md`\n')
        note=self.root/'research/notes/NOTE-0001.md'
        note.write_text(note.read_text()+'Source statement: exact text\nInference: agent interpretation, still unresolved\nContrary evidence: SRC-0002\n')
        owner=self.root/'DECISIONS.md';owner.write_text('D-0001: owner selected the original option; no revised choice supplied.\n')
        before={p:p.read_bytes() for p in self.root.rglob('*.md')}
        self.accepted(self.doctor())
        for ident,phrase in [('SRC-0001','exact text'),('SRC-0002','Conflicting updated statement')]:
            result=self.cli(boundaries.INDEX,self.root,'--id',ident);self.accepted(result);self.assertIn(phrase,result.stdout)
        self.assertEqual({p:p.read_bytes() for p in self.root.rglob('*.md')},before)
        # An attributed reference to historical evidence is valid. A missing
        # address is a mechanical failure; a stale interpretation needs review.
        note.write_text(note.read_text().replace('Contrary evidence: SRC-0002','Contrary evidence: SRC-0999'))
        self.rejected(self.doctor(),'missing references SRC-0999')
        note.write_bytes(before[note]);self.accepted(self.doctor())
        source.write_text(old.replace('superseded by SRC-0002','superseded by SRC-0001'))
        self.rejected(self.doctor(),'invalid supersession target SRC-0001')
        source.write_text(old);self.accepted(self.doctor())
        source.write_text(old.replace('superseded by SRC-0002','superseded by SRC-0999'))
        self.rejected(self.doctor(),'invalid supersession target SRC-0999')

    def test_reference_fields_cannot_borrow_next_line(self):
        for path,field in [('notes/NOTE-0001.md','Source'),('questions/RQ-0001.md','Evidence'),('synthesis/SYN-0001.md','Claim'),('synthesis/SYN-0001.md','Decision')]:
            with self.subTest(field=field):
                record=self.root/'research'/path;original=record.read_text()
                self.accepted(self.doctor())
                record.write_text('\n'.join(field+': \t' if line.startswith(field+':') else line for line in original.splitlines())+'\nFollowing: descriptive prose\n')
                self.rejected(self.doctor(),'missing nonempty '+field)
                record.write_text(original)

    def test_incomplete_and_direct_supersession_fields(self):
        source=self.source();original=source.read_text()
        for line,diagnostic in [('Status: superseded by','invalid supersession target'),('Status: correction of','invalid supersession target'),('Superseded-By: SRC-0001','invalid supersession target'),('Superseded-By: ','invalid supersession target')]:
            with self.subTest(line=line):
                source.write_text(original);self.accepted(self.doctor())
                source.write_text(original.replace('Status: current',line) if line.startswith('Status:') else original+line+'\n')
                self.rejected(self.doctor(),diagnostic)
