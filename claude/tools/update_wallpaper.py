"""予定（plan/ の計画・教材の日割り）から壁紙を作り直して、デスクトップの壁紙に設定する。
Linux（GNOME）・Windows の両方で動く（Mac は壁紙の設定の部分を自分で足す）。
使い方: python tools/update_wallpaper.py              git pull → 壁紙を作り直す → 設定する
        python tools/update_wallpaper.py --install    自動で動くように登録する
                                                      Windows: ログイン時・ロック解除時・毎朝5時（寝ていたら起きたとき）
                                                      （スリープから起きた直後の実行は止められることがあるので、ロック解除でもう一度動かす）
                                                      Linux: ログイン時
        python tools/update_wallpaper.py --uninstall  登録を消す
"""
import datetime as dt
import glob
import os
import platform
import re
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.abspath(__file__)
WALL = os.path.join(BASE, 'wallpaper')
VENV = os.path.join(os.path.dirname(BASE), '.venv')  # .venv はリポジトリの一番上
LOG = os.path.join(WALL, 'update.log')
STUDY = '--study' in sys.argv
WIN = platform.system() == 'Windows'
TASK = 'hibi_wallpaper'
AUTOSTART = os.path.expanduser('~/.config/autostart/hibi_wallpaper.desktop')
NO_WINDOW = 0x08000000 if WIN else 0  # Windows で黒い画面を出さない


def log(msg):
    print(msg)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n')


def run(cmd, **kw):
    # Windows の既定の文字コード（cp932）で読めない出力があると stderr が None になるので utf-8 で読む
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace',
                          creationflags=NO_WINDOW, **kw)


def pull():
    # パスフレーズやパスワードを聞かれて止まらないようにする
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_SSH_COMMAND='ssh -o BatchMode=yes')
    try:
        r = run(['git', '-C', BASE, 'pull', '--ff-only', '-q'], env=env, timeout=60)
        if r.returncode:
            log('git pull できず（手元の予定のまま作る）: ' + r.stderr.strip())
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f'git pull できず（手元の予定のまま作る）: {e}')


def screen_size():
    """画面の縦横（ピクセル）。分からなければ None"""
    if WIN:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()  # 拡大表示の設定に関係なく本当の解像度を取る
        return ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
    if shutil.which('xrandr'):
        m = re.search(r' connected (?:primary )?(\d+)x(\d+)\+', run(['xrandr', '--current']).stdout)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None


def make():
    # GNOME は同じパスだと読み直さないので、毎回ファイル名を変える
    out = os.path.join(WALL, f'current_{dt.datetime.now():%Y%m%d%H%M%S}.png')
    size = screen_size()
    # 横1920の目盛りで画面と同じ縦横比にする（字の大きさの見え方は画面が変わっても同じ）
    size_arg = [f'--size=1920x{round(1920 * size[1] / size[0])}', f'--scale={max(1, round(size[0] / 1920))}'] if size else []
    # 配置は横1920の目盛りのまま、画素を画面に合わせて増やす（4K なら2倍）。引き伸ばさないので字がくっきりする
    cmd = [sys.executable, os.path.join(BASE, 'tools', 'make_wallpaper.py')] + (['--study'] if STUDY else []) + size_arg + [out]
    r = run(cmd)
    if r.returncode:
        raise RuntimeError('壁紙を作れなかった: ' + r.stderr.strip())
    return out


def set_wallpaper(path):
    if WIN:
        import ctypes
        # SPI_SETDESKWALLPAPER。設定を保存して、全部のウィンドウに知らせる
        if not ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3):
            raise RuntimeError('壁紙を設定できなかった')
        return
    if shutil.which('gsettings'):
        uri = 'file://' + path
        for key, value in (('picture-uri', uri), ('picture-uri-dark', uri), ('picture-options', 'zoom')):
            run(['gsettings', 'set', 'org.gnome.desktop.background', key, value])  # 古い GNOME には -dark がない
        return
    if shutil.which('feh'):
        run(['feh', '--bg-max', path])
        return
    raise RuntimeError('壁紙を設定する方法が見つからない（gsettings も feh もない）。画像は ' + path)


def update():
    os.makedirs(WALL, exist_ok=True)
    pull()
    path = make()
    set_wallpaper(path)
    for old in glob.glob(os.path.join(WALL, 'current_*.png')):
        if old != path:
            os.remove(old)
    log('壁紙を更新: ' + os.path.basename(path))


def venv_python():
    """Pillow を入れた専用の Python（BASE/.venv）を用意する。ネットがなくても毎回動くように"""
    py = os.path.join(VENV, 'Scripts', 'pythonw.exe') if WIN else os.path.join(VENV, 'bin', 'python')
    if not os.path.exists(py):
        uv = shutil.which('uv')
        if uv:
            subprocess.run([uv, 'venv', VENV], check=True)
        else:
            subprocess.run([sys.executable, '-m', 'venv', VENV], check=True)
    pip_py = py.replace('pythonw.exe', 'python.exe')
    uv = shutil.which('uv')
    if uv:
        subprocess.run([uv, 'pip', 'install', '--python', pip_py, '-q', 'pillow'], check=True)
    else:
        subprocess.run([pip_py, '-m', 'pip', 'install', '-q', 'pillow'], check=True)
    return py


def install():
    py = venv_python()
    args = [HERE] + (['--study'] if STUDY else [])
    if WIN:
        user = os.environ.get('USERDOMAIN', '') + '\\' + os.environ['USERNAME']
        start = f'{dt.date.today() + dt.timedelta(days=1)}T05:00:00'
        xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger><UserId>{escape(user)}</UserId><Delay>PT30S</Delay></LogonTrigger>
    <CalendarTrigger><StartBoundary>{start}</StartBoundary><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger>
    <SessionStateChangeTrigger><UserId>{escape(user)}</UserId><StateChange>SessionUnlock</StateChange><Delay>PT10S</Delay></SessionStateChangeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author"><UserId>{escape(user)}</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal>
  </Principals>
  <Settings>
    <StartWhenAvailable>true</StartWhenAvailable>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <RestartOnFailure><Interval>PT1M</Interval><Count>3</Count></RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>{escape(py)}</Command><Arguments>{escape(subprocess.list2cmdline(args))}</Arguments></Exec>
  </Actions>
</Task>
'''
        tmp = os.path.join(WALL, 'task.xml')
        os.makedirs(WALL, exist_ok=True)
        with open(tmp, 'w', encoding='utf-16') as f:
            f.write(xml)
        r = run(['schtasks', '/Create', '/TN', TASK, '/XML', tmp, '/F'])
        os.remove(tmp)
        if r.returncode:
            raise RuntimeError('タスクを登録できなかった: ' + (r.stderr or r.stdout).strip())
        print(f'タスク「{TASK}」を登録した（ログイン時・ロック解除時・毎朝5時）')
    else:
        os.makedirs(os.path.dirname(AUTOSTART), exist_ok=True)
        with open(AUTOSTART, 'w', encoding='utf-8') as f:
            f.write('[Desktop Entry]\nType=Application\nName=hibi wallpaper\n'
                    f'Exec={" ".join([py] + args)}\nX-GNOME-Autostart-enabled=true\nNoDisplay=true\n')
        print('ログイン時に動くように登録した: ' + AUTOSTART)
    subprocess.run([py.replace('pythonw.exe', 'python.exe')] + args, check=True)  # 今すぐ1回動かす


def uninstall():
    if WIN:
        r = run(['schtasks', '/Delete', '/TN', TASK, '/F'])
        print(r.stdout.strip() or r.stderr.strip())
    elif os.path.exists(AUTOSTART):
        os.remove(AUTOSTART)
        print('消した: ' + AUTOSTART)


if __name__ == '__main__':
    if '--install' in sys.argv:
        install()
    elif '--uninstall' in sys.argv:
        uninstall()
    else:
        try:
            update()
        except Exception as e:
            log(f'失敗: {e}')
            raise
