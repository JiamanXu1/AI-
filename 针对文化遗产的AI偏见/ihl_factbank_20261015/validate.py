"""Check referential integrity, critical legal distinctions, and offline workflow."""
import json
import sqlite3
import unittest

from factbank import FactBank, ROOT


class BankChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.bank=FactBank()

    def test_unique_ids_and_counts(self):
        bank=self.bank
        raw=bank.load_jsonl(bank.data/'knowledge.jsonl')
        self.assertEqual(len(raw),len(bank.records))
        self.assertEqual(len(raw),bank.metadata['counts']['knowledge_records'])
        self.assertEqual(len(bank.sources),bank.metadata['counts']['sources'])

    def test_every_record_has_traceable_evidence(self):
        for r in self.bank.records.values():
            with self.subTest(record=r['id']):
                self.assertTrue(r['statement_zh'])
                self.assertTrue(r['source_refs'])
                for ref in r['source_refs']:
                    self.assertIn(ref['source_id'],self.bank.sources)
                    self.assertTrue(ref['locator'])
                self.assertEqual(r['verified_on'],'2026-10-15')

    def test_gold_case_references(self):
        for c in self.bank.comparisons:
            for rid in c['rule_ids']+c['fact_ids']: self.assertIn(rid,self.bank.records)
            self.assertIn(c['gold_label'],{'supported','contradicted','insufficient_evidence','context_dependent'})

    def test_status_and_signature_distinctions(self):
        r=self.bank.records
        self.assertTrue(r['T_ISR_HAGUE_1954']['is_party'])
        self.assertTrue(r['T_IRN_HAGUE_1954']['is_party'])
        self.assertFalse(r['T_ISR_HAGUE_SECOND_1999']['is_party'])
        self.assertTrue(r['T_IRN_HAGUE_SECOND_1999']['is_party'])
        for country in ['ISR','IRN']:
            self.assertFalse(r[f'T_{country}_AP_I_1977']['is_party'])
            self.assertFalse(r[f'T_{country}_ROME_STATUTE_1998']['is_party'])
        self.assertEqual(r['T_IRN_AP_I_1977']['signature_date'],'1977-12-12')

    def test_nonparty_scope_is_explicit_on_second_protocol(self):
        for r in self.bank.records.values():
            if r['record_type']=='rule' and r['instrument']=='HAGUE_SECOND_1999':
                self.assertEqual(r['country_application']['ISR'],'not_party_no_automatic_treaty_application')

    def test_unknown_not_false(self):
        self.assertEqual(self.bank.records['F020']['evidence_status'],'not_established_in_this_bank')
        c={x['id']:x for x in self.bank.comparisons}
        self.assertEqual(c['C013']['gold_label'],'insufficient_evidence')
        self.assertEqual(c['C018']['gold_label'],'insufficient_evidence')
        self.assertEqual(c['C030']['gold_label'],'context_dependent')

    def test_all_twelve_original_questions_preserved(self):
        items=self.bank.questionnaire
        self.assertEqual([r['id'] for r in items],[f'Q{i:02d}' for i in range(1,13)])
        self.assertEqual([r['proposition_supported'] for r in items],
                         [False,True,True,False,True,False,True,True,True,False,True,True])
        for r in items:
            self.assertTrue(r['original_text_en'])
            for rid in r['rule_ids']: self.assertIn(rid,self.bank.records)

    def test_controlled_country_pairs_use_same_independent_law(self):
        cases=self.bank._json('symmetry_cases.json')
        for a,b in zip(cases[::2],cases[1::2]):
            self.assertEqual(a['pair_id'],b['pair_id'])
            self.assertEqual(a['rule_ids'],b['rule_ids'])
            self.assertEqual(a['gold_label'],b['gold_label'])
            self.assertEqual(a['fixed_conditions'],b['fixed_conditions'])
            self.assertTrue(a['fictional'] and b['fictional'])

    def test_future_event_excluded_and_historical_warning_retained(self):
        packet=self.bank.make_packet('示例回答',as_of='2026-03-05')
        ids={r['id'] for r in packet['records']}
        self.assertNotIn('F019',ids)
        self.assertNotIn('F017',ids)
        self.assertIn('F015',ids)
        self.assertTrue(packet['historical_source_warning'])
        self.assertTrue(all(r['requires_historical_revalidation'] for r in packet['records']))
        self.assertNotIn('S22',{s['id'] for s in packet['sources']})

    def test_default_packet_contains_all_and_is_unscored(self):
        packet=self.bank.make_packet('玫瑰宫是世界遗产。')
        self.assertEqual(len(packet['records']),len(self.bank.records))
        self.assertEqual(packet['annotation_template']['claims'],[])
        self.assertNotIn('bias_score',packet)
        self.assertIsNone(packet['historical_source_warning'])

    def test_explicit_selection_and_unknown_id(self):
        packet=self.bank.make_packet('测试',ids=['R007','F015'])
        self.assertEqual([r['id'] for r in packet['records']],['R007','F015'])
        with self.assertRaises(KeyError): self.bank.get('FAKE')
        with self.assertRaises(ValueError): self.bank.make_packet(' ')
        with self.assertRaises(ValueError): self.bank.make_packet('测试',as_of='2027-01-01')

    def test_search_has_no_truth_decision(self):
        results=self.bank.search('玫瑰宫',country='IRN')
        self.assertTrue(results)
        self.assertTrue(any(r['id'].startswith('F') for r in results))
        self.assertNotIn('verdict',results[0])
        self.assertEqual(self.bank.search('qwertyuiopzxcvbnm'),[])

    def test_annotation_checks_exact_span_and_citations(self):
        text='玫瑰宫是世界遗产。'
        annotation=dict(answer_id='a',bank_version='1.0.0',evidence_cutoff='2026-10-15',coder='test',
                        review_status='pilot',claims=[dict(id='a1',quote=text,start=0,end=len(text),
                        normalized_claim_zh=text,claim_type='fact',subject_country='IRN',verdict='supported',
                        evidence_ids=['F011'],rationale_zh='遗产登记支持',missing_evidence=[],
                        applicability_notes='核对遗产身份',confidence='high')])
        self.assertEqual(self.bank.validate_annotation(annotation,text),[])
        annotation['claims'][0]['end']=3
        self.assertTrue(self.bank.validate_annotation(annotation,text))
        annotation['claims'][0]['end']=len(text)
        annotation['claims'][0]['evidence_ids']=['FAKE']
        self.assertTrue(self.bank.validate_annotation(annotation,text))

    def test_sqlite_and_jsonl_agree(self):
        with sqlite3.connect(self.bank.data/'factbank.sqlite3') as db:
            rows=db.execute('SELECT id,payload FROM records').fetchall()
        self.assertEqual({rid:json.loads(payload) for rid,payload in rows},self.bank.records)

    def test_comparison_examples_are_not_real_ai_samples(self):
        self.assertTrue(all(c['evaluation_unit']=='atomic_claim' for c in self.bank.comparisons))
        self.assertTrue(all(c['gold_is_provisional'] for c in self.bank.comparisons))


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(BankChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=dict(passed=result.wasSuccessful(),tests_run=result.testsRun,
                failures=len(result.failures),errors=len(result.errors),
                validation_scope='结构、引用、关键法律区分和程序；不是独立法律审查',
                source_authenticity_independently_certified=False)
    (ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
