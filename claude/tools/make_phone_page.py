"""スマホで見るページ（1枚の HTML）を作る。Claude のアーティファクトとして公開して使う。
使い方: python tools/make_phone_page.py [出力先.html]

- 今日（前後の日にも動かせる）の予定、その日の教材、次のジムのメモ（Claude に渡すためのコピー）
- 予定の行の「始めた」・マーク（起きた・寝たなど）・ひと言メモを押すと、その時刻が残る。
  ページのデータの置き場（db）の log/<日付> に1日1文書で貯まる（本人だけが読み書きできる設定にする）
- Claude の外（普通のブラウザ）で開いたときは、予定の表示だけで記録の機能は出ない
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labels import category, label  # noqa: E402
from make_study_plan import by_date  # noqa: E402
from plan_data import load  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'phone', 'index.html')


def build_data():
    plan = load(BASE)
    sch = plan['schedule']

    def rows(timeline):
        res = []
        for r in timeline:
            name = label(r)
            res.append({'t': r['time'], 'label': name, 'text': r['activity'],
                        'color': '#%02x%02x%02x' % category(r['activity'] + name, sch)[1]})
        return res

    brief_path = os.path.join(BASE, 'GYM_BRIEF.md')
    return {
        'days': {d: {'title': v['title'], 'rows': rows(v['timeline'])} for d, v in sch['days'].items()},
        'overrides': {k: {'title': v['title'], 'rows': rows(v['timeline'])} for k, v in sch.get('date_overrides', {}).items()},
        'study': by_date(plan['study']) if plan['study'] else {},
        'marks': sch.get('marks', ['起きた', '家を出た', '帰った', '寝た']),
        'brief': open(brief_path, encoding='utf-8').read() if os.path.exists(brief_path) else '',
        'generated': dt.date.today().isoformat(),
    }


HTML = r'''<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>日々</title>
<style>
:root{--bg:#0f172a;--surface:#1e293b;--line:#334155;--fg:#f1f5f9;--dim:#94a3b8;--accent:#60a5fa}
@media (prefers-color-scheme: light){:root{--bg:#f8fafc;--surface:#fff;--line:#e2e8f0;--fg:#0f172a;--dim:#64748b;--accent:#2563eb}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;padding:12px;max-width:640px;margin:auto}
h1{font-size:20px;margin:4px 0}h3{margin:0 0 6px;font-size:16px}
.nav{display:flex;gap:8px;align-items:center;margin-bottom:10px}.nav b{flex:1;text-align:center}
button{font:inherit;background:var(--surface);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:6px 12px}
section{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;margin:10px 0}
ul{list-style:none;padding:0;margin:0}li{display:flex;gap:8px;align-items:flex-start;padding:5px 0;border-bottom:1px solid var(--line)}
li:last-child{border:0}.t{color:var(--dim);min-width:84px;font-variant-numeric:tabular-nums}.c{width:5px;align-self:stretch;border-radius:3px}
.x{flex:1}.sub{color:var(--dim);font-size:13px}.past{opacity:.45}.marks{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}
input{font:inherit;width:100%;padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--fg)}
</style></head><body>
<div class="nav"><button id="prev">◀</button><b id="date"></b><button id="next">▶</button></div>
<section><h3 id="title"></h3><ul id="rows"></ul></section>
<section id="studysec"><h3>今日の教材</h3><ul id="study"></ul></section>
<section id="recsec" hidden><h3>記録</h3><div class="marks" id="marks"></div><ul id="reclist"></ul>
<input id="memo" placeholder="ひと言メモ（Enter で残す）"><div class="sub" id="recmsg"></div></section>
<section id="gymsec"><h3>ジム</h3><button id="copybrief">スマホの Claude に渡すメモをコピー</button>
<div class="sub" id="copymsg">コピーして Claude に貼ると、今日のメニューと重さを出してくれます。終わったら、返事を PC の Claude に貼ってください</div></section>
<div class="sub">作成 __GENERATED__</div>
<script>
const DATA = __DATA__;
const $ = id => document.getElementById(id);
const pad = n => String(n).padStart(2, '0');
const key = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const WD = ['日', '月', '火', '水', '木', '金', '土'];
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const mins = t => { const [h, m] = t.split(/[–〜~-]/)[0].trim().split(':'); return +h * 60 + +m; };
const nowHM = () => { const n = new Date(); return `${pad(n.getHours())}:${pad(n.getMinutes())}`; };
let day = new Date(); day.setHours(0, 0, 0, 0);
let CUR_ROWS = [];
const REC = { ok: false, day: null, events: [], unsub: null, busy: Promise.resolve(), err: '' };

function render() {
  const k = key(day), isToday = k === key(new Date());
  const d = DATA.overrides[k] || DATA.days[WD[day.getDay()]];
  $('date').textContent = `${day.getMonth() + 1}/${day.getDate()}（${WD[day.getDay()]}）${isToday ? ' 今日' : ''}`;
  $('title').textContent = d.title;
  CUR_ROWS = d.rows;
  const now = new Date(), nm = now.getHours() * 60 + now.getMinutes();
  const done = new Set(REC.day === k ? REC.events.filter(e => e.k === 'row').map(e => e.plan + e.label) : []);
  $('rows').innerHTML = d.rows.map((r, i) => `<li class="${isToday && mins(r.t) < nm ? 'past' : ''}"><span class="c" style="background:${r.color}"></span>`
    + `<span class="t">${esc(r.t)}</span><span class="x">${esc(r.label)}<div class="sub">${esc(r.text === r.label ? '' : r.text)}</div></span>`
    + (isToday && REC.ok ? `<button data-row="${i}">${done.has(r.t + r.label) ? '済' : '始めた'}</button>` : '') + '</li>').join('');
  const st = DATA.study[k] || [];
  $('studysec').hidden = !st.length;
  $('study').innerHTML = st.map(s => `<li><span class="t">${esc(s.name)}</span><span class="x">${esc(s.text)}<div class="sub">${esc(s.slot)}</div></span></li>`).join('');
  $('gymsec').hidden = !DATA.brief;
  $('recsec').hidden = !(isToday && REC.ok);
  $('marks').innerHTML = DATA.marks.map(m => `<button data-mark="${esc(m)}">${esc(m)}</button>`).join('');
  $('reclist').innerHTML = REC.events.map(e => `<li><span class="t">${esc(e.at)}</span><span class="x">${esc(e.k === 'row' ? e.label + '（予定 ' + e.plan + '）' : e.k === 'memo' ? '📝 ' + e.text : e.label)}</span></li>`).join('')
    || '<li><span class="x sub">今日の記録はまだない</span></li>';
  $('recmsg').textContent = REC.err;
}

function watchDay() {
  const k = key(new Date());
  if (REC.day === k) return;
  if (REC.unsub) REC.unsub();
  REC.day = k; REC.events = [];
  REC.unsub = REC.db.doc('log/' + k).onSnapshot(snap => {
    REC.events = snap.exists ? (snap.data().events || []).map(e => ({ ...e })) : [];
    render();
  }, e => { REC.err = '記録を読めなかった（' + e.code + '）。ページを開き直してください'; render(); });
}

// 書くのは1回ずつ順番に（同じ文書に重ねて書かない）
function save(change) {
  REC.busy = REC.busy.then(async () => {
    const k = key(new Date());
    if (REC.day !== k) watchDay();
    const events = change(REC.events.map(e => ({ ...e })));
    REC.events = events; render();
    try { await REC.db.doc('log/' + k).set({ date: k, events, updated: new Date().toISOString() }); REC.err = ''; }
    catch (e) { REC.err = e.code === 'quota_exceeded' ? '記録の置き場がいっぱい。PC の Claude に古い記録の整理を頼んでください' : '残せなかった（' + e.code + '）。もう一度押してください'; }
    render();
  });
}

document.addEventListener('click', e => {
  const b = e.target.closest('button');
  if (!b) return;
  if (b.id === 'prev' || b.id === 'next') { day.setDate(day.getDate() + (b.id === 'next' ? 1 : -1)); render(); }
  else if (b.id === 'copybrief') { navigator.clipboard.writeText(DATA.brief).then(() => { $('copymsg').textContent = 'コピーしました。Claude に貼ってください'; }); }
  else if (!REC.ok) return;
  else if (b.dataset.row !== undefined) { const r = CUR_ROWS[+b.dataset.row]; save(ev => [...ev, { k: 'row', at: nowHM(), plan: r.t, label: r.label, ts: Date.now() }]); }
  else if (b.dataset.mark) save(ev => [...ev, { k: 'mark', at: nowHM(), label: b.dataset.mark, ts: Date.now() }]);
});
$('memo').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.isComposing && $('memo').value.trim()) { const text = $('memo').value.trim(); $('memo').value = ''; save(ev => [...ev, { k: 'memo', at: nowHM(), text, ts: Date.now() }]); }
});
render();
(async () => {
  const db = window.claude && await window.claude.use('db');
  if (!db) return;  // Claude の外で開いたときは記録の機能なし
  REC.db = db; REC.ok = true;
  watchDay(); render();
  document.addEventListener('visibilitychange', () => { if (!document.hidden) { watchDay(); render(); } });
})();
</script></body></html>
'''

if __name__ == '__main__':
    data = build_data()
    html = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')).replace('__GENERATED__', data['generated'])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    print(f'wrote {OUT} ({os.path.getsize(OUT)} bytes)')
