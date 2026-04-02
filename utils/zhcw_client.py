import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


LOTTERY_ID = {
    "ssq": "1",
    "fc3d": "2",
    "qlc": "3",
    "dlt": "281",
}


WEEK_CN_MAP = {
    "星期一": "一",
    "星期二": "二",
    "星期三": "三",
    "星期四": "四",
    "星期五": "五",
    "星期六": "六",
    "星期日": "日",
    "星期天": "日",
}


@dataclass(frozen=True)
class DrawItem:
    issue: str
    open_time: str
    week: str
    front: str
    back: str
    prize_pool_money: str
    sale_money: str
    winner_details: List[Dict[str, Any]]
    raw: Dict[str, Any]


def _parse_jsonp(text: str) -> Dict[str, Any]:
    m = re.search(r"^[^(]*\((\{.*\})\)\s*$", text, flags=re.S)
    if m:
        return json.loads(m.group(1))
    return json.loads(text)


def fetch_draw_list(game_key: str, page_num: int = 1, page_size: int = 30) -> List[DrawItem]:
    lottery_id = LOTTERY_ID.get(game_key)
    if not lottery_id:
        return []

    url = "https://jc.zhcw.com/port/client_json.php"
    params = {
        "transactionType": "10001001",
        "lotteryId": lottery_id,
        "issueCount": str(page_size),
        "startIssue": "",
        "endIssue": "",
        "startDate": "",
        "endDate": "",
        "type": "1",
        "pageNum": str(page_num),
        "pageSize": str(page_size),
        "tt": "0.1",
        "callback": "cb",
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://www.zhcw.com/kjxx/{game_key}/kjxq/",
    }
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    payload = _parse_jsonp(r.text)
    if payload.get("resCode") != "000000":
        return []
    rows = payload.get("data") or []
    items: List[DrawItem] = []
    for row in rows:
        issue = str(row.get("issue") or "")
        open_time = str(row.get("openTime") or "")
        week = str(row.get("week") or "")
        front = str(row.get("frontWinningNum") or "")
        back = str(row.get("backWinningNum") or "")
        prize_pool_money = str(row.get("prizePoolMoney") or "")
        sale_money = str(row.get("saleMoney") or "")
        winner_details = row.get("winnerDetails") or []
        items.append(
            DrawItem(
                issue=issue,
                open_time=open_time,
                week=week,
                front=front,
                back=back,
                prize_pool_money=prize_pool_money,
                sale_money=sale_money,
                winner_details=winner_details,
                raw=row,
            )
        )
    return items


def normalize_issue(issue: str) -> str:
    s = str(issue).strip()
    if s.isdigit() and len(s) == 5:
        return "20" + s
    return s


def format_open_time(open_time: str, week: str = "") -> str:
    s = (open_time or "").strip()
    if not s:
        return ""
    try:
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        cn = WEEK_CN_MAP.get(week, "")
        if cn:
            return f"{dt.strftime('%Y-%m-%d')}({cn})"
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return s

