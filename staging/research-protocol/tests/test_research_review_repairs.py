"""Valid-first independent review regressions for the first Stage C repair."""
import hashlib
import io
import contextlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import unittest
from unittest.mock import patch
import test_research_boundaries as boundaries
import test_research_transactions as transactions


class ResearchReviewRepairTests(unittest.TestCase):
    setUp=boundaries.ResearchBoundaryTests.setUp
    tearDown=boundaries.ResearchBoundaryTests.tearDown
    cli=boundaries.ResearchBoundaryTests.cli
    doctor=boundaries.ResearchBoundaryTests.doctor
    accepted=boundaries.ResearchBoundaryTests.accepted
    rejected=boundaries.ResearchBoundaryTests.rejected
    target=boundaries.ResearchBoundaryTests.target
    write=boundaries.ResearchBoundaryTests.write

    def test_newline_target_generated_sidecars_are_reserved(self):
        ordinary=self.target().with_name('.ordinary.md');ordinary.write_text('original');self.accepted(self.write(ordinary))
        target=self.target().with_name('.ordinary\nrecord.md');target.write_text('original');self.accepted(self.write(target))
        for suffix in ('.lock','.tmp','.tmp.retained'):
            with self.subTest(suffix=suffix):
                sidecar=target.with_name('.'+target.name+suffix)
                if not sidecar.exists():sidecar.write_text('retained helper state')
                before=(sidecar.read_bytes(),sidecar.stat().st_ino)
                directory_before=set(os.listdir(sidecar.parent))
                self.rejected(self.write(sidecar),'reserved helper sidecar')
                self.assertEqual((sidecar.read_bytes(),sidecar.stat().st_ino),before)
                self.assertEqual(set(os.listdir(sidecar.parent)),directory_before)

    def test_special_permission_bits_survive_actual_cli_write(self):
        target=self.target();target.chmod(0o640);self.accepted(self.write());self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o640)
        for mode in (0o2640,0o4640,0o6640):
            with self.subTest(mode=oct(mode)):
                target.chmod(mode);self.assertEqual(stat.S_IMODE(target.stat().st_mode),mode,'fixture cannot establish requested mode')
                self.accepted(self.write());self.assertEqual(stat.S_IMODE(target.stat().st_mode),mode)

    def test_failed_mode_setting_or_verification_preserves_target(self):
        self.accepted(self.write());target=self.target();target.chmod(0o640)
        lock=target.with_name('.'+target.name+'.lock')
        before=(target.read_bytes(),target.stat().st_mode,target.stat().st_ino,lock.stat().st_ino);writer=transactions.writer_module()
        for action,diagnostic in [('error','mode setting failed'),('no-op','permission bits')]:
            with self.subTest(action=action):
                output=io.StringIO()
                kwargs={'side_effect':OSError('mode setting failed')} if action=='error' else {'return_value':None}
                with patch.object(writer.os,'fchmod',**kwargs),contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
                    result=writer.main([str(target),'changed bytes','--expected-sha256',hashlib.sha256(target.read_bytes()).hexdigest(),'--root',str(self.root)])
                self.assertEqual(result,1,output.getvalue());self.assertIn(diagnostic,output.getvalue())
                self.assertEqual((target.read_bytes(),target.stat().st_mode,target.stat().st_ino,lock.stat().st_ino),before)
                self.assertEqual(list(target.parent.glob('.'+target.name+'.tmp.*')),[])
        self.accepted(self.write())

    def test_exact_id_rejects_period_and_unicode_suffixes(self):
        source=self.root/'research/sources/SRC-0001.md';original=source.read_text()
        for suffix in ('.extra','é'):
            with self.subTest(suffix=suffix):
                source.write_text(original);self.accepted(self.doctor());self.accepted(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'))
                source.write_text(original.replace('# SRC-0001 ', '# SRC-0001'+suffix+' '))
                self.rejected(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'),'id not found')
                self.rejected(self.doctor(),'malformed id SRC-0001'+suffix)

    def test_requested_id_syntax_and_supported_titles(self):
        source=self.root/'research/sources/SRC-0001.md';original=source.read_text()
        for heading in ('# SRC-0001 — primary','# SRC-0001: primary','# SRC-0001 primary','# SRC-0001'):
            with self.subTest(heading=heading):
                source.write_text(heading+'\n'+'\n'.join(original.splitlines()[1:])+'\n')
                self.accepted(self.doctor());self.accepted(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'))
        for query in ('SRC-0001.extra','SRC-0001é','SRC-001','SRC-0001 ',''):
            with self.subTest(query=query):
                self.rejected(self.cli(boundaries.INDEX,self.root,'--id',query),'requested id')

    def test_ordinary_hidden_records_share_reader_boundary(self):
        self.accepted(self.doctor());self.accepted(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'))
        source=self.root/'research/sources/SRC-0001.md';hidden=source.with_name('.ordinary-source.md');source.rename(hidden)
        index=self.root/'research/INDEX.md';index.write_text(index.read_text().replace('sources/SRC-0001.md','sources/.ordinary-source.md'))
        self.accepted(self.doctor());self.accepted(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'))
        # Actual helper metadata may contain Markdown-looking bytes without
        # becoming another record. It still passes file safety checks.
        for suffix in ('.lock','.tmp','.tmp.retained.md'):
            sidecar=hidden.with_name('.'+hidden.name+suffix);sidecar.write_text(hidden.read_text())
        self.accepted(self.doctor());self.accepted(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'))
        self.accepted(self.write(hidden,content=hidden.read_text()))

    def merged_record_fixture(self):
        # The index supports both locations before the only conceptual change:
        # relocating an intact NOTE declaration into the SRC file. References
        # and provenance remain valid under the old ambiguous file model.
        source=self.root/'research/sources/SRC-0001.md';note=self.target()
        index=self.root/'research/INDEX.md'
        index.write_text(index.read_text().replace('- NOTE-0001 — `notes/NOTE-0001.md`',
            '- NOTE-0001 — `notes/NOTE-0001.md` `sources/SRC-0001.md`'))
        self.accepted(self.doctor());self.accepted(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'))
        source.write_text(source.read_text()+'\n'+note.read_text())
        note.write_text('# Notes overview\n')
    def test_distinct_record_declarations_cannot_share_provenance(self):
        self.merged_record_fixture()
        self.rejected(self.doctor(),'multiple record declarations')

    def test_retrieval_refuses_distinct_record_declarations(self):
        self.merged_record_fixture()
        self.rejected(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'),'multiple record declarations')

    def test_nested_research_folder_is_judged_from_the_selected_root(self):
        # The root is explicit (default: cwd), so a nested folder named
        # research/ is an ordinary subfolder of <root>/research/, and running
        # from inside research/ without --root selects the wrong project.
        outer=self.root/'research'
        for form in ('relative-outer','relative-inner'):
            with self.subTest(form=form):
                self.accepted(self.write())
                inner=outer/form/'research';inner.mkdir(parents=True)
                target=inner/'record.md';target.write_text('nested original')
                before=target.read_bytes();expected=hashlib.sha256(before).hexdigest()
                spelling,cwd={'relative-outer':(form+'/research/record.md',outer),
                    'relative-inner':('record.md',inner)}[form]
                result=subprocess.run([sys.executable,'-B',str(boundaries.WRITE),spelling,'changed','--expected-sha256',expected],cwd=cwd,capture_output=True,text=True,timeout=10)
                self.rejected(result,'inside research/');self.assertEqual(target.read_bytes(),before)
                self.assertEqual(sorted(p.name for p in inner.iterdir()),['record.md'])
        target=outer/'absolute/research/record.md';target.parent.mkdir(parents=True);target.write_text('nested original')
        self.accepted(self.write(target,content='nested changed'));self.assertEqual(target.read_text(),'nested changed')

    def test_link_between_research_roots_does_not_promote_trusted_parent(self):
        self.accepted(self.write());outer=self.root/'research';outside=self.root/'outside';inner=outside/'research';inner.mkdir(parents=True)
        target=inner/'record.md';target.write_text('OUTSIDE-BOUNDARY-MARKER');(outer/'nested').symlink_to(outside,target_is_directory=True)
        spelling=outer/'nested/research/record.md';expected=hashlib.sha256(target.read_bytes()).hexdigest()
        before=target.read_bytes();result=self.write(spelling,expected)
        self.rejected(result,'symlinked research path: nested');self.assertEqual(target.read_bytes(),before)
        self.assertNotIn('OUTSIDE-BOUNDARY-MARKER',result.stdout+result.stderr)
        self.assertEqual(sorted(p.name for p in inner.iterdir()),['record.md'])

    def test_final_mode_is_applied_after_complete_content(self):
        # Call-through observation is portable even on root-run filesystems
        # that do not clear set-ID bits on writes. Actual CLI modes are above.
        self.accepted(self.write());writer=transactions.writer_module()
        target=self.target();target.chmod(0o640);content='complete é replacement\n'
        original=writer.os.fchmod;observed=[]
        def observe(fd,mode):
            observed.append((os.fstat(fd).st_size,mode))
            return original(fd,mode)
        with patch.object(writer.os,'fchmod',side_effect=observe):
            result=writer.main([str(target),content,'--expected-sha256',hashlib.sha256(target.read_bytes()).hexdigest(),'--root',str(self.root)])
        self.assertEqual(result,0)
        self.assertEqual(observed,[(len(content.encode('utf-8')),0o640)],'final mode preceded complete content')
        self.assertEqual(target.read_text(),content)

    def test_nested_boundary_refusal_never_opens_outside_inode(self):
        writer=transactions.writer_module();real_open=writer.os.open;opened=[]
        def observe(*args,**kwargs):
            fd=real_open(*args,**kwargs);info=os.fstat(fd)
            opened.append((info.st_dev,info.st_ino));return fd
        target=self.target();identity=lambda p:(p.stat().st_dev,p.stat().st_ino)
        target_id=identity(target)
        with patch.object(writer.os,'open',side_effect=observe),patch.object(writer.os,'supports_dir_fd',set(writer.os.supports_dir_fd)|{writer.os.open}):
            self.assertEqual(writer.main([str(target),'control','--expected-sha256',hashlib.sha256(target.read_bytes()).hexdigest(),'--root',str(self.root)]),0)
        self.assertIn(target_id,opened,'I/O witness missed valid target open')
        outside=self.root/'outside/research';outside.mkdir(parents=True)
        sentinel=outside/'record.md';sentinel.write_text('outside sentinel')
        (self.root/'research/nested').symlink_to(outside.parent,target_is_directory=True)
        opened.clear();before=(sentinel.read_bytes(),identity(sentinel))
        output=io.StringIO()
        with patch.object(writer.os,'open',side_effect=observe),patch.object(writer.os,'supports_dir_fd',set(writer.os.supports_dir_fd)|{writer.os.open}),contextlib.redirect_stderr(output):
            result=writer.main([str(self.root/'research/nested/research/record.md'),'changed','--expected-sha256',hashlib.sha256(before[0]).hexdigest(),'--root',str(self.root)])
        self.assertEqual(result,1);self.assertIn('symlinked research path: nested',output.getvalue())
        self.assertNotIn(before[1],opened,'outside inode opened')
        self.assertEqual((sentinel.read_bytes(),identity(sentinel)),before)

    def test_single_root_relative_target_is_anchored_to_cwd(self):
        self.accepted(self.write());target=self.target()
        result=subprocess.run([sys.executable,'-B',str(boundaries.WRITE),target.name,'relative content','--expected-sha256',hashlib.sha256(target.read_bytes()).hexdigest(),'--root',str(self.root)],cwd=target.parent,capture_output=True,text=True,timeout=10)
        self.accepted(result);self.assertEqual(target.read_text(),'relative content')

    def test_diagnostic_retrieval_and_normal_sections_remain_supported(self):
        source=self.root/'research/sources/SRC-0001.md'
        source.write_text(source.read_text()+'\n## Analysis\nA normal section.\n')
        self.accepted(self.doctor());self.accepted(self.cli(boundaries.INDEX,self.root,'--id','SRC-0001'))
        source.write_text(source.read_text().replace('URL: https://example.test/source','URL:'))
        self.rejected(self.doctor(),'missing nonempty URL')
        result=self.cli(boundaries.INDEX,self.root,'--id','SRC-0001')
        self.accepted(result);self.assertIn('## Analysis',result.stdout)
