# 日々（hibi）

**Claude と話しながら、毎日の予定を育てる。** 睡眠・授業・勉強・ジム・食事の計画を Claude Code に管理してもらい、そこから壁紙・カレンダー・スマホのページを自動で作る仕組みのひな形。

```
 Claude と話す → plan/*.json（元データ）が変わる → make all → 予定・壁紙・カレンダー・スマホのページができる
                                                      ↑
                         logs/（実績）と DECISIONS.md（決めた理由）に足していく
```

## できること

| 機能 | 元データ | 出力 |
|---|---|---|
| 曜日ごとの1日の予定（時刻つき） | `claude/plan/schedule.json`, `daily_notes.md` | `DAILY_PLAN.md` |
| 教材の日割り（試験日から逆算。遅れたら開始日をずらす） | `claude/plan/study.json` | `STUDY_PLAN.md` |
| 壁紙（今日と明日の予定。ログインのたびに自動で作り直す） | 同上 | `claude/wallpaper/` |
| カレンダー（iPhone・Google カレンダーに取り込める） | `schedule.json` | `claude/calendar/hibi.ics` |
| スマホのページ（今日の予定・「始めた」ボタン・起きた／寝た・ひと言メモ） | 同上 | `claude/phone/index.html` |
| ジム（スマホの Claude に渡す資料と、返事の記録） | `claude/plan/gym.json`, `claude/logs/` | `claude/GYM_BRIEF.md` |
| 点検（予定の時刻の順番、手で書き換えていないか） | | `make all` の最後 |
| 決めた理由の記録（本人の言葉つき） | | `claude/DECISIONS.md` |

## はじめかた

必要なもの：[Claude Code](https://claude.com/claude-code)、Python 3.9 以上、`make`（Windows は Git Bash に無いので、手順は `CLAUDE.md` 参照）、git。

1. このリポジトリを自分のものにする（GitHub の「Use this template」、または clone して自分の private リポジトリに push）。**private にする**（自分の予定・体の記録が入るため）。
2. 環境を作る：
   ```
   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   ```
   壁紙の日本語表示にフォントが要る（Linux は `sudo apt install fonts-noto-cjk`）。
3. 動くか確かめる（サンプルの予定が出る）：
   ```
   make -C claude all
   ```
4. このフォルダで Claude Code を開いて、次を貼る：

   ```
   このリポジトリは、私の生活・勉強・運動・食事の計画を Claude と一緒に管理する仕組みです。
   CLAUDE.md を読んで、「最初にやること」のとおりに、私への聞き取りから始めてください。
   plan/ の中身は全部サンプルなので、私の計画に作り直してください。
   ```
5. 聞き取りに答える。Claude が `plan/` を作り、`make -C claude all` で `DAILY_PLAN.md` ができる。
6. 以後は、予定を変えたいときも、勉強が遅れたときも、Claude に話すだけ。

## 使いこなし

- **壁紙を自動で更新する**：`python claude/tools/update_wallpaper.py --install`（Linux はログイン時、Windows はログイン・ロック解除・毎朝5時）。
- **スマホのページ**：Claude に「`claude/phone/index.html` をアーティファクトとして出して」と頼む。出したあと、ページのデータの置き場（db）の読み書きを**本人だけ**に設定してもらう。押した時刻は、PC の Claude が読み取って `claude/logs/actual_times.json` に足し、予定を実際に合わせていく。
- **ジム**：`claude/GYM_BRIEF.md`（またはスマホのページのコピーボタン）をスマホの Claude に渡すと、次の重さを決めてくれる。返事を PC の Claude に貼ると記録に入る。使わないなら `gym.json` とジムの予定を消す。
- **教材の写真**：本やプリントを撮った写真を Claude に見せると、中身・進み具合・間違えた所を `claude/textbooks/` に残し、日割りや相談に使う。

## 入っていない物（必要なら Claude に作らせる）

元になった仕組みにはあるが、人によって要らないのでひな形には入れていない。`CLAUDE.md` と `claude/tools/` の書き方に合わせて、Claude に頼めば足せる。

- 食事の管理（献立・作り置き・買い物・1週間の使用量の点検）
- 勉強の進み具合の画面（遅れ・本ごとの進み・週ごとの時間）
- 体重・InBody のグラフ
- 週末テスト・実力テストの作成と採点
- 42 の課題の取得（API）

## 考え方（なぜこうなっているか）

- **見る物は予定だけ。** ログ・元データ・資料は `claude/` に隠す。
- **作る物は直接書き換えない。** 元を直して作り直す（手で直すと次の `make` で消え、点検でも見つかる）。
- **実績は足すだけ。** 記録を書き換えないので、あとから「実際にどうだったか」を信じられる。
- **理想の予定ではなく、回る予定にする。** 実際の時刻を記録して、予定を実際に合わせる。遅れは取り戻そうと詰め込まず、開始日をずらして作り直す。予備日を入れておく。
- **決めたことは理由つきで残す。** 後から「なぜこうしたか」が追えるので、Claude に任せやすくなる。
