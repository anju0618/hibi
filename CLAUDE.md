# 日々（hibi）— AI 向けの決まりごと

本人の生活・勉強・運動・食事の計画を、Claude が相談役・パートナーとして管理するリポジトリ。**本人は決めてほしいことを Claude に任せている。** 決めたことは本人の言葉と理由つきで `claude/DECISIONS.md` に残す。

## 最初にやること（plan/ がサンプルのままのとき）
`claude/plan/schedule.json` の `status` に「サンプル」とあれば、まだ本人の計画ではない。`README.md` の「はじめかた」のとおり、次の順で進める。
1. 本人に聞き取りをする（一度に聞きすぎない。決められないことは「こうしたらどう？」と案を出す）：睡眠・起きる時刻、授業や仕事の時間と通う時間、運動（場所と開く時間）、食事、勉強したい教材と試験日、目標、使う端末（Linux・Windows・Mac／スマホ）。
2. 答えから `claude/plan/schedule.json`（曜日ごとの予定）、`study.json`、`gym.json`（使うなら）、`profile_goals.json` を作る。サンプルの値は全部消して、本人の値にする。`status` から「サンプル」を消す。
3. 教材の目次・シリーズの巻数・試験の日程は、本人に聞く前にネットで調べる。
4. `make -C claude all` が「点検OK」になるまで直す。`DAILY_PLAN.md` を本人に見せる。
5. 決めたことを `DECISIONS.md` に足し、コミットする。

## どこに何があるか
一番上に置くのは、本人が見る予定だけ：`DAILY_PLAN.md`・`STUDY_PLAN.md`・`tests/`（テストのページと採点）。**それ以外は全部 `claude/` の中。** 一番上に新しいファイルやフォルダを増やさない。下の表は `claude/` から見た場所。

| 場所 | 中身 | 書き方 |
|---|---|---|
| `plan/schedule.json` | 曜日ごとの予定（days）・その日だけの予定（date_overrides）・分類と色（categories）・カレンダーの期間（calendar）・スマホの記録ボタン（marks）・前提（premises） | 今の計画。変わったら上書き |
| `plan/study.json` | 教材（節の一覧か総量・曜日・1回の量）・期間・予備日・試験 | 同上 |
| `plan/gym.json` | ジムのメニュー・増やすルール・けが | 同上 |
| `plan/diet.json`・`plan/profile_goals.json` | 食事・プロフィールと目標（使うものだけ） | 同上 |
| `plan/daily_notes.md` | DAILY_PLAN.md の手で書く部分 | 同上 |
| `logs/*.json` | ジム（gym_training）・InBody（inbody）・食事（meals）・実際の時刻（actual_times） | **足すだけ。書き換えない** |
| `archive/` | 古い版。`<中身>_<開始日>〜<終了日>.json` の名前で置く | 読み込まない。参照だけ |
| `DECISIONS.md` | いつ・何を・なぜ決めたか（本人の言葉つき）。新しい日付を上に足す | 足す |
| `BOOKSHELF.md` | 手持ちの本。**教材を提案する前に必ず見る** | 上書き |
| `toc/`・`textbooks/` | 使っている本の目次・本人が撮った教材の写真の書き起こし（どこまで進んだか・どこを間違えたか） | 上書き。新しい写真をもらったら書き足す |

作るファイル（**直接書き換えない**。元を直して `make all`）：`DAILY_PLAN.md`・`STUDY_PLAN.md`・`claude/GYM_BRIEF.md`・`claude/wallpaper/*.png`・`claude/calendar/hibi.ics`・`claude/phone/index.html`。`make` は `claude/` の中で動かす（一番上からなら `make -C claude all`）。`.venv` は一番上に置く（`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`）。Windows の Git Bash には `make` がないので、`claude/Makefile` の順に `python claude/tools/xxx.py` を動かす。

## 計画を変えたら
1. `plan/` の元を直す（予定は `plan/schedule.json` の days。壁紙・カレンダーの表示名は行の `short`、色は `categories`）。
2. `make -C claude all`（作り直し → `tools/check_plan.py` で点検。NG なら直す）。
3. `make -C claude wallpaper-set`（デスクトップの壁紙にも設定）。
4. 決めたことを `DECISIONS.md` に本人の言葉つきで足す。
5. コミットする。push するかどうかは本人に最初に一度だけ聞いて、ここに書いておく：**push は〈 毎回確認する ／ 常にやる 〉（未設定）**。
6. スマホのページを同じ URL に出し直す（初めて出したとき、その URL をここに書く）：`claude/phone/index.html` → 〈URL 未設定〉

## スマホのページと実際の時刻の記録
- 本人はスマホのページで、予定の行の「始めた」・マーク（起きた／家を出た／帰った／寝た）・ひと言メモを押す。ページのデータの置き場（db）の `log/<日付>`（1日1文書、`events` に `{k: row|mark|memo, at, plan, label, text, ts}`）に残る。**db の rules は read・write とも owner にする**（本人だけが読み書きできる）。
- 読むときは `db_list`（アーティファクトの slug、collection `log`）。読んだ日の分を `logs/actual_times.json` に足し（足すだけ）、予定とのずれを週ごとにまとめて、予定の時間を実際に合わせる。移した日の文書は db から消してよい（置き場の上限があるため）。

## ジム（スマホの Claude との分担）
- 重さを決めるのはスマホの Claude。渡すのは `claude/GYM_BRIEF.md` だけ（記録を全部渡さない）。スマホのページの「メモをコピー」ボタンでも渡せる。
- 本人がスマホの Claude の返事（`GYM_BRIEF.md` の最後の「返事の形」）を貼ったら：その日の記録を `logs/gym_training.json` に、InBody を `logs/inbody.json` に足し、`plan/gym.json` の current_program の重さ・状態を更新して `make -C claude all`。

## 決まりごと
- 古くなった内容は消さずに `archive/` へ（期間をファイル名に）。`plan/` には今の計画だけを置く。日付つきのメモ（`xxx_2026-10-24` のような項目）を `plan/` に増やさず、理由は `DECISIONS.md` に書く。
- 壁紙はログインのときに `claude/tools/update_wallpaper.py` が自動で作り直す。登録は `python claude/tools/update_wallpaper.py --install`。リポジトリの場所を変えたら登録し直す。
- 本人への説明は日本語で、平易に。専門用語には説明をつける。
