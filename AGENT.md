# AGENT.md: Operational Protocol for AI Coding Agents

This repository implements an experimental economics research platform using **oTree 5/6**, **Python 3.12**, and **statsmodels**. All AI agents operating in this repository must strictly adhere to the following principles.

---

## 1. Environment & Execution Rules
- **Virtual Environment Only:** Always activate and execute inside `.venv`.
  - macOS/Linux: `source .venv/bin/activate` or prefix commands with `.venv/bin/`
  - Windows: `.\.venv\Scripts\Activate.ps1`
  - Never execute global `pip install` commands.
- **Python Version Integrity:** Use Python 3.12. Do not upgrade to Python 3.13+ or 3.14 without verifying pre-compiled wheel compatibility for `numpy`, `scipy`, and `pyarrow`.
- **Database Safety:** **Never directly edit `db.sqlite3`**. Use `otree resetdb --noinput` to reset schemas when models change.
- **Dependency Hygiene:** Do not install packages that force upgrades of `websockets` or `starlette` beyond oTree 5/6 compatibility constraints. `pyfixest` must not be installed in the main `.venv` because it forces `click>=8` and `websockets>=12` which breaks oTree.

---

## 2. Experimental Design Invariants
- **Strict Net Cost Equivalence:** Under all circumstances, the net financial advantage of public transit over private car must remain **strictly identical** in Treatment B (Loss) and Treatment C (Gain):
  $$\Delta \text{Cost}_B = \Delta \text{Cost}_C = \Delta \text{Cost}_A + 30$$
  Never alter cost tables without maintaining this exact equivalence.
- **Balanced Randomization:** Session-level treatment assignment must remain balanced complete randomization by default (`balanced_random`), with fixed branches available (`modal_shift_A`, `modal_shift_B`, `modal_shift_C`).
- **NEP Reverse Coding:** When modifying or processing the 15-item Revised NEP Scale (Dunlap et al., 2000), even-numbered items (2, 4, 6, 8, 10, 12, 14) must always be reverse-coded: $\text{score} = 6 - \text{response}$.

---

## 3. oTree 5/6 API Standards
- Use the modern simplified oTree 5/6 API:
  - Constants class: `class C(BaseConstants):`
  - Subsession hook: `creating_session(subsession)`
  - Page definitions: `class MyPage(Page): form_model = 'player'`
  - Bot submissions: `yield Submission(MyPage, dict(...))`
  - Bot assertions: `expect(expected, "in", self.html)` or `expect(val1, val2)`
- Do not import legacy oTree 3/4 constructs (`models.BasePlayer`, `views.Page`, `Group.get_player_by_id`).

---

## 4. Repository Layout & File Locations
- Apps live at root: `intro/`, `commute_choice/`, `survey_demographics/`, `survey_traits/`, `post_task/`.
- Shared simulation logic must reside in `dgp.py`.
- Bot parameter presets live in `bots_config.json`.
- Utility CLI scripts live in `scripts/`:
  - Room management: `scripts/manage_rooms.py`
  - Link generation: `scripts/generate_links.py`
  - Bot simulation: `scripts/run_bots.py`
  - Fallback simulation: `scripts/simulate_fallback.py`
- Econometric pipelines live in `analysis/`:
  - Data cleaning: `analysis/prepare_data.py`
  - Regressions & reporting: `analysis/run_analysis.py`
- Data directories:
  - Bot data: `data/bots/`
  - Live data: `data/live/`
  - Cleaned data: `data/processed/`
- Output directories:
  - Reports & figures: `outputs/{bots,live,both}/`
  - QR codes & links: `outputs/links/`

---

## 5. Verification Gate Before Task Completion
Before concluding any modification or adding features, you must execute and verify that all of the following commands exit cleanly with return code 0:
```bash
otree test modal_shift_A 6
otree test modal_shift_B 6
otree test modal_shift_C 6
otree test modal_shift 60
python scripts/run_bots.py --n 150 --seed 123
python test.py
python analysis/run_analysis.py --source both
```
Keep the `acceptance_checklist.md` artifact up to date.
