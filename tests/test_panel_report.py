import unittest
from evals import panel_report as report

class ReportTests(unittest.TestCase):
    def assert_summary_equal(self, actual, expected):
        # Python 3.12 changed float summation; receipts and integer counts remain exact.
        if isinstance(expected, dict):
            self.assertEqual(set(actual), set(expected))
            for key in expected:
                self.assert_summary_equal(actual[key], expected[key])
        elif isinstance(expected, list):
            self.assertEqual(len(actual), len(expected))
            for left, right in zip(actual, expected):
                self.assert_summary_equal(left, right)
        elif isinstance(expected, float):
            self.assertAlmostEqual(actual, expected, delta=1e-12)
        else:
            self.assertEqual(actual, expected)

    def test_metrics_count_errors_and_label_confusion(self):
        records=[dict(id='1',task='t',target='A',prediction='A',latency_seconds=1,response={'usage':{'cost':.1}}),
                 dict(id='2',task='t',target='B',error={'type':'ValueError'},latency_seconds=3,response={})]
        result=report.metrics(records,'chat')
        self.assertEqual(result['correct'],1)
        self.assertEqual(result['valid'],1)
        self.assertEqual(result['confusion']['B']['__error__'],1)
        self.assertIsNone(result['usage']['reported_cost_usd'])
        self.assertIsNone(result['calibration'])
        self.assertEqual(result['median_latency_seconds'],2)

    def test_export_omits_text_and_rejects_derived_record_edits(self):
        import tempfile,json
        from pathlib import Path
        from evals.model_panel import prepare,run
        class Client:
            def base(self,payload):
                return {'choices':[{'finish_reason':'stop','message':{'content':'{"choice":"A"}'}}], 'model':'test/chat','usage':{'cost':.01}}
        with tempfile.TemporaryDirectory() as tmp:
            raw=Path(tmp)/'raw';public=Path(tmp)/'public'
            prepare(raw,[dict(id='1',task='demo',input='SOURCE_NOT_FOR_PUBLICATION',criteria={'A':'COPYRIGHT_OPTION'},target='A')],
                    [dict(id='test/chat',kind='chat',options={})],{})
            run(raw,Client());summary=report.export_run(raw,public)
            self.assertNotIn('SOURCE_NOT_FOR_PUBLICATION',(public/'records.json').read_text())
            self.assertNotIn('COPYRIGHT_OPTION',(public/'records.json').read_text())
            self.assertEqual(report.regenerate(public),summary)
            (public/'records.json').write_text('[]')
            with self.assertRaisesRegex(ValueError,'changed'):report.regenerate(public)

    def test_real_agent_final_states_replay_from_receipts(self):
        import json
        from pathlib import Path
        from evals.scenarios import World
        from evals.run import aggregate
        root=Path(__file__).resolve().parents[1]/'evals/results/agent-v4-panel-2026-09-22'
        for result in json.loads((root/'results.json').read_text()):
            world=World(result['case'])
            episode=root/f"r{result['repeat']}-{result['case']}-{result['arm']}"
            events=[json.loads(line) for line in (episode/'events.jsonl').read_text().splitlines()]
            calls={e['step']:e for e in events if e['event']=='api_receipt' and e['kind']=='base'}
            for event in events:
                if event['event']=='environment_step':
                    self.assertEqual(event['call'],json.loads(calls[event['step']]['response']['choices'][0]['message']['content']))
                    self.assertEqual(world.step(event['call']),event['observation'])
            self.assertEqual(world.state,result['final_state'])
            self.assertEqual(world.success(),result['success'])
            self.assertEqual(world.unsafe_attempts,result['unsafe_attempts'])
            self.assert_summary_equal(aggregate([e for e in events if e['event']=='api_receipt']),result['total'])

    def test_published_tables_match_all_derived_metrics(self):
        import json,re,tempfile,shutil
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        for source in (root/'docs/experiments/model-panel/runs').iterdir():
            with tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'run';shutil.copytree(source,target)
                original=(target/'summary.json').read_text(encoding="utf-8")
                table=(target/'table.md').read_text(encoding="utf-8")
                report.regenerate(target)
                self.assert_summary_equal(json.loads((target/'summary.json').read_text(encoding="utf-8")),json.loads(original))
                self.assertEqual((target/'table.md').read_text(encoding="utf-8"),table)
                self.assertIn(table.strip(),(target/'README.md').read_text(encoding="utf-8"))
        for path in (root/'docs/experiments/model-panel').rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding="utf-8")):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((path.parent/link.split('#')[0]).exists(),f'{path}: {link}')
        self.assertIn('*.sha256',(root/'MANIFEST.in').read_text(encoding="utf-8"))
