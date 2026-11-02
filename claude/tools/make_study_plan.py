"""教材を「何日に・何をやるか」まで日割りした STUDY_PLAN.md を作る。
使い方: python tools/make_study_plan.py [出力先.md]

plan/study.json の考え方：
- start〜end の間で、spare_dates（予備日。遅れの取り戻し）以外の日に、教材ごとに days（曜日）の日だけ per_day ずつ進める
- 教材は sections（節の名前の一覧。目次から）か total（ページ数・問題数など）のどちらかで持つ
- 勉強できなかった日があったら start を後ろにずらして作り直す（教材は前から順に割り当てるので、遅れた分が後ろにずれる）
- exams は試験日（逆算の目印として STUDY_PLAN.md の先頭に出すだけ）
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labels import ORDER  # noqa: E402
from plan_data import load  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BASE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'STUDY_PLAN.md')


def by_date(study):
    """{日付(iso): [{key, name, text, slot, done}]}。教材は前から順に、枠の来た日に割り当てる"""
    start, end = dt.date.fromisoformat(study['start']), dt.date.fromisoformat(study['end'])
    spare = set(study.get('spare_dates', []))
    pos = {m['key']: 0 for m in study['materials']}
    out, d = {}, start
    while d <= end:
        if d.isoformat() not in spare:
            for m in study['materials']:
                if ORDER[d.weekday()] not in m['days']:
                    continue
                n = len(m['sections']) if 'sections' in m else m['total']
                a, b = pos[m['key']], min(pos[m['key']] + m.get('per_day', 1), n)
                if a >= n:
                    continue
                pos[m['key']] = b
                if 'sections' in m:
                    text = '、'.join(m['sections'][a:b])
                else:
                    text = f'{a + 1}〜{b}{m.get("unit", "")}' if b - a > 1 else f'{b}{m.get("unit", "")}'
                out.setdefault(d.isoformat(), []).append({'key': m['key'], 'name': m['name'], 'text': text,
                                                          'slot': m.get('slot', '')})
        d += dt.timedelta(days=1)
    return out


def main():
    study = load(BASE)['study']
    start = dt.date.fromisoformat(study['start'])
    plan = by_date(study)
    out = ['# 教材の日割り', '',
           '**このファイルは `claude/tools/make_study_plan.py` で作る。直接書き換えない。** 元は `claude/plan/study.json`。', '',
           f'期間：{study["start"]} 〜 {study["end"]}'
           + (f'　予備日（遅れの取り戻し）：{"、".join(study["spare_dates"])}' if study.get('spare_dates') else '')]
    if study.get('exams'):
        out += ['', '試験：' + '、'.join(f'{e["name"]}（{e["date"]}）' for e in study['exams'])]
    out += ['', '## 教材', '| 記号 | 教材 | 曜日 | 1回の量 | 全体 | 終わる日 |', '|---|---|---|---|---|---|']
    for m in study['materials']:
        n = len(m['sections']) if 'sections' in m else m['total']
        last = max((d for d, xs in plan.items() if any(x['key'] == m['key'] for x in xs)), default='（入りきらない）')
        out.append(f'| {m["key"]} | {m["name"]} | {"".join(m["days"])} | {m.get("per_day", 1)}{m.get("unit", "")} | {n}{m.get("unit", "")} | {last} |')
    week = start - dt.timedelta(days=start.weekday())
    end = dt.date.fromisoformat(study['end'])
    while week <= end:
        out += ['', f'## {week:%m/%d}〜の週', '| 日 | 教材 | 中身 | 枠 |', '|---|---|---|---|']
        for k in range(7):
            d = week + dt.timedelta(days=k)
            rows = plan.get(d.isoformat(), [])
            if d.isoformat() in set(study.get('spare_dates', [])):
                out.append(f'| {d:%m/%d}({ORDER[d.weekday()]}) | 予備日 | 遅れを取り戻す | |')
            for x in rows:
                out.append(f'| {d:%m/%d}({ORDER[d.weekday()]}) | {x["name"]} | {x["text"]} | {x["slot"]} |')
        week += dt.timedelta(days=7)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
