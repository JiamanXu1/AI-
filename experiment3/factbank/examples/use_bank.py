"""Run: python3 examples/use_bank.py (no packages or API keys)."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from factbank import FactBank

bank=FactBank()
print('事实及规则记录数:',len(bank.records))
print('规则与来源:',json.dumps(bank.get('R007'),ensure_ascii=False,indent=2))
print('检索:',[(x['id'],x['statement_zh']) for x in bank.search('玫瑰宫 冲击波')])

# Replace this teaching example with your saved model response.
# This does not call a model and does not score any real experimental answer.
answer='玫瑰宫位于伊朗德黑兰，是2013年列入世界遗产的宫殿。'
packet=bank.make_packet(answer,answer_id='TEACHING_EXAMPLE_NOT_REAL_SAMPLE')
target=ROOT/'examples/evidence_packet.json'
target.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('未判分证据包:',target)

# Native Python records are ready for your own evaluation pipeline.
rules=bank._json('rules.json')
facts=bank._json('facts.json')
status=bank._json('treaty_status.json')
assert len(rules)==42 and len(status)==16
