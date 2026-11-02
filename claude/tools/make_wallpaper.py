"""今日と明日の予定を壁紙の画像にする。
使い方: python tools/make_wallpaper.py [--size=1920x1080] [--scale=1] [出力先.png]

- 今日（左）と明日（右）の予定を、分類の色つきで並べる。今日の過ぎた行は薄くする
- 配置は横1920の目盛りで決め、--scale 倍の画素で描く（4K なら 2）。引き伸ばさないので字がくっきりする
- 日本語のフォントが要る（Linux: fonts-noto-cjk、Windows: 游ゴシック、Mac: ヒラギノ）
"""
import datetime as dt
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labels import ORDER, category, label, minutes, parse_time, rows_of  # noqa: E402
from plan_data import load  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0] if args else os.path.join(BASE, 'wallpaper', 'weekly_schedule.png')
W, H = 1920, 1080
SCALE = 1
for a in sys.argv[1:]:
    if a.startswith('--size='):
        W, H = map(int, a[7:].split('x'))
    elif a.startswith('--scale='):
        SCALE = int(a[8:])

FONTS = ['C:/Windows/Fonts/YuGothM.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
         '/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc']
FONTS_B = ['C:/Windows/Fonts/YuGothB.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
           '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc']
BG, FG, DIM = (15, 23, 42), (241, 245, 249), (100, 116, 139)


def font(size, bold=False):
    for p in (FONTS_B if bold else FONTS):
        if os.path.exists(p):
            return ImageFont.truetype(p, size * SCALE)
    sys.exit('日本語のフォントが見つからない（Linux なら fonts-noto-cjk を入れる）')


def column(d, x0, x1, date, schedule, now):
    fh, fb = font(26, True), font(22)
    s = SCALE
    d.text((x0 * s, 70 * s), f'{date.month}/{date.day}（{ORDER[date.weekday()]}）' + ('　今日' if date == now.date() else '　明日'),
           font=fh, fill=FG)
    rows = rows_of(schedule, date)
    step = min(40, (H - 200) // max(len(rows), 1))
    y = 130
    for r in rows:
        start = minutes(parse_time(r['time'])[0])
        name = label(r)
        color = category(r['activity'] + name, schedule)[1]
        past = date == now.date() and start < now.hour * 60 + now.minute
        dim = lambda c: tuple(int(v * 0.4 + BG[i] * 0.6) for i, v in enumerate(c))  # noqa: E731
        d.rectangle([x0 * s, y * s + 4 * s, (x0 + 6) * s, (y + step - 6) * s], fill=dim(color) if past else color)
        d.text(((x0 + 20) * s, y * s), r['time'], font=fb, fill=DIM)
        d.text(((x0 + 190) * s, y * s), name, font=fb, fill=DIM if past else FG)
        y += step


def main():
    plan = load(BASE)
    schedule = plan['schedule']
    now = dt.datetime.now()
    img = Image.new('RGB', (W * SCALE, H * SCALE), BG)
    d = ImageDraw.Draw(img)
    column(d, 80, 940, now.date(), schedule, now)
    column(d, 1000, 1860, now.date() + dt.timedelta(days=1), schedule, now)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print(f'saved {OUT} ({W * SCALE}x{H * SCALE})')


if __name__ == '__main__':
    main()
