# claude/ の中で（または一番上から make -C claude all）。計画を変えたら make all（作り直し → 点検）。
# スマホのページは GYM_BRIEF.md を入れるので gym のあと。壁紙をデスクトップにも設定するなら make wallpaper-set
PY := $(if $(wildcard ../.venv/bin/python),$(abspath ../.venv/bin/python),python3)

.PHONY: all study daily wallpaper calendar phone gym check wallpaper-set

all: study daily wallpaper calendar gym phone check

study:
	$(PY) tools/make_study_plan.py

daily:
	$(PY) tools/make_daily_plan.py

wallpaper:
	$(PY) tools/make_wallpaper.py

calendar:
	$(PY) tools/make_calendar.py

phone:
	$(PY) tools/make_phone_page.py

gym:
	$(PY) tools/make_gym_brief.py

check:
	$(PY) tools/check_plan.py

wallpaper-set:
	$(PY) tools/update_wallpaper.py
