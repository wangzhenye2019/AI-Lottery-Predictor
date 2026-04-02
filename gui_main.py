# -*- coding:utf-8 -*-
"""Author: BigCat"""

import json
import math
import os
import random
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import messagebox
from typing import Dict, List, Optional, Tuple

import customtkinter as ctk
import pandas as pd
import matplotlib
from matplotlib import font_manager, rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import data_file_name, model_args, name_path
from core.strategies import StrategyAnalyzer
from get_data import run as run_get_data
from utils.zhcw_client import fetch_draw_list, format_open_time, normalize_issue

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

HARMONY_FONT_DIR = r"F:\Downloads\HarmonyOS+Sans+字体\HarmonyOS+Sans+字体\HarmonyOS Sans 字体"
UI_FONT_FAMILY: Optional[str] = None


def _setup_matplotlib_chinese() -> None:
    candidates = [
        "Microsoft YaHei",
        "Microsoft YaHei UI",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "PingFang SC",
    ]
    for name in candidates:
        try:
            font_manager.findfont(font_manager.FontProperties(family=name), fallback_to_default=False)
            rcParams["font.sans-serif"] = [name]
            rcParams["axes.unicode_minus"] = False
            return
        except Exception:
            continue
    rcParams["axes.unicode_minus"] = False


def _pick_random_font_file(font_dir: str) -> Optional[str]:
    if not font_dir or not os.path.exists(font_dir):
        return None
    font_files: List[str] = []
    preferred_sc: List[str] = []
    preferred_tc: List[str] = []
    preferred_cjk: List[str] = []
    for root, _, files in os.walk(font_dir):
        for f in files:
            lf = f.lower()
            if lf.endswith('.ttf') or lf.endswith('.otf'):
                full = os.path.join(root, f)
                font_files.append(full)
                p = full.lower()
                if "sanssc" in p:
                    preferred_sc.append(full)
                elif "sanstc" in p:
                    preferred_tc.append(full)
                elif "cjk" in p:
                    preferred_cjk.append(full)

    if preferred_sc:
        return random.choice(preferred_sc)
    if preferred_cjk:
        return random.choice(preferred_cjk)
    if preferred_tc:
        return random.choice(preferred_tc)
    if font_files:
        return random.choice(font_files)
    return None


def _setup_harmony_font() -> None:
    global UI_FONT_FAMILY

    font_file = _pick_random_font_file(HARMONY_FONT_DIR)
    if not font_file:
        return

    try:
        try:
            ctk.FontManager.load_font(font_file)
        except Exception:
            pass
        try:
            font_manager.fontManager.addfont(font_file)
        except Exception:
            pass
        try:
            UI_FONT_FAMILY = font_manager.FontProperties(fname=font_file).get_name()
        except Exception:
            UI_FONT_FAMILY = "HarmonyOS Sans"

        rcParams["font.sans-serif"] = [UI_FONT_FAMILY]
        rcParams["axes.unicode_minus"] = False

        _orig = ctk.CTkFont

        def _ctk_font(*args, **kwargs):
            if UI_FONT_FAMILY and "family" not in kwargs:
                kwargs["family"] = UI_FONT_FAMILY
            return _orig(*args, **kwargs)

        ctk.CTkFont = _ctk_font
    except Exception:
        UI_FONT_FAMILY = None


_setup_matplotlib_chinese()
_setup_harmony_font()

COLORS = {
    "bg": ("#F5F7FB", "#0B1220"),
    "card": ("#FFFFFF", "#111827"),
    "border": ("#E0E3EB", "#243244"),
    "text": ("#202124", "#E5E7EB"),
    "subtext": ("#5F6368", "#AAB4C2"),
    "primary": ("#1A73E8", "#1A73E8"),
    "primary_hover": ("#1669C1", "#1669C1"),
    "danger": ("#D93025", "#F87171"),
    "red": ("#EA4335", "#EA4335"),
    "red_hover": ("#D93025", "#D93025"),
    "blue": ("#1A73E8", "#1A73E8"),
    "blue_hover": ("#1669C1", "#1669C1"),
    "chip": ("#EEF2FF", "#1F2A44"),
    "log_bg": ("#0F172A", "#0B1220"),
    "log_fg": ("#E5E7EB", "#E5E7EB"),
}


@dataclass(frozen=True)
class GameRule:
    key: str
    name: str
    red_max: int
    red_pick: int
    blue_max: int
    blue_pick: int
    draw_weekdays: Tuple[int, ...] = (1, 3, 6)
    close_time: str = "20:00:00"
    cost_per_bet: int = 2


GAME_RULES: Dict[str, GameRule] = {
    "ssq": GameRule(key="ssq", name="双色球", red_max=33, red_pick=6, blue_max=16, blue_pick=1, draw_weekdays=(1, 3, 6), close_time="20:00:00"),
    "dlt": GameRule(key="dlt", name="大乐透", red_max=35, red_pick=5, blue_max=12, blue_pick=2, draw_weekdays=(0, 2, 5), close_time="20:00:00"),
    "qlc": GameRule(key="qlc", name="七乐彩", red_max=30, red_pick=7, blue_max=30, blue_pick=1, draw_weekdays=(0, 2, 4), close_time="20:00:00"),
}


WEEKDAY_CN = {
    0: "一",
    1: "二",
    2: "三",
    3: "四",
    4: "五",
    5: "六",
    6: "日",
}


def _normalize_issue(issue: str) -> str:
    s = str(issue).strip()
    if s.isdigit() and len(s) == 5:
        return "20" + s
    return s


def _parse_draw_date(date_str: str) -> Optional[datetime]:
    s = (date_str or "").strip()
    if len(s) >= 10:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d")
        except Exception:
            return None
    return None


def _format_date_cn(dt: datetime) -> str:
    return f"{dt.strftime('%Y-%m-%d')}({WEEKDAY_CN.get(dt.weekday(), '')})"


def _next_draw_date(last_draw: datetime, rule: GameRule) -> datetime:
    d = last_draw
    for _ in range(10):
        d = d.replace(hour=0, minute=0, second=0, microsecond=0) + pd.Timedelta(days=1)
        if d.weekday() in rule.draw_weekdays:
            return datetime(d.year, d.month, d.day)
    return datetime(d.year, d.month, d.day)


def _calc_current_sale_issue(last_draw_issue: str, last_draw_date: str, rule: GameRule, now: Optional[datetime] = None) -> Tuple[str, str]:
    now = now or datetime.now()
    draw_dt = _parse_draw_date(last_draw_date)
    base_issue = _normalize_issue(last_draw_issue)

    if draw_dt is None or not base_issue.isdigit() or len(base_issue) < 7:
        return base_issue, (last_draw_date or "")

    next_dt = _next_draw_date(draw_dt, rule)
    next_date_str = _format_date_cn(next_dt)

    try:
        last_issue_int = int(base_issue)
        if next_dt.year != draw_dt.year:
            next_issue = f"{next_dt.year}001"
        else:
            next_issue = str(last_issue_int + 1)
    except Exception:
        next_issue = base_issue

    return next_issue, next_date_str


def comb(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def poisson_binomial_pmf(ps: List[float]) -> List[float]:
    dp = [1.0]
    for p in ps:
        nxt = [0.0] * (len(dp) + 1)
        for i, v in enumerate(dp):
            nxt[i] += v * (1 - p)
            nxt[i + 1] += v * p
        dp = nxt
    return dp


def estimate_ssq_prize_prob(
    red_selected: List[int],
    blue_selected: List[int],
    analyzer: StrategyAnalyzer,
    rule: GameRule,
    recent_n: int = 300
) -> Dict[str, float]:
    probs_red = analyzer.calculate_probability("red")
    probs_blue = analyzer.calculate_probability("blue")
    p_red = [float(probs_red.get(x, rule.red_pick / rule.red_max)) for x in red_selected]
    p_blue = [float(probs_blue.get(x, rule.blue_pick / rule.blue_max)) for x in blue_selected]

    pmf_red = poisson_binomial_pmf(p_red)
    pmf_blue = poisson_binomial_pmf(p_blue)

    def p_red_k(k: int) -> float:
        return pmf_red[k] if 0 <= k < len(pmf_red) else 0.0

    def p_blue_k(k: int) -> float:
        return pmf_blue[k] if 0 <= k < len(pmf_blue) else 0.0

    if rule.key != "ssq":
        any_win = 1.0 - (p_red_k(0) * p_blue_k(0))
        return {
            "任意中奖(估算)": max(0.0, min(1.0, any_win)),
        }

    p_b1 = sum(p_blue_k(k) for k in range(1, len(pmf_blue)))
    p_b0 = p_blue_k(0)

    p6 = p_red_k(6)
    p5 = p_red_k(5)
    p4 = p_red_k(4)
    p3 = p_red_k(3)
    p2 = p_red_k(2)
    p1 = p_red_k(1)
    p0 = p_red_k(0)

    grade1 = p6 * p_b1
    grade2 = p6 * p_b0
    grade3 = p5 * p_b1
    grade4 = (p5 * p_b0) + (p4 * p_b1)
    grade5 = (p4 * p_b0) + (p3 * p_b1)
    grade6 = (p2 + p1 + p0) * p_b1
    any_win = grade1 + grade2 + grade3 + grade4 + grade5 + grade6

    return {
        "一等奖(6+1)": grade1,
        "二等奖(6+0)": grade2,
        "三等奖(5+1)": grade3,
        "四等奖(5+0或4+1)": grade4,
        "五等奖(4+0或3+1)": grade5,
        "六等奖(0-2+1)": grade6,
        "任意中奖(估算)": any_win,
    }


class DataCache:
    def __init__(self):
        self._game_key: Optional[str] = None
        self._df: Optional[pd.DataFrame] = None
        self._analyzer: Optional[StrategyAnalyzer] = None
        self._omission_red: Dict[int, int] = {}
        self._omission_blue: Dict[int, int] = {}
        self._hot_red: set[int] = set()
        self._hot_blue: set[int] = set()
        self._latest_issue: str = "未知"
        self._latest_date: str = ""

    def load(self, game_key: str) -> None:
        if self._game_key == game_key and self._df is not None:
            return

        self._game_key = game_key
        self._df = None
        self._analyzer = None
        self._omission_red = {}
        self._omission_blue = {}
        self._hot_red = set()
        self._hot_blue = set()
        self._latest_issue = "未知"
        self._latest_date = ""

        data_path = os.path.join(name_path[game_key]["path"], data_file_name)
        if not os.path.exists(data_path):
            run_get_data(game_key)

        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            self._df = df
            if len(df):
                self._latest_issue = _normalize_issue(str(df.iloc[0].get("期数", "未知")))
                self._latest_date = str(df.iloc[0].get("日期", ""))
            self._analyzer = StrategyAnalyzer(df)
            self._omission_red = self._fast_omission(df, "red")
            self._omission_blue = self._fast_omission(df, "blue")
            self._hot_red = set(self._analyzer.get_hot_numbers("red", recent_n=80, top_ratio=0.33))
            self._hot_blue = set(self._analyzer.get_hot_numbers("blue", recent_n=80, top_ratio=0.33))

            if (not self._latest_date) or ("日期" not in df.columns):
                if game_key in ["ssq", "qlc", "fc3d"]:
                    try:
                        from get_data import spider_cwl
                        api_df = spider_cwl(game_key, 1)
                        if api_df is not None and len(api_df):
                            self._latest_issue = _normalize_issue(str(api_df.iloc[0].get("期数", self._latest_issue)))
                            self._latest_date = str(api_df.iloc[0].get("日期", self._latest_date))
                    except Exception:
                        pass
                elif game_key == "dlt":
                    try:
                        items = fetch_draw_list("dlt", page_num=1, page_size=1)
                        if items:
                            it = items[0]
                            self._latest_issue = _normalize_issue(normalize_issue(it.issue))
                            self._latest_date = format_open_time(it.open_time, it.week)
                    except Exception:
                        pass

    @staticmethod
    def _fast_omission(df: pd.DataFrame, ball_type: str) -> Dict[int, int]:
        cols = [c for c in df.columns if ("红球" in c if ball_type == "red" else "蓝球" in c)]
        if not cols:
            return {}
        values = df[cols].values.astype(int)
        max_num = int(values.max()) if values.size else 0
        total = len(values)
        newest_first = False
        if '期数' in df.columns and len(df) >= 2:
            try:
                first = int(str(df.iloc[0]['期数']))
                last = int(str(df.iloc[-1]['期数']))
                newest_first = first > last
            except Exception:
                newest_first = False

        if newest_first:
            omission = {i: total for i in range(1, max_num + 1)}
            for idx, row in enumerate(values):
                for n in row.tolist():
                    if 1 <= n <= max_num and omission[n] == total:
                        omission[n] = idx
            return omission

        last_seen = {i: -1 for i in range(1, max_num + 1)}
        for idx, row in enumerate(values):
            for n in row.tolist():
                if 1 <= n <= max_num:
                    last_seen[n] = idx
        omission = {}
        for n, seen in last_seen.items():
            omission[n] = (total - 1 - seen) if seen >= 0 else total
        return omission

    @property
    def df(self) -> Optional[pd.DataFrame]:
        return self._df

    @property
    def analyzer(self) -> Optional[StrategyAnalyzer]:
        return self._analyzer

    @property
    def omission_red(self) -> Dict[int, int]:
        return self._omission_red

    @property
    def omission_blue(self) -> Dict[int, int]:
        return self._omission_blue

    @property
    def hot_red(self) -> set[int]:
        return self._hot_red

    @property
    def hot_blue(self) -> set[int]:
        return self._hot_blue

    @property
    def latest_issue(self) -> str:
        return self._latest_issue

    @property
    def latest_date(self) -> str:
        return self._latest_date


class BallGrid(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        title: str,
        max_num: int,
        min_pick: int,
        color_key: str,
        cache: DataCache,
        ball_type: str,
        get_pick_target,
        get_selected,
        set_selected,
        on_change,
    ):
        super().__init__(master, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self._title = title
        self._max_num = max_num
        self._min_pick = min_pick
        self._color_key = color_key
        self._cache = cache
        self._ball_type = ball_type
        self._get_pick_target = get_pick_target
        self._get_selected = get_selected
        self._set_selected = set_selected
        self._on_change = on_change
        self._mode = ctk.StringVar(value="遗漏")
        self._buttons: Dict[int, ctk.CTkButton] = {}
        self._sub_labels: Dict[int, ctk.CTkLabel] = {}

        self.grid_columnconfigure(0, weight=1)
        self._header = ctk.CTkFrame(self, fg_color="transparent")
        self._header.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        self._header.grid_columnconfigure(0, weight=1)

        self._lbl_title = ctk.CTkLabel(self._header, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"])
        self._lbl_title.grid(row=0, column=0, sticky="w")

        self._lbl_hint = ctk.CTkLabel(
            self._header,
            text=f"至少选择{min_pick}个",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["subtext"],
        )
        self._lbl_hint.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self._right = ctk.CTkFrame(self._header, fg_color="transparent")
        self._right.grid(row=0, column=1, rowspan=2, sticky="e")

        self._pick_count = ctk.StringVar(value=str(min_pick))
        self._pick_menu = ctk.CTkOptionMenu(
            self._right,
            variable=self._pick_count,
            values=[str(i) for i in range(min_pick, min(min_pick + 10, max_num) + 1)],
            width=80,
            fg_color=COLORS["chip"],
            text_color=COLORS["text"],
            button_color=COLORS[color_key],
            button_hover_color=COLORS[f"{color_key}_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
        )
        self._pick_menu.grid(row=0, column=0, padx=(0, 10))

        self._btn_random = ctk.CTkButton(
            self._right,
            text="机选",
            width=90,
            fg_color=COLORS[color_key],
            hover_color=COLORS[f"{color_key}_hover"],
            text_color="#FFFFFF",
            command=self._random_pick,
        )
        self._btn_random.grid(row=0, column=1, padx=(0, 10))

        self._btn_clear = ctk.CTkButton(
            self._right,
            text="清空",
            width=70,
            fg_color=COLORS["chip"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._clear,
        )
        self._btn_clear.grid(row=0, column=2)

        self._toggle = ctk.CTkSegmentedButton(
            self._header,
            values=["遗漏", "热号"],
            variable=self._mode,
            selected_color=COLORS[color_key],
            selected_hover_color=COLORS[f"{color_key}_hover"],
            fg_color=COLORS["chip"],
            unselected_color=COLORS["chip"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=lambda _: self.refresh(),
        )
        self._toggle.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        self._grid = ctk.CTkFrame(self, fg_color="transparent")
        self._grid.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")

        self._build_grid()

    def set_rule(self, max_num: int, min_pick: int) -> None:
        self._max_num = max_num
        self._min_pick = min_pick
        self._lbl_hint.configure(text=f"至少选择{min_pick}个")
        self._pick_menu.configure(values=[str(i) for i in range(min_pick, min(min_pick + 10, max_num) + 1)])
        if int(self._pick_count.get()) < min_pick:
            self._pick_count.set(str(min_pick))
        self._rebuild_grid()

    def _build_grid(self) -> None:
        cols = 11 if self._max_num >= 33 else 10
        btn_size = 42
        pad_x, pad_y = 10, 8
        for i in range(self._max_num):
            n = i + 1
            r = (i // cols) * 2
            c = i % cols
            cell = ctk.CTkFrame(self._grid, fg_color="transparent")
            cell.grid(row=r, column=c, padx=pad_x, pady=(0, 0))
            b = ctk.CTkButton(
                cell,
                text=f"{n:02d}",
                width=btn_size,
                height=btn_size,
                corner_radius=btn_size // 2,
                fg_color=COLORS["chip"],
                hover_color=COLORS["border"],
                text_color=COLORS["text"],
                command=lambda x=n: self._toggle_number(x),
            )
            b.grid(row=0, column=0)
            lbl = ctk.CTkLabel(cell, text="", font=ctk.CTkFont(size=11), text_color=COLORS["subtext"])
            lbl.grid(row=1, column=0, pady=(2, 0))
            self._buttons[n] = b
            self._sub_labels[n] = lbl
        self.refresh()

    def _rebuild_grid(self) -> None:
        for w in self._grid.winfo_children():
            w.destroy()
        self._buttons.clear()
        self._sub_labels.clear()
        self._build_grid()

    def _toggle_number(self, n: int) -> None:
        selected = set(self._get_selected())
        if n in selected:
            selected.remove(n)
        else:
            selected.add(n)
        self._set_selected(sorted(selected))
        self.refresh()
        self._on_change()

    def _random_pick(self) -> None:
        target = int(self._pick_count.get())
        if self._ball_type == "red":
            freqs = self._cache.analyzer.calculate_frequency("red", recent_n=200) if self._cache.analyzer else {}
        else:
            freqs = self._cache.analyzer.calculate_frequency("blue", recent_n=200) if self._cache.analyzer else {}

        nums = list(range(1, self._max_num + 1))
        weights = []
        total_freq = sum(freqs.values())
        for n in nums:
            w = 1.0 + (freqs.get(n, 0) / max(1, total_freq)) * 10.0
            weights.append(w)
        s = sum(weights)
        probs = [w / s for w in weights]
        picked = set()
        while len(picked) < min(target, len(nums)):
            picked.add(random.choices(nums, weights=probs, k=1)[0])
        self._set_selected(sorted(picked))
        self.refresh()
        self._on_change()

    def _clear(self) -> None:
        self._set_selected([])
        self.refresh()
        self._on_change()

    def refresh(self) -> None:
        selected = set(self._get_selected())
        show_mode = self._mode.get()
        omission = self._cache.omission_red if self._ball_type == "red" else self._cache.omission_blue
        hot_set = self._cache.hot_red if self._ball_type == "red" else self._cache.hot_blue
        for n, btn in self._buttons.items():
            is_sel = n in selected
            if is_sel:
                btn.configure(
                    fg_color=COLORS[self._color_key],
                    hover_color=COLORS[f"{self._color_key}_hover"],
                    text_color="#FFFFFF",
                )
            else:
                btn.configure(
                    fg_color=COLORS["chip"],
                    hover_color=COLORS["border"],
                    text_color=COLORS["text"],
                )

            if show_mode == "遗漏":
                v = omission.get(n, 0)
                self._sub_labels[n].configure(text=str(v), text_color=COLORS["danger"] if v >= 15 else COLORS["subtext"])
            else:
                self._sub_labels[n].configure(text="热" if n in hot_set else "", text_color=COLORS[self._color_key] if n in hot_set else COLORS["subtext"])


class DantuoPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        cache: DataCache,
        get_rule,
        get_red_dan,
        set_red_dan,
        get_red_tuo,
        set_red_tuo,
        get_blue,
        set_blue,
        on_change,
    ):
        super().__init__(master, fg_color="transparent")
        self._cache = cache
        self._get_rule = get_rule
        self._get_red_dan = get_red_dan
        self._set_red_dan = set_red_dan
        self._get_red_tuo = get_red_tuo
        self._set_red_tuo = set_red_tuo
        self._get_blue = get_blue
        self._set_blue = set_blue
        self._on_change = on_change
        self._mode = ctk.StringVar(value="遗漏")
        self._pick_mode = ctk.StringVar(value="胆码")

        self.grid_columnconfigure(0, weight=1)

        self._red_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self._red_card.grid(row=0, column=0, sticky="ew")
        self._red_card.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(self._red_card, fg_color="transparent")
        head.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="红球区（胆拖）", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, sticky="w"
        )
        self._red_hint = ctk.CTkLabel(head, text="", font=ctk.CTkFont(size=13), text_color=COLORS["subtext"])
        self._red_hint.grid(row=1, column=0, sticky="w", pady=(2, 0))

        right = ctk.CTkFrame(head, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=2, sticky="e")
        ctk.CTkButton(
            right,
            text="清空胆码",
            width=90,
            fg_color=COLORS["chip"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._clear_dan,
        ).grid(row=0, column=0, padx=(0, 10))
        ctk.CTkButton(
            right,
            text="清空拖码",
            width=90,
            fg_color=COLORS["chip"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._clear_tuo,
        ).grid(row=0, column=1, padx=(0, 10))
        ctk.CTkButton(
            right,
            text="清空全部",
            width=90,
            fg_color=COLORS["chip"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._clear_all,
        ).grid(row=0, column=2)

        self._toggle = ctk.CTkSegmentedButton(
            self._red_card,
            values=["遗漏", "热号"],
            variable=self._mode,
            selected_color=COLORS["red"],
            selected_hover_color=COLORS["red_hover"],
            fg_color=COLORS["chip"],
            unselected_color=COLORS["chip"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=lambda _: self.refresh(),
        )
        self._toggle.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        self._pick_toggle = ctk.CTkSegmentedButton(
            self._red_card,
            values=["胆码", "拖码"],
            variable=self._pick_mode,
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["primary_hover"],
            fg_color=COLORS["chip"],
            unselected_color=COLORS["chip"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self._pick_toggle.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="e")

        self._red_grid = ctk.CTkFrame(self._red_card, fg_color="transparent")
        self._red_grid.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")

        self._red_buttons: Dict[int, ctk.CTkButton] = {}
        self._red_sub: Dict[int, ctk.CTkLabel] = {}
        self._build_red_grid()

        self._blue_holder = ctk.CTkFrame(self, fg_color="transparent")
        self._blue_holder.grid(row=1, column=0, pady=(12, 0), sticky="ew")
        self._blue_holder.grid_columnconfigure(0, weight=1)
        self._blue_grid = BallGrid(
            self._blue_holder,
            title="蓝球区",
            max_num=16,
            min_pick=1,
            color_key="blue",
            cache=self._cache,
            ball_type="blue",
            get_pick_target=lambda: None,
            get_selected=self._get_blue,
            set_selected=self._set_blue,
            on_change=self._on_change,
        )
        self._blue_grid.grid(row=0, column=0, sticky="ew")

        self.refresh()

    def set_rule(self) -> None:
        rule = self._get_rule()
        self._blue_grid.set_rule(rule.blue_max, rule.blue_pick)
        self._rebuild_red_grid()
        self.refresh()

    def _build_red_grid(self) -> None:
        rule = self._get_rule()
        max_num = rule.red_max
        cols = 11 if max_num >= 33 else 10
        btn_size = 42
        for i in range(max_num):
            n = i + 1
            r = (i // cols) * 2
            c = i % cols
            cell = ctk.CTkFrame(self._red_grid, fg_color="transparent")
            cell.grid(row=r, column=c, padx=10, pady=(0, 0))
            b = ctk.CTkButton(
                cell,
                text=f"{n:02d}",
                width=btn_size,
                height=btn_size,
                corner_radius=btn_size // 2,
                fg_color=COLORS["chip"],
                hover_color=COLORS["border"],
                text_color=COLORS["text"],
                command=lambda x=n: self._toggle_red(x),
            )
            b.grid(row=0, column=0)
            lbl = ctk.CTkLabel(cell, text="", font=ctk.CTkFont(size=11), text_color=COLORS["subtext"])
            lbl.grid(row=1, column=0, pady=(2, 0))
            self._red_buttons[n] = b
            self._red_sub[n] = lbl

    def _rebuild_red_grid(self) -> None:
        for w in self._red_grid.winfo_children():
            w.destroy()
        self._red_buttons.clear()
        self._red_sub.clear()
        self._build_red_grid()

    def _toggle_red(self, n: int) -> None:
        dan = set(self._get_red_dan())
        tuo = set(self._get_red_tuo())
        rule = self._get_rule()

        if self._pick_mode.get() == "胆码":
            if n in dan:
                dan.remove(n)
            else:
                if n in tuo:
                    tuo.remove(n)
                if len(dan) >= rule.red_pick - 1:
                    messagebox.showwarning("提示", f"胆码最多 {rule.red_pick - 1} 个")
                    self.refresh()
                    return
                dan.add(n)
        else:
            if n in tuo:
                tuo.remove(n)
            else:
                if n in dan:
                    dan.remove(n)
                tuo.add(n)

        dan = dan - tuo
        tuo = tuo - dan
        self._set_red_dan(sorted(dan))
        self._set_red_tuo(sorted(tuo))
        self.refresh()
        self._on_change()

    def _clear_dan(self) -> None:
        self._set_red_dan([])
        self.refresh()
        self._on_change()

    def _clear_tuo(self) -> None:
        self._set_red_tuo([])
        self.refresh()
        self._on_change()

    def _clear_all(self) -> None:
        self._set_red_dan([])
        self._set_red_tuo([])
        self._set_blue([])
        self.refresh()
        self._on_change()

    def refresh(self) -> None:
        rule = self._get_rule()
        dan = set(self._get_red_dan())
        tuo = set(self._get_red_tuo())
        need_tuo = max(0, rule.red_pick - len(dan))
        self._red_hint.configure(text=f"胆码 1-{rule.red_pick - 1} 个，拖码至少 {need_tuo} 个")
        show_mode = self._mode.get()
        omission = self._cache.omission_red
        hot_set = self._cache.hot_red
        for n, btn in self._red_buttons.items():
            if n in dan:
                btn.configure(fg_color=COLORS["danger"], hover_color=COLORS["red_hover"], text_color="#FFFFFF")
            elif n in tuo:
                btn.configure(fg_color=COLORS["red"], hover_color=COLORS["red_hover"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=COLORS["chip"], hover_color=COLORS["border"], text_color=COLORS["text"])

            if show_mode == "遗漏":
                v = omission.get(n, 0)
                self._red_sub[n].configure(text=str(v), text_color=COLORS["danger"] if v >= 15 else COLORS["subtext"])
            else:
                self._red_sub[n].configure(text="热" if n in hot_set else "", text_color=COLORS["red"] if n in hot_set else COLORS["subtext"])


class TrendPanel(ctk.CTkFrame):
    def __init__(self, master, cache: DataCache, get_game_key):
        super().__init__(master, fg_color=COLORS["bg"])
        self._cache = cache
        self._get_game_key = get_game_key
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._left = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self._left.grid(row=0, column=0, padx=(0, 12), sticky="ns")
        self._right = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self._right.grid(row=0, column=1, sticky="nsew")
        self._right.grid_rowconfigure(0, weight=1)
        self._right.grid_columnconfigure(0, weight=1)

        self._chart_type = ctk.StringVar(value="综合分布图")
        self._btns: Dict[str, ctk.CTkButton] = {}
        items = [
            "综合分布图",
            "蓝球综合走势图",
            "红球和值走势图",
            "红球三区分布图",
        ]
        ctk.CTkLabel(self._left, text="走势图", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, padx=14, pady=(14, 10), sticky="w"
        )
        for idx, name in enumerate(items, start=1):
            b = ctk.CTkButton(
                self._left,
                text=name,
                fg_color=COLORS["chip"],
                hover_color=COLORS["border"],
                text_color=COLORS["text"],
                anchor="w",
                width=190,
                command=lambda x=name: self._select(x),
            )
            b.grid(row=idx, column=0, padx=14, pady=6, sticky="ew")
            self._btns[name] = b

        self._fig = Figure(figsize=(6.5, 4.5), dpi=100)
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._right)
        self._canvas.get_tk_widget().grid(row=0, column=0, padx=14, pady=14, sticky="nsew")

        self._select(items[0])

    def _select(self, name: str) -> None:
        self._chart_type.set(name)
        for n, b in self._btns.items():
            if n == name:
                b.configure(fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], text_color="#FFFFFF")
            else:
                b.configure(fg_color=COLORS["chip"], hover_color=COLORS["border"], text_color=COLORS["text"])
        self.render()

    def render(self) -> None:
        game_key = self._get_game_key()
        self._cache.load(game_key)
        df = self._cache.df
        self._ax.clear()
        if df is None or not len(df):
            self._ax.text(0.5, 0.5, "暂无数据", ha="center", va="center")
            self._canvas.draw()
            return

        chart = self._chart_type.get()
        tail_n = 80
        sub = df.tail(tail_n).copy()
        red_cols = [c for c in sub.columns if "红球" in c]
        blue_cols = [c for c in sub.columns if "蓝球" in c]
        x = list(range(len(sub)))

        if chart == "综合分布图":
            reds = sub[red_cols].values.flatten().astype(int)
            self._ax.hist(reds, bins=max(10, int(reds.max())), color="#1A73E8", alpha=0.9)
            self._ax.set_title("红球综合分布(近80期)")
            self._ax.set_xlabel("号码")
            self._ax.set_ylabel("出现次数")
        elif chart == "蓝球综合走势图":
            if not blue_cols:
                self._ax.text(0.5, 0.5, "该玩法无蓝球走势", ha="center", va="center")
            else:
                blue = sub[blue_cols].values[:, 0].astype(int)
                self._ax.plot(x, blue, color="#EA4335", linewidth=2)
                self._ax.set_title("蓝球走势图(近80期)")
                self._ax.set_xlabel("期序")
                self._ax.set_ylabel("蓝球")
        elif chart == "红球和值走势图":
            sums = sub[red_cols].sum(axis=1).astype(int).tolist()
            self._ax.plot(x, sums, color="#1A73E8", linewidth=2)
            self._ax.set_title("红球和值走势(近80期)")
            self._ax.set_xlabel("期序")
            self._ax.set_ylabel("和值")
        elif chart == "红球三区分布图":
            rule = GAME_RULES.get(game_key)
            if rule is None:
                self._ax.text(0.5, 0.5, "该玩法暂不支持三区分布", ha="center", va="center")
            else:
                cut1 = rule.red_max // 3
                cut2 = cut1 * 2
                rows = sub[red_cols].values.astype(int)
                a, b, c = [], [], []
                for row in rows:
                    a.append(int(((row >= 1) & (row <= cut1)).sum()))
                    b.append(int(((row > cut1) & (row <= cut2)).sum()))
                    c.append(int((row > cut2).sum()))
                self._ax.stackplot(x, a, b, c, labels=["一区", "二区", "三区"], colors=["#1A73E8", "#34A853", "#FBBC04"], alpha=0.9)
                self._ax.legend(loc="upper right")
                self._ax.set_title("红球三区分布(近80期)")
                self._ax.set_xlabel("期序")
                self._ax.set_ylabel("个数")

        self._ax.grid(True, alpha=0.25)
        self._fig.tight_layout()
        self._canvas.draw()


class TermsPanel(ctk.CTkFrame):
    def __init__(self, master, terms_path: str):
        super().__init__(master, fg_color=COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._terms_path = terms_path
        self._terms = self._load_terms()

        head = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        head.grid(row=0, column=0, sticky="ew")
        head.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(head, text="彩票术语", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, padx=14, pady=14, sticky="w"
        )
        self._q = ctk.StringVar(value="")
        self._search = ctk.CTkEntry(
            head,
            textvariable=self._q,
            placeholder_text="搜索术语，例如：胆拖、和值、振幅…",
            fg_color=COLORS["card"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self._search.grid(row=0, column=1, padx=(0, 14), pady=14, sticky="ew")
        self._search.bind("<KeyRelease>", lambda _: self._render())

        self._list = ctk.CTkScrollableFrame(self, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self._list.grid(row=1, column=0, pady=(12, 0), sticky="nsew")
        self._render()

    def _load_terms(self) -> List[Dict[str, str]]:
        if os.path.exists(self._terms_path):
            with open(self._terms_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _render(self) -> None:
        q = self._q.get().strip()
        for w in self._list.winfo_children():
            w.destroy()
        items = self._terms
        if q:
            items = [t for t in items if q in t.get("term", "") or q in t.get("desc", "")]
        for idx, t in enumerate(items):
            card = ctk.CTkFrame(self._list, fg_color="transparent")
            card.grid(row=idx, column=0, padx=14, pady=(10 if idx == 0 else 6, 6), sticky="ew")
            title = ctk.CTkLabel(card, text=t.get("term", ""), font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["text"])
            title.grid(row=0, column=0, sticky="w")
            desc = ctk.CTkLabel(
                card,
                text=t.get("desc", ""),
                font=ctk.CTkFont(size=13),
                text_color=COLORS["subtext"],
                wraplength=820,
                justify="left",
            )
            desc.grid(row=1, column=0, pady=(2, 0), sticky="w")


class PickerPanel(ctk.CTkFrame):
    def __init__(self, master, cache: DataCache, on_summary_change, get_game_key=None):
        super().__init__(master, fg_color=COLORS["bg"])
        self._cache = cache
        self._on_summary_change = on_summary_change
        self._game_display_to_key = {rule.name: key for key, rule in GAME_RULES.items()}
        self._game_key_to_display = {key: rule.name for key, rule in GAME_RULES.items()}

        self.red_selected: List[int] = []
        self.blue_selected: List[int] = []

        self.dt_red_dan: List[int] = []
        self.dt_red_tuo: List[int] = []
        self.dt_blue: List[int] = []

        self.my_tickets: List[Dict] = []
        self._sim_selected_ticket_idx: int = -1

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self._top = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self._top.grid(row=0, column=0, sticky="ew")
        self._top.grid_columnconfigure(2, weight=1)

        self._title = ctk.CTkLabel(self._top, text="选号", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"])
        self._title.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        self._warn = ctk.CTkLabel(
            self._top,
            text="模拟投注为虚拟玩法，切勿当真",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["danger"],
        )
        self._warn.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")

        self._issue = ctk.CTkLabel(self._top, text="", font=ctk.CTkFont(size=12), text_color=COLORS["subtext"])
        self._issue.grid(row=0, column=2, padx=14, pady=(12, 4), sticky="e")

        self._game_var = ctk.StringVar(value=self._game_key_to_display.get("ssq", "双色球"))
        self._game_menu = ctk.CTkOptionMenu(
            self._top,
            variable=self._game_var,
            values=[self._game_key_to_display[k] for k in ["ssq", "dlt", "qlc"] if k in self._game_key_to_display],
            fg_color=COLORS["chip"],
            text_color=COLORS["text"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
            width=90,
            command=lambda _: self._change_game(),
        )
        self._game_menu.grid(row=1, column=2, padx=14, pady=(0, 12), sticky="e")

        self._bet_mode = ctk.StringVar(value="普通投注")
        self._modes = ctk.CTkSegmentedButton(
            self._top,
            values=["普通投注", "胆拖投注", "AI选号", "模拟摇奖", "开奖信息"],
            variable=self._bet_mode,
            selected_color=COLORS["danger"],
            selected_hover_color=COLORS["danger"],
            fg_color=COLORS["chip"],
            unselected_color=COLORS["chip"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=lambda _: self._switch_mode(),
        )
        self._modes.grid(row=2, column=0, columnspan=3, padx=14, pady=(0, 14), sticky="ew")

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.grid(row=1, column=0, pady=(12, 0), sticky="nsew")
        self._body.grid_columnconfigure(0, weight=1)

        self._footer = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self._footer.grid(row=2, column=0, pady=(12, 12), sticky="ew")
        self._footer.grid_columnconfigure(0, weight=1)
        self._footer.grid_columnconfigure(1, weight=0)
        self._summary = ctk.CTkLabel(self._footer, text="", font=ctk.CTkFont(size=13), text_color=COLORS["text"])
        self._summary.grid(row=0, column=0, padx=14, pady=14, sticky="w")
        self._btn_done = ctk.CTkButton(
            self._footer,
            text="选好了",
            width=120,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color="#FFFFFF",
            command=self._done,
        )
        self._btn_done.grid(row=0, column=1, padx=14, pady=14, sticky="e")

        self._mode_frames: Dict[str, ctk.CTkFrame] = {}

        self._build_mode_common()
        self._change_game(initial=True)

    def get_game_key(self) -> str:
        display = self._game_var.get().strip()
        return self._game_display_to_key.get(display, "ssq")

    def _build_mode_common(self) -> None:
        for w in self._body.winfo_children():
            w.destroy()
        self._mode_frames.clear()

        for mode in ["普通投注", "胆拖投注", "AI选号", "模拟摇奖", "开奖信息"]:
            f = ctk.CTkFrame(self._body, fg_color="transparent")
            f.grid(row=0, column=0, sticky="nsew")
            self._mode_frames[mode] = f

        self._build_normal(self._mode_frames["普通投注"])
        self._build_dantuo(self._mode_frames["胆拖投注"])
        self._build_lucky(self._mode_frames["AI选号"])
        self._build_sim(self._mode_frames["模拟摇奖"])
        self._build_draw_info(self._mode_frames["开奖信息"])

        self._switch_mode()

    def _build_placeholder(self, frame: ctk.CTkFrame, text: str) -> None:
        card = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        card.pack(fill="both", expand=True)
        ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=14), text_color=COLORS["subtext"]).pack(padx=14, pady=14)

    def _build_draw_info(self, frame: ctk.CTkFrame) -> None:
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        left.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        right = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(left, fg_color="transparent")
        head.grid(row=0, column=0, padx=14, pady=(14, 10), sticky="ew")
        ctk.CTkLabel(head, text="开奖期号", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, sticky="w"
        )
        self._draw_refresh_btn = ctk.CTkButton(
            head,
            text="刷新",
            width=70,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color="#FFFFFF",
            command=self._refresh_draw_info,
        )
        self._draw_refresh_btn.grid(row=0, column=1, padx=(10, 0), sticky="e")

        self._draw_issue_list = ctk.CTkScrollableFrame(left, fg_color="transparent", width=210)
        self._draw_issue_list.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        left.grid_rowconfigure(1, weight=1)

        rhead = ctk.CTkFrame(right, fg_color="transparent")
        rhead.grid(row=0, column=0, padx=14, pady=(14, 10), sticky="ew")
        rhead.grid_columnconfigure(0, weight=1)
        self._draw_title = ctk.CTkLabel(rhead, text="开奖信息", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"])
        self._draw_title.grid(row=0, column=0, sticky="w")
        self._draw_hint = ctk.CTkLabel(rhead, text="数据来源：中彩网", font=ctk.CTkFont(size=12), text_color=COLORS["subtext"])
        self._draw_hint.grid(row=0, column=1, sticky="e")

        self._draw_detail = ctk.CTkTextbox(
            right,
            state="disabled",
            fg_color=COLORS["log_bg"],
            text_color=COLORS["log_fg"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self._draw_detail.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")

        self._draw_items: List = []
        self._draw_selected_issue: str = ""
        self._refresh_draw_info()

    def _refresh_draw_info(self) -> None:
        if getattr(self, "_draw_loading", False):
            return
        self._draw_loading = True
        self._draw_refresh_btn.configure(state="disabled", text="刷新中...")

        game = self.get_game_key()

        def job():
            try:
                items = fetch_draw_list(game, page_num=1, page_size=50)
                try:
                    if self.winfo_exists():
                        self.after(0, lambda: self._render_draw_issue_list(items))
                except Exception:
                    pass
            finally:
                self._draw_loading = False
                try:
                    if self.winfo_exists():
                        self.after(0, lambda: self._draw_refresh_btn.configure(state="normal", text="刷新"))
                except Exception:
                    pass

        threading.Thread(target=job, daemon=True).start()

    def _render_draw_issue_list(self, items) -> None:
        self._draw_items = items or []
        for w in self._draw_issue_list.winfo_children():
            w.destroy()
        if not self._draw_items:
            ctk.CTkLabel(self._draw_issue_list, text="暂无数据", text_color=COLORS["subtext"]).pack(padx=10, pady=10)
            return

        for i, item in enumerate(self._draw_items):
            issue = normalize_issue(item.issue)
            label = issue
            btn = ctk.CTkButton(
                self._draw_issue_list,
                text=label,
                fg_color=COLORS["chip"],
                hover_color=COLORS["border"],
                text_color=COLORS["text"],
                anchor="w",
                width=180,
                command=lambda x=issue: self._select_draw_issue(x),
            )
            btn.pack(fill="x", padx=6, pady=4)

        self._select_draw_issue(normalize_issue(self._draw_items[0].issue))

    def _select_draw_issue(self, issue: str) -> None:
        self._draw_selected_issue = issue
        item = None
        for it in self._draw_items:
            if normalize_issue(it.issue) == issue:
                item = it
                break
        if item is None:
            return

        title = f"{self._game_var.get()} 第{issue}期"
        open_date = format_open_time(item.open_time, item.week)
        reds = (item.front or "").strip()
        blues = (item.back or "").strip()

        lines = []
        lines.append(title)
        if open_date:
            lines.append(f"开奖日期: {open_date}")
        if reds:
            lines.append(f"红球: {reds}")
        if blues:
            lines.append(f"蓝球: {blues}")
        if item.sale_money:
            lines.append(f"销量: {item.sale_money}")
        if item.prize_pool_money:
            lines.append(f"奖池: {item.prize_pool_money}")

        if item.winner_details:
            lines.append("\n奖级信息:")
            for wd in item.winner_details:
                base = wd.get("baseBetWinner") or {}
                remark = base.get("remark") or wd.get("awardEtc")
                award_num = base.get("awardNum")
                award_money = base.get("awardMoney")
                if remark and award_num and award_money:
                    lines.append(f"- {remark}: {award_num} 注, {award_money} 元")

        self._draw_detail.configure(state="normal")
        self._draw_detail.delete("1.0", tk.END)
        self._draw_detail.insert(tk.END, "\n".join(lines))
        self._draw_detail.configure(state="disabled")

    def _build_normal(self, frame: ctk.CTkFrame) -> None:
        frame.grid_columnconfigure(0, weight=1)
        self._red_grid = BallGrid(
            frame,
            title="红球区",
            max_num=33,
            min_pick=6,
            color_key="red",
            cache=self._cache,
            ball_type="red",
            get_pick_target=lambda: None,
            get_selected=lambda: self.red_selected,
            set_selected=lambda xs: setattr(self, "red_selected", xs),
            on_change=self._update_summary,
        )
        self._red_grid.grid(row=0, column=0, sticky="ew")

        self._blue_grid = BallGrid(
            frame,
            title="蓝球区",
            max_num=16,
            min_pick=1,
            color_key="blue",
            cache=self._cache,
            ball_type="blue",
            get_pick_target=lambda: None,
            get_selected=lambda: self.blue_selected,
            set_selected=lambda xs: setattr(self, "blue_selected", xs),
            on_change=self._update_summary,
        )
        self._blue_grid.grid(row=1, column=0, pady=(12, 0), sticky="ew")

        self._prob_card = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self._prob_card.grid(row=2, column=0, pady=(12, 0), sticky="ew")
        self._prob_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self._prob_card, text="中奖概率(估算)", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, padx=14, pady=(12, 6), sticky="w"
        )
        self._prob_text = ctk.CTkLabel(
            self._prob_card,
            text="请选择号码后自动估算",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["subtext"],
            justify="left",
            wraplength=860,
        )
        self._prob_text.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")

    def _build_dantuo(self, frame: ctk.CTkFrame) -> None:
        frame.grid_columnconfigure(0, weight=1)
        self._dt_panel = DantuoPanel(
            frame,
            cache=self._cache,
            get_rule=lambda: GAME_RULES[self.get_game_key()],
            get_red_dan=lambda: self.dt_red_dan,
            set_red_dan=lambda xs: setattr(self, "dt_red_dan", xs),
            get_red_tuo=lambda: self.dt_red_tuo,
            set_red_tuo=lambda xs: setattr(self, "dt_red_tuo", xs),
            get_blue=lambda: self.dt_blue,
            set_blue=lambda xs: setattr(self, "dt_blue", xs),
            on_change=self._update_summary,
        )
        self._dt_panel.grid(row=0, column=0, sticky="ew")

    def _build_lucky(self, frame: ctk.CTkFrame) -> None:
        frame.grid_columnconfigure(0, weight=1)
        card = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, padx=14, pady=14, sticky="ew")
        top.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(top, text="AI选号", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, sticky="w"
        )

        self._lucky_strategy = ctk.StringVar(value="hybrid")
        ctk.CTkOptionMenu(
            top,
            variable=self._lucky_strategy,
            values=["hybrid", "model_only", "strategy_only"],
            fg_color=COLORS["chip"],
            text_color=COLORS["text"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
            width=140,
        ).grid(row=0, column=1, padx=(10, 0))

        self._lucky_count = ctk.StringVar(value="5")
        ctk.CTkOptionMenu(
            top,
            variable=self._lucky_count,
            values=[str(i) for i in range(1, 101)],
            fg_color=COLORS["chip"],
            text_color=COLORS["text"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
            width=90,
        ).grid(row=0, column=2, padx=(10, 0), sticky="e")

        self._lucky_fill_index = ctk.StringVar(value="1")
        ctk.CTkLabel(
            top,
            text="填充第",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["subtext"],
        ).grid(row=0, column=3, padx=(10, 0))
        self._lucky_fill_menu = ctk.CTkOptionMenu(
            top,
            variable=self._lucky_fill_index,
            values=["1"],
            fg_color=COLORS["chip"],
            text_color=COLORS["text"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
            width=90,
        )
        self._lucky_fill_menu.grid(row=0, column=4, padx=(6, 0))
        ctk.CTkLabel(
            top,
            text="组",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["subtext"],
        ).grid(row=0, column=5, padx=(6, 0))

        self._lucky_btn = ctk.CTkButton(
            top,
            text="生成推荐",
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color="#FFFFFF",
            command=self._run_lucky,
        )
        self._lucky_btn.grid(row=0, column=6, padx=(10, 0))

        self._lucky_fill_btn = ctk.CTkButton(
            top,
            text="填充到选号",
            fg_color=COLORS["chip"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._fill_selected_lucky,
        )
        self._lucky_fill_btn.grid(row=0, column=7, padx=(10, 0))

        self._lucky_log = ctk.CTkTextbox(
            card,
            state="disabled",
            height=260,
            fg_color=COLORS["log_bg"],
            text_color=COLORS["log_fg"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self._lucky_log.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")

        self._lucky_last: List[Dict] = []

    def _build_sim(self, frame: ctk.CTkFrame) -> None:
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="我的选号", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, padx=14, pady=(14, 8), sticky="w"
        )
        self._my_ticket_list = ctk.CTkScrollableFrame(left, fg_color="transparent", width=260)
        self._my_ticket_list.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        right = ctk.CTkFrame(frame, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(right, text="模拟摇奖", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, padx=14, pady=(14, 6), sticky="w"
        )
        self._sim_text = ctk.CTkLabel(
            right,
            text="随机摇出一注，并与‘我的选号’中选中的一注对比（仅供娱乐）",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["subtext"],
        )
        self._sim_text.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="w")

        self._sim_btn = ctk.CTkButton(
            right,
            text="开始摇奖",
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger"],
            text_color="#FFFFFF",
            command=self._simulate_draw,
        )
        self._sim_btn.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")

        self._sim_log = ctk.CTkTextbox(
            right,
            state="disabled",
            height=260,
            fg_color=COLORS["log_bg"],
            text_color=COLORS["log_fg"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self._sim_log.grid(row=3, column=0, padx=14, pady=(0, 14), sticky="nsew")

        self._render_my_ticket_list()

    def _render_my_ticket_list(self) -> None:
        if not hasattr(self, "_my_ticket_list"):
            return
        for w in self._my_ticket_list.winfo_children():
            w.destroy()
        if not self.my_tickets:
            ctk.CTkLabel(self._my_ticket_list, text="暂无选号\n在普通投注/胆拖投注点‘选好了’或AI选号填充即可加入", text_color=COLORS["subtext"], justify="left").pack(
                padx=10, pady=10, anchor="w"
            )
            return

        for idx, t in enumerate(self.my_tickets):
            active = idx == self._sim_selected_ticket_idx
            title = f"{t.get('game_name','')} · {t.get('mode','')}"
            red = " ".join([f"{int(x):02d}" for x in t.get('red', [])])
            blue_list = t.get('blue', [])
            if isinstance(blue_list, list):
                blue = " ".join([f"{int(x):02d}" for x in blue_list])
            else:
                blue = str(blue_list)

            btn = ctk.CTkButton(
                self._my_ticket_list,
                text=f"{title}\n红: {red}\n蓝: {blue}",
                fg_color=COLORS["primary"] if active else COLORS["chip"],
                hover_color=COLORS["primary_hover"] if active else COLORS["border"],
                text_color="#FFFFFF" if active else COLORS["text"],
                corner_radius=10,
                anchor="w",
                height=64,
                command=lambda i=idx: self._select_my_ticket(i),
            )
            btn.pack(fill="x", padx=6, pady=6)

    def _select_my_ticket(self, idx: int) -> None:
        self._sim_selected_ticket_idx = idx
        self._render_my_ticket_list()

    def _add_my_ticket(self, *, game_key: str, mode: str, red: List[int], blue: List[int]) -> None:
        rule = GAME_RULES.get(game_key)
        if rule is None:
            return
        ticket = {
            "game_key": game_key,
            "game_name": rule.name,
            "mode": mode,
            "red": sorted([int(x) for x in red]),
            "blue": sorted([int(x) for x in blue]),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.my_tickets.insert(0, ticket)
        self._sim_selected_ticket_idx = 0
        self._render_my_ticket_list()

    def _get_ticket_for_sim(self) -> Optional[Dict]:
        if 0 <= self._sim_selected_ticket_idx < len(self.my_tickets):
            return self.my_tickets[self._sim_selected_ticket_idx]
        game_key = self.get_game_key()
        rule = GAME_RULES.get(game_key)
        if rule is None:
            return None
        if len(self.red_selected) >= rule.red_pick and len(self.blue_selected) >= rule.blue_pick:
            return {
                "game_key": game_key,
                "game_name": rule.name,
                "mode": "普通投注",
                "red": sorted(self.red_selected),
                "blue": sorted(self.blue_selected),
            }
        return None

    def _exact_match_prob(self, rule: GameRule, hit_red: int, hit_blue: int) -> float:
        total_red = comb(rule.red_max, rule.red_pick)
        total_blue = comb(rule.blue_max, rule.blue_pick)
        p_red = comb(rule.red_pick, hit_red) * comb(rule.red_max - rule.red_pick, rule.red_pick - hit_red) / max(1, total_red)
        p_blue = comb(rule.blue_pick, hit_blue) * comb(rule.blue_max - rule.blue_pick, rule.blue_pick - hit_blue) / max(1, total_blue)
        return float(p_red) * float(p_blue)

    def _write_box(self, box: ctk.CTkTextbox, text: str, clear: bool = False) -> None:
        box.configure(state="normal")
        if clear:
            box.delete("1.0", tk.END)
        box.insert(tk.END, text)
        box.see(tk.END)
        box.configure(state="disabled")

    def _run_lucky(self) -> None:
        if getattr(self, "_lucky_running", False):
            return
        self._lucky_running = True
        self._lucky_btn.configure(state="disabled", text="生成中...")
        self._write_box(self._lucky_log, "", clear=True)
        self._write_box(self._lucky_log, "开始生成AI选号...\n")

        game = self.get_game_key()
        if game == "fc3d":
            self._write_box(self._lucky_log, "福彩3D暂不支持AI选号面板\n")
            self._lucky_running = False
            self._lucky_btn.configure(state="normal", text="生成推荐")
            return

        def job():
            try:
                def ui(msg: str) -> None:
                    self.after(0, lambda m=msg: self._write_box(self._lucky_log, m))

                strategy = self._lucky_strategy.get().strip()
                count = int(self._lucky_count.get())

                ui(f"策略: {strategy}，目标组数: {count}\n")
                ui("加载历史数据...\n")

                self._cache.load(game)
                df = self._cache.df
                if df is None or not len(df):
                    ui("暂无历史数据\n")
                    return
                from core.strategies import LotteryStrategy
                from services.predict_service import PredictService

                ui(f"历史数据: {len(df)} 期，最新期号: {self._cache.latest_issue}\n")

                strategy_engine = LotteryStrategy(df)
                ui("计算号码推荐池...\n")
                recommendation = strategy_engine.recommend_balls(strategy='hybrid')
                combos: List[Dict] = []

                ui(f"候选池: 红球{len(recommendation.get('red_candidates', []))}个，蓝球{len(recommendation.get('blue_candidates', []))}个\n")

                if strategy == 'strategy_only':
                    ui("使用统计算法生成组合...\n")
                    combos = strategy_engine.generate_combinations(
                        recommendation['red_candidates'],
                        recommendation['blue_candidates'],
                        n_combinations=count,
                    )
                    combos = strategy_engine.smart_filter(combos)
                else:
                    ui("加载模型并预测...（首次可能较慢）\n")
                    windows_size = model_args[game]["model_args"]["windows_size"]
                    features = df.iloc[:windows_size]
                    with PredictService(game) as service:
                        model_pred = service.get_final_prediction(features)
                    ui(f"模型预测: 红球 {sorted(model_pred.get('red', []))} + 蓝球 {model_pred.get('blue')}\n")
                    if strategy == 'model_only':
                        if isinstance(model_pred.get('blue'), list):
                            blue = model_pred['blue']
                        else:
                            blue = [int(model_pred['blue'])]
                        combos = [{"red": sorted(model_pred['red']), "blue": blue[0] if len(blue) == 1 else blue}]
                    else:
                        ui("混合策略：融合模型预测与统计候选池...\n")
                        red_pool = list(set(model_pred['red'] + recommendation['red_candidates'][:12]))
                        blue_candidates = recommendation['blue_candidates']
                        if isinstance(model_pred.get('blue'), int):
                            blue_pool = list(set([int(model_pred['blue'])] + blue_candidates[:max(3, model_args[game]["model_args"].get('blue_sequence_len', 1))]))
                        else:
                            blue_pool = list(set(model_pred.get('blue', []) + blue_candidates[:max(3, model_args[game]["model_args"].get('blue_sequence_len', 1))]))
                        ui(f"融合后候选池: 红球{len(red_pool)}个，蓝球{len(blue_pool)}个\n")
                        combos = strategy_engine.generate_combinations(red_pool, blue_pool, n_combinations=count)
                        combos = strategy_engine.smart_filter(combos)

                def _combo_key(c: Dict) -> tuple:
                    r = tuple(sorted([int(x) for x in (c.get('red') or [])]))
                    b = c.get('blue')
                    if isinstance(b, list):
                        bb = tuple(sorted([int(x) for x in b]))
                    elif b is None:
                        bb = tuple()
                    else:
                        bb = (int(b),)
                    return (r, bb)

                if len(combos) < count:
                    ui(f"组合不足({len(combos)}/{count})，补足生成...\n")
                    seen = {_combo_key(c) for c in combos}
                    fallback_rounds = 0
                    while len(combos) < count and fallback_rounds < 20:
                        need = count - len(combos)
                        extra = strategy_engine.generate_combinations(
                            recommendation['red_candidates'],
                            recommendation['blue_candidates'],
                            n_combinations=max(need, 10),
                        )
                        for c in extra:
                            k = _combo_key(c)
                            if k in seen:
                                continue
                            seen.add(k)
                            combos.append(c)
                            if len(combos) >= count:
                                break
                        fallback_rounds += 1

                if not combos:
                    ui("过滤条件过严，回退到未过滤组合...\n")
                    combos = strategy_engine.generate_combinations(
                        recommendation['red_candidates'],
                        recommendation['blue_candidates'],
                        n_combinations=count,
                    )

                self._lucky_last = combos
                try:
                    max_idx = min(100, max(1, min(count, len(combos))))
                    values = [str(i) for i in range(1, max_idx + 1)]
                    self.after(0, lambda v=values: self._lucky_fill_menu.configure(values=v))
                    self.after(0, lambda: self._lucky_fill_index.set("1"))
                except Exception:
                    pass
                lines = ["\n结果：\n"]
                for i, c in enumerate(combos[: max(1, min(count, len(combos)))], 1):
                    lines.append(f"组合{i}: 红球 {c.get('red')} + 蓝球 {c.get('blue')}")
                ui("\n".join(lines) + "\n")
            except Exception as e:
                msg = f"\n生成失败: {e}\n"
                self.after(0, lambda m=msg: self._write_box(self._lucky_log, m))
            finally:
                self._lucky_running = False
                self.after(0, lambda: self._lucky_btn.configure(state="normal", text="生成推荐"))

        threading.Thread(target=job, daemon=True).start()

    def _fill_selected_lucky(self) -> None:
        if not getattr(self, "_lucky_last", None):
            messagebox.showinfo("提示", "请先生成推荐组合")
            return
        try:
            idx = int((self._lucky_fill_index.get() or "1").strip()) - 1
        except Exception:
            idx = 0
        idx = max(0, min(idx, len(self._lucky_last) - 1))
        combo = self._lucky_last[idx]

        self.red_selected = sorted([int(x) for x in combo.get('red', [])])
        b = combo.get('blue')
        if isinstance(b, list):
            self.blue_selected = sorted([int(x) for x in b])
        elif b is None:
            self.blue_selected = []
        else:
            self.blue_selected = [int(b)]

        self._bet_mode.set("普通投注")
        self._switch_mode()
        self._red_grid.refresh()
        self._blue_grid.refresh()
        self._update_summary()
        game_key = self.get_game_key()
        self._add_my_ticket(game_key=game_key, mode="AI选号", red=self.red_selected, blue=self.blue_selected)

    def _simulate_draw(self) -> None:
        ticket = self._get_ticket_for_sim()
        if ticket is None:
            messagebox.showinfo("提示", "请先在‘我的选号’中选择一注，或在普通投注选好后点‘选好了’保存。")
            return

        game = ticket.get("game_key")
        rule = GAME_RULES.get(game)
        if rule is None:
            return

        my_red = sorted([int(x) for x in ticket.get("red", [])])
        my_blue = sorted([int(x) for x in ticket.get("blue", [])])
        draw_red = sorted(random.sample(range(1, rule.red_max + 1), rule.red_pick))
        draw_blue = sorted(random.sample(range(1, rule.blue_max + 1), rule.blue_pick))
        hit_red = len(set(draw_red) & set(my_red))
        hit_blue = len(set(draw_blue) & set(my_blue))

        prob = self._exact_match_prob(rule, hit_red, hit_blue)
        grade = ""
        if game == "ssq":
            if hit_red == 6 and hit_blue == 1:
                grade = "一等奖"
            elif hit_red == 6 and hit_blue == 0:
                grade = "二等奖"
            elif hit_red == 5 and hit_blue == 1:
                grade = "三等奖"
            elif (hit_red == 5 and hit_blue == 0) or (hit_red == 4 and hit_blue == 1):
                grade = "四等奖"
            elif (hit_red == 4 and hit_blue == 0) or (hit_red == 3 and hit_blue == 1):
                grade = "五等奖"
            elif hit_blue == 1 and hit_red <= 2:
                grade = "六等奖"
            else:
                grade = "未中奖"

        text = ""
        text += f"使用号码: {ticket.get('game_name','')} · {ticket.get('mode','')}\n"
        text += f"我的选号: 红球 {my_red} + 蓝球 {my_blue}\n"
        text += f"摇奖结果: 红球 {draw_red} + 蓝球 {draw_blue}\n"
        text += f"命中情况: 红球 {hit_red} 个, 蓝球 {hit_blue} 个\n"
        if grade:
            text += f"奖级判断: {grade}\n"
        text += f"该命中组合理论概率(随机一注): {prob * 100:.6f}%\n\n"

        self._write_box(self._sim_log, text, clear=True)

    def _switch_mode(self) -> None:
        mode = self._bet_mode.get()
        for name, frame in self._mode_frames.items():
            frame.grid_remove()
            frame.pack_forget()
            frame.place_forget()
        self._mode_frames[mode].grid(row=0, column=0, sticky="nsew")

    def _change_game(self, initial: bool = False) -> None:
        game_key = self.get_game_key()
        self._cache.load(game_key)
        rule = GAME_RULES[game_key]
        sale_issue, sale_date = _calc_current_sale_issue(self._cache.latest_issue, self._cache.latest_date, rule)
        date_str = (sale_date or "").strip()
        if date_str:
            self._issue.configure(text=f"第{sale_issue}期  {date_str}  {rule.close_time}截止")
        else:
            self._issue.configure(text=f"第{sale_issue}期  {rule.close_time}截止")

        self.red_selected = []
        self.blue_selected = []
        self.dt_red_dan = []
        self.dt_red_tuo = []
        self.dt_blue = []
        self._red_grid.set_rule(rule.red_max, rule.red_pick)
        self._blue_grid.set_rule(rule.blue_max, rule.blue_pick)
        if hasattr(self, "_dt_panel"):
            self._dt_panel.set_rule()
        self._update_summary()
        if not initial:
            self._switch_mode()

    def _update_summary(self) -> None:
        game_key = self.get_game_key()
        rule = GAME_RULES.get(game_key)
        if rule is None:
            self._summary.configure(text="")
            return

        mode = self._bet_mode.get()
        if mode == "胆拖投注":
            dan_n = len(self.dt_red_dan)
            tuo_n = len(self.dt_red_tuo)
            blue_n = len(self.dt_blue)
            need_tuo = max(0, rule.red_pick - dan_n)
            red_bets = comb(tuo_n, need_tuo) if 1 <= dan_n <= (rule.red_pick - 1) and tuo_n >= need_tuo else 0
            blue_bets = comb(blue_n, rule.blue_pick) if blue_n >= rule.blue_pick else 0
            bets = red_bets * blue_bets
            cost = bets * rule.cost_per_bet
            self._summary.configure(text=f"胆码{dan_n}个，拖码{tuo_n}个，蓝球{blue_n}个，共{bets}注，共{cost}元")
            self._prob_text.configure(text="胆拖投注暂不提供奖级概率估算")
            self._on_summary_change()
            return

        red_n = len(self.red_selected)
        blue_n = len(self.blue_selected)
        bets = comb(red_n, rule.red_pick) * comb(blue_n, rule.blue_pick)
        cost = bets * rule.cost_per_bet
        self._summary.configure(text=f"您选择了{red_n}个红球，{blue_n}个蓝球，共{bets}注，共{cost}元")

        self._update_prob(rule)
        self._on_summary_change()

    def _update_prob(self, rule: GameRule) -> None:
        if rule.key != "ssq":
            self._prob_text.configure(text="当前仅对双色球提供奖级概率估算（其他玩法会逐步补齐）。")
            return
        if len(self.red_selected) == 0 or len(self.blue_selected) == 0:
            self._prob_text.configure(text="请选择号码后自动估算")
            return
        if self._cache.analyzer is None:
            self._prob_text.configure(text="暂无历史数据，无法估算")
            return

        res = estimate_ssq_prize_prob(self.red_selected, self.blue_selected, self._cache.analyzer, rule)
        lines = []
        for k, v in res.items():
            lines.append(f"{k}: {v * 100:.4f}%")
        lines.append("注：基于历史频率的独立近似估算，仅供娱乐。")
        self._prob_text.configure(text="\n".join(lines))

    def _done(self) -> None:
        game_key = self.get_game_key()
        rule = GAME_RULES.get(game_key)
        if rule is None:
            return

        mode = self._bet_mode.get()
        if mode == "胆拖投注":
            dan_n = len(self.dt_red_dan)
            tuo_n = len(self.dt_red_tuo)
            blue_n = len(self.dt_blue)
            need_tuo = max(0, rule.red_pick - dan_n)
            if not (1 <= dan_n <= (rule.red_pick - 1) and tuo_n >= need_tuo and blue_n >= rule.blue_pick):
                messagebox.showwarning("提示", f"胆码需 1-{rule.red_pick - 1} 个，拖码至少 {need_tuo} 个，蓝球至少 {rule.blue_pick} 个")
                return
            dan = " ".join([f"{x:02d}" for x in sorted(self.dt_red_dan)])
            tuo = " ".join([f"{x:02d}" for x in sorted(self.dt_red_tuo)])
            blue = " ".join([f"{x:02d}" for x in sorted(self.dt_blue)])
            messagebox.showinfo("已选择（胆拖）", f"胆码: {dan}\n拖码: {tuo}\n蓝球: {blue}")
            self._add_my_ticket(game_key=game_key, mode="胆拖投注", red=sorted(set(self.dt_red_dan + self.dt_red_tuo)), blue=self.dt_blue)
            return

        if len(self.red_selected) < rule.red_pick or len(self.blue_selected) < rule.blue_pick:
            messagebox.showwarning("提示", f"至少选择{rule.red_pick}个红球和{rule.blue_pick}个蓝球")
            return
        red = " ".join([f"{x:02d}" for x in sorted(self.red_selected)])
        blue = " ".join([f"{x:02d}" for x in sorted(self.blue_selected)])
        messagebox.showinfo("已选择", f"红球: {red}\n蓝球: {blue}")
        self._add_my_ticket(game_key=game_key, mode="普通投注", red=self.red_selected, blue=self.blue_selected)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI 彩票预测系统 v3.0")
        self.geometry("1060x760")
        self.minsize(980, 700)
        self.configure(fg_color=COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._cache = DataCache()

        header = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=14, border_width=1, border_color=COLORS["border"])
        header.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="选号系统", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, padx=14, pady=14, sticky="w"
        )
        ctk.CTkLabel(header, text="数据来源：中彩网/福彩官方接口（仅供学习娱乐）", font=ctk.CTkFont(size=12), text_color=COLORS["subtext"]).grid(
            row=0, column=1, padx=14, pady=14, sticky="e"
        )

        self._tabs = ctk.CTkTabview(self, fg_color=COLORS["bg"], segmented_button_fg_color=COLORS["chip"], segmented_button_selected_color=COLORS["primary"], segmented_button_selected_hover_color=COLORS["primary_hover"], segmented_button_unselected_color=COLORS["chip"], segmented_button_unselected_hover_color=COLORS["border"], text_color=COLORS["text"])
        self._tabs.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

        tab_picker = self._tabs.add("选号")
        tab_trend = self._tabs.add("走势图")
        tab_terms = self._tabs.add("术语")

        self._current_game_for_trend = "ssq"

        self._picker = PickerPanel(tab_picker, self._cache, on_summary_change=lambda: None)
        self._picker.pack(fill="both", expand=True)

        self._trend = TrendPanel(tab_trend, self._cache, get_game_key=lambda: self._picker.get_game_key())
        self._trend.pack(fill="both", expand=True)

        terms_path = os.path.join(os.path.dirname(__file__), "data", "lottery_terms.json")
        self._terms = TermsPanel(tab_terms, terms_path=terms_path)
        self._terms.pack(fill="both", expand=True)


def main():
    app = App()
    try:
        if os.path.exists("icon.ico"):
            app.iconbitmap("icon.ico")
    except Exception:
        pass
    app.mainloop()


if __name__ == "__main__":
    main()
