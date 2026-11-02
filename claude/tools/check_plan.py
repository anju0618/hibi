"""計画の点検。make all の最後に流す。おかしい所があれば理由を出して 1 で終わる。
使い方: python tools/check_plan.py

1. plan/ と logs/ の JSON が読めるか
2. 曜日ごとの予定の時刻が、朝から夜へ順に並んでいるか（その日だけの予定も）
3. 過ぎた日の「その日だけの予定」が残っていないか（注意だけ）
4. DAILY_PLAN.md・STUDY_PLAN.md・GYM_BRIEF.md が元のデータから作り直したものと同じか（手で書き換えていないか）
自分の計画に合わせて、点検を足していく（1週間に買う量と使う量が合うか、など）
"""
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labels import minutes  # noqa: E402
from plan_data import load  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems, notes = [], []


def check_order(days):
    for day, v in days.items():
        last = -1
        for r in v['timeline']:
            start = minutes(re.split(r'[–〜~-]', r['time'])[0].strip())
            if start < last:
                problems.append(f'{day}の予定の順番が逆：{r["time"]} {r["activity"][:20]}')
            last = max(last, start)


def check_date_overrides(schedule):
    today = dt.date.today()
    for d, ov in schedule.get('date_overrides', {}).items():
        if dt.date.fromisoformat(d) < today:
            notes.append(f'過ぎた日の「その日だけの予定」が残っている：{d}（plan/schedule.json の date_overrides から archive/ へ移す）')
        else:
            check_order({d: ov})


def check_generated():
    for script, out in [('make_daily_plan.py', 'DAILY_PLAN.md'), ('make_study_plan.py', 'STUDY_PLAN.md'), ('make_gym_brief.py', 'GYM_BRIEF.md')]:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, out)
            subprocess.run([sys.executable, os.path.join(BASE, 'tools', script), path], check=True, capture_output=True)
            new = open(path, encoding='utf-8').read()
        cur_path = os.path.join(BASE if out == 'GYM_BRIEF.md' else os.path.dirname(BASE), out)
        cur = open(cur_path, encoding='utf-8').read() if os.path.exists(cur_path) else ''
        if new != cur:
            problems.append(f'{out} が元のデータと合っていない（手で書き換えたか、作り直し忘れ）。make all で作り直す')


if __name__ == '__main__':
    try:
        plan = load(BASE)
    except Exception as e:  # JSON が壊れているときはここで止める
        print(f'NG: plan/ か logs/ の JSON が読めない：{e}')
        sys.exit(1)
    check_order(plan['schedule']['days'])
    check_date_overrides(plan['schedule'])
    check_generated()
    for n in notes:
        print('注意:', n)
    for p in problems:
        print('NG:', p)
    print('点検OK' if not problems else f'点検NG（{len(problems)}件）')
    sys.exit(1 if problems else 0)
