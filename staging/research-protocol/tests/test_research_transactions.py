"""Deterministic real-lock and interruption exercises, without production hooks."""
import contextlib
import hashlib
import importlib.util
import io
import multiprocessing
import os
from pathlib import Path
import stat
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import test_research_protocol as fixtures


def writer_module():
    sys.path.insert(0,str(fixtures.WRITE.parent))
    spec=importlib.util.spec_from_file_location('research_writer',fixtures.WRITE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def worker(target, expected, content, mode, pipe, root):
    writer=writer_module()
    actual_flock=writer.fcntl.flock
    actual_replace=writer.os.replace
    if mode=='cooperate':
        def flock(fd, operation):
            pipe.send(('opened',os.fstat(fd).st_ino))
            try:
                actual_flock(fd,operation|writer.fcntl.LOCK_NB)
                pipe.send(('unblocked',))
            except BlockingIOError:
                pipe.send(('blocked',))
            actual_flock(fd,operation)
            pipe.send(('held',os.fstat(fd).st_ino))
            assert pipe.recv()=='release'
        writer.fcntl.flock=flock
    elif mode=='lock-held':
        def flock(fd, operation):
            actual_flock(fd,operation);pipe.send(('phase',mode));pipe.recv()
        writer.fcntl.flock=flock
    else:
        def replace(*args,**kwargs):
            if mode=='post-replace': actual_replace(*args,**kwargs)
            pipe.send(('phase',mode));pipe.recv()
            if mode=='pre-replace': actual_replace(*args,**kwargs)
        writer.os.replace=replace
    result=writer.main([target,content,'--expected-sha256',expected,'--root',root])
    pipe.send(('result',result))


class ResearchTransactionTests(unittest.TestCase):
    setUp=fixtures.ResearchProtocolTests.setUp
    tearDown=fixtures.ResearchProtocolTests.tearDown

    def target(self): return self.root/'research/notes/NOTE-0001.md'

    def invoke(self, writer=None, content='complete replacement\n'):
        writer=writer or writer_module();target=self.target()
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            code=writer.main([str(target),content,'--expected-sha256',hashlib.sha256(target.read_bytes()).hexdigest(),'--root',str(self.root)])
        return code,output.getvalue()

    def valid(self):
        result=self.invoke();self.assertEqual(result[0],0,result[1])
        return self.target().read_bytes()

    def receive(self,pipe,kind):
        self.assertTrue(pipe.poll(15),'child did not reach '+kind)
        result=pipe.recv();self.assertEqual(result[0],kind,result);return result

    def spawn(self,mode,expected,content):
        ctx=multiprocessing.get_context('spawn');a,b=ctx.Pipe()
        process=ctx.Process(target=worker,args=(str(self.target()),expected,content,mode,b,str(self.root)));process.start();b.close()
        self.addCleanup(a.close)
        def cleanup():
            if process.is_alive():process.kill()
            process.join(10)
        self.addCleanup(cleanup)
        return process,a

    def test_three_overlapping_writers_share_one_lock(self):
        before=self.valid();expected=hashlib.sha256(before).hexdigest()
        a,pa=self.spawn('cooperate',expected,'generation A\n')
        inode=self.receive(pa,'opened')[1];self.receive(pa,'unblocked');self.receive(pa,'held')
        b,pb=self.spawn('cooperate',expected,'generation B\n')
        self.assertEqual(self.receive(pb,'opened')[1],inode);self.receive(pb,'blocked')
        pa.send('release');self.assertEqual(self.receive(pa,'result')[1],0);a.join(10)
        self.assertEqual(self.receive(pb,'held')[1],inode)
        c,pc=self.spawn('cooperate',expected,'generation C\n')
        self.assertEqual(self.receive(pc,'opened')[1],inode);self.receive(pc,'blocked')
        pb.send('release');self.assertEqual(self.receive(pb,'result')[1],1);b.join(10)
        self.assertEqual(self.receive(pc,'held')[1],inode)
        pc.send('release');self.assertEqual(self.receive(pc,'result')[1],1);c.join(10)
        self.assertEqual(self.target().read_text(),'generation A\n')
        self.assertEqual(self.target().with_name('.NOTE-0001.md.lock').stat().st_ino,inode)

    def test_abrupt_interruption_at_each_phase_and_retry(self):
        for phase in ('lock-held','pre-replace','post-replace'):
            with self.subTest(phase=phase):
                before=self.valid();target=self.target();lock=target.with_name('.'+target.name+'.lock');inode=lock.stat().st_ino
                process,pipe=self.spawn(phase,hashlib.sha256(before).hexdigest(),'complete next generation\n')
                self.receive(pipe,'phase');process.kill();process.join(10);self.assertFalse(process.is_alive())
                self.assertEqual(target.read_bytes(),b'complete next generation\n' if phase=='post-replace' else before)
                self.assertEqual(lock.stat().st_ino,inode)
                # Prove the OS lock is released, without a timing sleep.
                import fcntl
                with lock.open('rb') as handle:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                orphans={p.name:p.read_bytes() for p in target.parent.glob('.'+target.name+'.tmp.*')}
                result=self.invoke();self.assertEqual(result[0],0,result[1]);self.assertEqual(lock.stat().st_ino,inode)
                self.assertEqual({p.name:p.read_bytes() for p in target.parent.glob('.'+target.name+'.tmp.*')},orphans)

    def test_waiter_and_third_writer_share_generation_after_setup(self):
        before=self.valid();a,pa=self.spawn('post-replace',hashlib.sha256(before).hexdigest(),'setup generation G1\n')
        self.receive(pa,'phase')
        expected=hashlib.sha256(self.target().read_bytes()).hexdigest()
        b,pb=self.spawn('cooperate',expected,'generation G2 from B\n')
        inode=self.receive(pb,'opened')[1];self.receive(pb,'blocked')
        pa.send('release');self.assertEqual(self.receive(pa,'result')[1],0);a.join(10)
        self.assertEqual(self.receive(pb,'held')[1],inode)
        c,pc=self.spawn('cooperate',expected,'generation G2 from C\n')
        self.assertEqual(self.receive(pc,'opened')[1],inode);self.receive(pc,'blocked')
        pb.send('release');self.assertEqual(self.receive(pb,'result')[1],0);b.join(10)
        self.receive(pc,'held');pc.send('release');self.assertEqual(self.receive(pc,'result')[1],1);c.join(10)
        self.assertEqual(self.target().read_text(),'generation G2 from B\n')

    def test_failed_replacement_cleans_only_own_temp_and_retries(self):
        before=self.valid();writer=writer_module();target=self.target();lock=target.with_name('.'+target.name+'.lock');inode=lock.stat().st_ino
        orphan=target.with_name('.'+target.name+'.tmp.foreign');orphan.write_text('foreign incomplete update')
        with patch.object(writer.os,'replace',side_effect=OSError('injected replace failure')):
            code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('injected replace failure',out)
        self.assertEqual(target.read_bytes(),before);self.assertEqual(orphan.read_text(),'foreign incomplete update')
        self.assertEqual(list(target.parent.glob('.'+target.name+'.tmp.*')),[orphan])
        self.assertEqual(lock.stat().st_ino,inode);self.assertEqual(self.invoke()[0],0)

    def test_handled_interrupt_cleans_own_temp(self):
        before=self.valid();writer=writer_module();target=self.target()
        with patch.object(writer.os,'replace',side_effect=KeyboardInterrupt):code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('interrupted research write',out)
        self.assertEqual(target.read_bytes(),before);self.assertEqual(list(target.parent.glob('.*.tmp.*')),[])
        self.assertEqual(self.invoke()[0],0)

    def test_handled_interrupt_while_lock_held(self):
        before=self.valid();writer=writer_module();actual=writer.fcntl.flock
        def flock(fd,operation):
            actual(fd,operation);raise KeyboardInterrupt
        with patch.object(writer.fcntl,'flock',side_effect=flock):code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('interrupted research write',out)
        self.assertEqual(self.target().read_bytes(),before);self.assertEqual(self.invoke()[0],0)

    def test_handled_interrupt_after_replacement_retains_new_bytes(self):
        self.valid();writer=writer_module();actual=writer.os.replace
        def replace(*args,**kwargs):
            actual(*args,**kwargs);raise KeyboardInterrupt
        with patch.object(writer.os,'replace',side_effect=replace):code,out=self.invoke(writer,content='new complete bytes\n')
        self.assertEqual(code,1,out);self.assertIn('interrupted research write',out)
        self.assertEqual(self.target().read_text(),'new complete bytes\n');self.assertEqual(self.invoke()[0],0)

    def test_waiter_progresses_after_holder_is_killed(self):
        before=self.valid();a,pa=self.spawn('post-replace',hashlib.sha256(before).hexdigest(),'setup G1\n');self.receive(pa,'phase')
        expected=hashlib.sha256(self.target().read_bytes()).hexdigest();b,pb=self.spawn('cooperate',expected,'surviving writer G2\n')
        inode=self.receive(pb,'opened')[1];self.receive(pb,'blocked');a.kill();a.join(10)
        self.assertEqual(self.receive(pb,'held')[1],inode);pb.send('release');self.assertEqual(self.receive(pb,'result')[1],0);b.join(10)
        self.assertEqual(self.target().read_text(),'surviving writer G2\n')

    def test_temp_collision_never_adopts_or_cleans_foreign_entry(self):
        self.valid();writer=writer_module();target=self.target();outside=self.root/'outside';outside.write_text('foreign temp sentinel')
        with patch.object(writer.uuid,'uuid4',return_value=SimpleNamespace(hex='fixed-token')):
            self.assertEqual(self.invoke(writer)[0],0)
            name=target.with_name('.'+target.name+'.tmp.fixed-token');name.symlink_to(outside)
            before=target.read_bytes();code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('File exists',out)
        self.assertTrue(name.is_symlink());self.assertEqual(outside.read_text(),'foreign temp sentinel');self.assertEqual(target.read_bytes(),before)

    def test_existing_lock_contents_and_identity_are_retained(self):
        self.valid();lock=self.target().with_name('.NOTE-0001.md.lock');lock.write_text('stable lock marker');inode=lock.stat().st_ino
        self.assertEqual(self.invoke()[0],0)
        self.assertEqual(lock.read_text(),'stable lock marker');self.assertEqual(lock.stat().st_ino,inode)

    def test_cleanup_failure_still_releases_lock(self):
        before=self.valid();writer=writer_module();target=self.target();lock=target.with_name('.'+target.name+'.lock')
        with patch.object(writer.os,'replace',side_effect=OSError('injected replace failure')):
            code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('injected replace failure',out)
        self.assertEqual(self.invoke()[0],0)
        with patch.object(writer.os,'replace',side_effect=OSError('injected replace failure')),patch.object(writer.os,'unlink',side_effect=OSError('injected cleanup failure')):
            code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('injected cleanup failure',out)
        self.assertEqual(target.read_bytes(),before)
        import fcntl
        with lock.open('rb') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:self.fail('cleanup failure retained the cooperative lock')
        self.assertEqual(self.invoke()[0],0)

    def substitution(self,kind):
        before=self.valid();writer=writer_module();target=self.target();sync=writer.os.fsync
        substitute=None;once=[False]
        def fsync(fd):
            nonlocal substitute
            sync(fd)
            if once[0] or not stat.S_ISREG(os.fstat(fd).st_mode):return
            once[0]=True
            if kind=='target':
                target.rename(self.root/'held-target');target.write_bytes(before)
            elif kind=='temp':
                substitute=next(target.parent.glob('.'+target.name+'.tmp.*'));substitute.rename(self.root/'held-temp');substitute.write_text('foreign temp sentinel')
            elif kind=='lock':
                substitute=target.with_name('.'+target.name+'.lock');substitute.rename(self.root/'held-lock');substitute.write_text('foreign lock sentinel')
            elif kind=='parent':
                target.parent.rename(self.root/'old-parent');target.parent.mkdir()
        with patch.object(writer.os,'fsync',side_effect=fsync):code,out=self.invoke(writer,content='changed by helper\n')
        self.assertEqual(code,1,out);self.assertIn('identity changed',out)
        if kind!='parent':self.assertEqual(target.read_bytes(),before)
        else:self.assertEqual((self.root/'old-parent'/target.name).read_bytes(),before)
        if kind in ('temp','lock'):
            self.assertTrue(substitute.exists(),'foreign sidecar removed')
            self.assertEqual(substitute.read_text(),'foreign '+kind+' sentinel')
        if kind=='parent':self.assertFalse(target.exists())

    def test_replaced_target_identity(self):self.substitution('target')
    def test_replaced_temp_identity_and_cleanup(self):self.substitution('temp')
    def test_replaced_lock_identity(self):self.substitution('lock')
    def test_replaced_parent_identity(self):self.substitution('parent')

    def test_unsupported_locking_refuses_before_mutation(self):
        before=self.valid();writer=writer_module();target=self.target();files={p.name:p.read_bytes() for p in target.parent.iterdir()}
        with patch.object(writer,'fcntl',None):code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('cooperative locking unavailable',out)
        self.assertEqual({p.name:p.read_bytes() for p in target.parent.iterdir()},files)

    def test_unsupported_descriptor_capability_refuses_before_mutation(self):
        self.valid();writer=writer_module();target=self.target();files={p.name:p.read_bytes() for p in target.parent.iterdir()}
        with patch.object(os,'supports_dir_fd',set()):code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('secure descriptor operations unavailable',out)
        self.assertEqual({p.name:p.read_bytes() for p in target.parent.iterdir()},files)

    def test_hash_rechecked_immediately_before_replacement(self):
        self.valid();writer=writer_module();target=self.target();sync=os.fsync;once=[False]
        def fsync(fd):
            sync(fd)
            if not once[0] and stat.S_ISREG(os.fstat(fd).st_mode):
                once[0]=True;target.write_text('intervening edit on same inode\n')
        with patch.object(os,'fsync',side_effect=fsync):code,out=self.invoke(writer)
        self.assertEqual(code,1,out);self.assertIn('stale target hash before replacement',out)
        self.assertEqual(target.read_text(),'intervening edit on same inode\n')
        self.assertEqual(list(target.parent.glob('.*.tmp.*')),[])
        self.assertEqual(self.invoke()[0],0)

    def test_safe_reader_never_opens_linked_outside_bytes(self):
        self.valid();writer=writer_module();tree_type=writer.SafeTree
        with tree_type(self.root/'research') as tree:self.assertEqual(tree.read('notes/NOTE-0001.md'),self.target().read_bytes())
        outside=self.root/'outside';outside.write_text('OUTSIDE-READ-MARKER')
        self.target().unlink();self.target().symlink_to(outside)
        actual_read=os.read;seen=[]
        def read(fd,size):
            self.assertNotEqual((os.fstat(fd).st_dev,os.fstat(fd).st_ino),(outside.stat().st_dev,outside.stat().st_ino),'outside bytes opened')
            seen.append(fd);return actual_read(fd,size)
        with patch.object(os,'read',side_effect=read),tree_type(self.root/'research') as tree:
            with self.assertRaisesRegex(ValueError,'symlink'):tree.read('notes/NOTE-0001.md')
        self.assertEqual(seen,[])
