"""計画と記録を読み込む（壁紙・カレンダー・スマホのページ・DAILY_PLAN・ジムのまとめで共通）。

- plan/  今の計画。変わったら上書きする（schedule・study・gym・diet・profile_goals）
- logs/  記録。足すだけで書き換えない（gym_training・inbody・meals・actual_times）
- 無いファイルは空として読む（使わない機能のファイルは作らなくていい）
"""
import json
import os

PLAN_FILES = ['profile_goals', 'schedule', 'study', 'diet', 'gym']
LOG_FILES = ['gym_training', 'inbody', 'meals', 'actual_times']


def _read(path, empty):
    if not os.path.exists(path):
        return empty
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load(base):
    """{'profile_goals', 'schedule', 'study', 'diet', 'gym', 'logs': {...}} を返す"""
    data = {name: _read(os.path.join(base, 'plan', name + '.json'), {}) for name in PLAN_FILES}
    data['logs'] = {name: _read(os.path.join(base, 'logs', name + '.json'), []) for name in LOG_FILES}
    return data
