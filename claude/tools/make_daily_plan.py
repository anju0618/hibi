"""DAILY_PLAN.md を作る。
使い方: python tools/make_daily_plan.py [出力先.md]

- 手で書く部分は plan/daily_notes.md（前提・家事・持ち物など）。目印 <!-- DAYS --> のところに曜日ごとの予定を差し込む
- 曜日ごとの予定は plan/schedule.json の days から作る
- 予定を変えるときは plan/schedule.json を直して、これを流し直す（DAILY_PLAN.md は直接書き換えない）
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan_data import load  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BASE)  # 本人が見る予定（DAILY_PLAN.md・STUDY_PLAN.md）はリポジトリの一番上、ほかは claude/ の中
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'DAILY_PLAN.md')


def days_md(days):
    out = []
    for day, v in days.items():
        out += [f'### {day}（{v["title"]}）', '| 時間 | やること |', '|---|---|']
        for r in v['timeline']:
            out.append(f'| {r["time"]} | {r["activity"].replace(chr(10), "<br>")} |')
        out.append('')
    return '\n'.join(out)


if __name__ == '__main__':
    plan = load(BASE)
    notes_path = os.path.join(BASE, 'plan', 'daily_notes.md')
    notes = open(notes_path, encoding='utf-8').read() if os.path.exists(notes_path) else '<!-- DAYS -->\n'
    head = ('# 毎日の計画\n\n**このファイルは `claude/tools/make_daily_plan.py` で作る。直接書き換えない。**'
            '曜日ごとの予定は `claude/plan/schedule.json`、それ以外は `claude/plan/daily_notes.md` を直して作り直す。\n\n')
    notes = notes.split('\n', 3)[3] if notes.startswith('# ') else notes  # daily_notes.md の見出しと説明の3行は外す
    body = re.sub(r'<!-- DAYS.*?-->', lambda m: days_md(plan['schedule']['days']), notes)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(head + body)
    print(f'wrote {OUT}')
