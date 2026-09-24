"""Synthetic histories validate classification only; these are not measured results."""
import unittest
from types import SimpleNamespace
from source.lab import Trial


def op(label, value=None, start=0, error=False):
    return dict(label=label,status='error' if error else 'ok',value={'a':value},
                invocation_ns=start,completion_ns=start+1)


def check(ops):
    t=Trial.__new__(Trial)
    t.ops,t.sessions=ops,[]
    t.key,t.scenario,t.config='synthetic','test','A'
    t.cluster=SimpleNamespace(log=SimpleNamespace(emit=lambda *a,**kw:None))
    return t.finish()['checks']


class CheckerTests(unittest.TestCase):
    def test_preserved(self):
        c=check(dict(W1=op('W1',start=0),R1=op('R1',1,2),R2=op('R2',1,4),W2=op('W2',1,6)))
        self.assertEqual(c,dict.fromkeys(['RYW','MR','MW','WFR'],False))

    def test_stale_read_is_not_write_reordering(self):
        c=check(dict(W1=op('W1',start=0),R1=op('R1',1,2),R2=op('R2',0,4),W2=op('W2',1,6)))
        self.assertEqual(c,dict(RYW=True,MR=True,MW=False,WFR=False))

    def test_first_read_stale_second_read_fresh_still_violates_ryw(self):
        c=check(dict(W1=op('W1',start=0),R1=op('R1',0,2),R2=op('R2',1,4),W2=op('W2',1,6)))
        self.assertTrue(c['RYW'])

    def test_timeout_not_violation(self):
        c=check(dict(W1=op('W1',start=0),R1=op('R1',1,2),R2=op('R2',start=4,error=True),W2=op('W2',1,6)))
        self.assertEqual(c,dict(RYW=False,MR=None,MW=False,WFR=False))

    def test_unknown_write_not_acknowledged(self):
        c=check(dict(W1=op('W1',start=0,error=True),R1=op('R1',start=2,error=True),R2=op('R2',0,4),W2=op('W2',0,6)))
        self.assertIsNone(c['RYW'])
        self.assertIsNone(c['MW'])

    def test_rollback_and_wfr_precedes_later_read(self):
        c=check(dict(W1=op('W1',start=0),R1=op('R1',1,2),W2=op('W2',0,4),R2=op('R2',0,6)))
        self.assertEqual(c,dict.fromkeys(['RYW','MR','MW','WFR'],True))

    def test_wfr_cannot_forget_earlier_read(self):
        c=check(dict(W1=op('W1',start=0),R1=op('R1',1,2),R2=op('R2',0,4),W2=op('W2',0,6)))
        self.assertTrue(c['WFR'])

    def test_no_read_before_write_inconclusive(self):
        c=check(dict(W1=op('W1',start=0),W2=op('W2',0,2),R2=op('R2',1,4)))
        self.assertIsNone(c['WFR'])


if __name__=='__main__':
    unittest.main()
