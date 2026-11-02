"""スマホの Claude（ジムの重さを決めてもらう相手）に渡す GYM_BRIEF.md を作る。
使い方: python tools/make_gym_brief.py [出力先.md]

ジムの記録を全部読ませるとトークンの無駄なので、次の回を決めるのに要る分だけにする：
今のメニュー（重さ・目標回数・状態）、増やすルール、けがの注意、種目ごとの直近2回、InBody の直近3回。
返事は最後の「返事の形」で書いてもらい、それを Claude Code に貼って logs/ と plan/gym.json に入れる。
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan_data import load  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'GYM_BRIEF.md')


def main():
    plan = load(BASE)
    gym, log, inbody = plan['gym'], plan['logs']['gym_training'], plan['logs']['inbody']
    prog = gym['current_program']
    out = ['# ジムのまとめ（スマホの Claude 用）', '',
           f'{dt.date.today():%Y-%m-%d} に `tools/make_gym_brief.py` で作成。次の回の種目と重さを決めるのに要る分だけ。', '',
           '## お願いしたいこと',
           '- 下の記録を見て、次の回のメニューと重さを決める。終わったら、その日の記録と次回の重さを最後の「返事の形」で書く',
           '- メニューを出すときは毎回、種目ごとに「重さ × 回数 × セット数」と、やり方・呼吸のタイミングを書く',
           f'- 回し方：{prog["rotation_rule"]}', '']
    out += ['## 目標・体', *[f'- {k}：{v}' for k, v in gym.get('profile', {}).items()], '']
    if gym.get('progression_rules'):
        out += ['## 増やすルール', *[f'- {x}' for x in gym['progression_rules']], '']
    if gym.get('injuries'):
        out += ['## けが・注意', *[f'- {x}' for x in gym['injuries']], '']
    for key in prog['rotation']:
        day = prog[key]
        out += [f'## {day["label"]}', '| 種目 | 重さ × 回数 × セット | 状態・次 |', '|---|---|---|']
        for e in day['exercises']:
            out.append(f'| {e["name"]} | {e["kg"]}kg × {e["reps"]} × {e["sets"]} | {e.get("status", "")} |')
        recent = [r for r in log if r.get('day_type', '').lower().startswith(key)][-2:]
        for r in recent:
            ex = '、'.join(f'{x["name"]} {x["weight_kg"]}kg×{",".join(map(str, x["sets"]))}' for x in r['exercises'])
            out.append(f'- 直近 {r["date"]}：{ex}')
        out.append('')
    if inbody:
        out += ['## InBody（直近3回。測る時刻と条件で大きくぶれる）', '| 日付 | 時刻 | 体重 | 骨格筋量 | 体脂肪量 | 体脂肪率 |', '|---|---|---|---|---|---|']
        for b in inbody[-3:]:
            out.append(f'| {b["date"]} | {b.get("time", "")} | {b.get("weight_kg")} | {b.get("skeletal_muscle_mass_kg")} | {b.get("fat_mass_kg")} | {b.get("body_fat_pct")} |')
        out.append('')
    out += ['## 返事の形（これをそのまま Claude Code に貼る）', '```',
            '日付: 2026-11-04', '種類: Push', 'バーベルベンチプレス 40kg 10,10,10（最終セット RIR1）', '…（やった種目を全部）',
            'InBody: 時刻 10:20 / 体重 70.3 / 骨格筋量 30.5 / 体脂肪量 12.8 / 体脂肪率 18.2（測った日だけ）',
            '次回: バーベルベンチプレス 42.5kg（理由：2回連続クリア）', '…（変える種目だけ）', 'メモ: 朝食 有/無、痛み・違和感など', '```', '']
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out))
    print(f'wrote {OUT} ({os.path.getsize(OUT)} bytes)')


if __name__ == '__main__':
    main()
