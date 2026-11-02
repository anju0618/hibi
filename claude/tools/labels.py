"""壁紙・カレンダー・スマホのページで共通の、予定の短い表示名と分類。"""
import re

ORDER = ['月', '火', '水', '木', '金', '土', '日']
DEFAULT_COLOR = (203, 213, 225)


def parse_time(time):
    """'6:05–6:15' → ('6:05', '6:15')、'16:30〜' → ('16:30', None)"""
    parts = [p.strip() for p in re.split(r'[–〜~-]', time) if p.strip()]
    return parts[0], (parts[1] if len(parts) > 1 else None)


def minutes(hhmm):
    h, m = hhmm.split(':')
    return int(h) * 60 + int(m)


def label(row):
    """予定の行の短い表示名。row に "short" があればそれ、なければ最初の一文（かっこの中は省く）"""
    if row.get('short'):
        return row['short']
    t = row['activity'].replace('**', '').split('\n')[0]
    t = re.split(r'[。]', t)[0]
    t = re.sub(r'（[^）]*）?', '', t)
    t = re.sub(r'\([^)]*\)?', '', t)
    if '：' in t:
        head = t.split('：', 1)[0]
        t = head if len(head) >= 2 else t
    return t.strip() or row['activity'][:12]


def category(text, schedule):
    """schedule.json の categories（上から順に、キーワードを含む最初のもの）→ (名前, 色)。なければ (None, 灰色)"""
    for c in schedule.get('categories', []):
        if any(k in text for k in c['keywords']):
            return c['name'], tuple(c['color'])
    return None, DEFAULT_COLOR


def rows_of(schedule, date):
    """その日の予定の行。date_overrides（その日だけの予定）があればそれを使う"""
    ov = schedule.get('date_overrides', {}).get(date.isoformat())
    return (ov or schedule['days'][ORDER[date.weekday()]])['timeline']
