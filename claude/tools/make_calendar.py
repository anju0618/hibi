"""1週間の予定を iPhone・Google カレンダーに取り込める .ics ファイルにする。
使い方: python tools/make_calendar.py [出力先.ics]

- plan/schedule.json の calendar.start から calendar.until まで毎週くり返す
- date_overrides（その日だけの予定）の日は、毎週の予定から外して単発の予定にする
- 通知は、行に "alert": true を付けた予定と、categories の alert が true の分類にだけ付ける
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labels import ORDER, category, label, minutes, parse_time  # noqa: E402
from plan_data import load  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'calendar', 'hibi.ics')
SCHEDULE = load(BASE)['schedule']
CAL = SCHEDULE['calendar']
START = dt.date.fromisoformat(CAL['start'])
UNTIL = dt.date.fromisoformat(CAL['until']).strftime('%Y%m%dT145959Z')  # 日本時間 23:59:59
ALERT_CATS = {c['name'] for c in SCHEDULE.get('categories', []) if c.get('alert')}
OVERRIDES = SCHEDULE.get('date_overrides', {})
EXDATES = {}
for k in OVERRIDES:
    d = dt.date.fromisoformat(k)
    EXDATES.setdefault(d.weekday(), []).append(d)


def build_events(rows):
    events = []
    for i, r in enumerate(rows):
        s, e = parse_time(r['time'])
        sm = minutes(s)
        if e:
            em = minutes(e)
        elif i + 1 < len(rows):
            em = max(minutes(parse_time(rows[i + 1]['time'])[0]), sm + 5)
        else:
            em = sm + 10
        name = label(r)
        cat = category(r['activity'] + name, SCHEDULE)[0]
        events.append({'start': sm, 'end': em, 'summary': name, 'desc': r['activity'], 'cat': cat,
                       'alert': bool(r.get('alert')) or cat in ALERT_CATS})
    return events


def esc(text):
    return text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def fold(line):
    out, cur = [], b''
    for ch in line:
        b = ch.encode('utf-8')
        if len(cur) + len(b) > 73:
            out.append(cur.decode('utf-8'))
            cur = b' ' + b
        else:
            cur += b
    out.append(cur.decode('utf-8'))
    return '\r\n'.join(out)


def fmt(date, mins):
    return f'{date:%Y%m%d}T{mins // 60:02d}{mins % 60:02d}00'


def vevent(uid, date, ev, rrule=None):
    lines = ['BEGIN:VEVENT', f'UID:{uid}@hibi', 'DTSTAMP:20260101T000000Z',
             f'DTSTART;TZID=Asia/Tokyo:{fmt(date, ev["start"])}', f'DTEND;TZID=Asia/Tokyo:{fmt(date, ev["end"])}',
             f'SUMMARY:{esc(ev["summary"])}', f'DESCRIPTION:{esc(ev["desc"])}']
    if ev['cat']:
        lines.append(f'CATEGORIES:{esc(ev["cat"])}')
    if rrule:
        lines.append(rrule)
        for d in EXDATES.get(date.weekday(), []):
            lines.append(f'EXDATE;TZID=Asia/Tokyo:{fmt(d, ev["start"])}')
    if ev['alert']:
        lines += ['BEGIN:VALARM', 'ACTION:DISPLAY', f'DESCRIPTION:{esc(ev["summary"])}', 'TRIGGER:PT0M', 'END:VALARM']
    lines.append('END:VEVENT')
    return lines


cal = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//hibi//weekly//JA', 'CALSCALE:GREGORIAN', 'X-WR-CALNAME:日々の計画',
       'X-WR-TIMEZONE:Asia/Tokyo', 'BEGIN:VTIMEZONE', 'TZID:Asia/Tokyo', 'BEGIN:STANDARD', 'DTSTART:19700101T000000',
       'TZOFFSETFROM:+0900', 'TZOFFSETTO:+0900', 'TZNAME:JST', 'END:STANDARD', 'END:VTIMEZONE']
count = alerts = 0
for wd, day in enumerate(ORDER):  # 月=0
    first = START + dt.timedelta(days=(wd - START.weekday()) % 7)
    for i, ev in enumerate(build_events(SCHEDULE['days'][day]['timeline'])):
        cal += vevent(f'{wd}-{i}', first, ev, f'RRULE:FREQ=WEEKLY;UNTIL={UNTIL}')
        count += 1
        alerts += ev['alert']
for k, ov in OVERRIDES.items():
    for i, ev in enumerate(build_events(ov['timeline'])):
        cal += vevent(f'{k}-{i}-ov', dt.date.fromisoformat(k), ev)
        count += 1
cal.append('END:VCALENDAR')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8', newline='') as f:
    f.write('\r\n'.join(fold(l) for l in cal) + '\r\n')
print(f'saved {OUT}: 1週間 {count} 件（うち通知 {alerts} 件）')
