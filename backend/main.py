"""Ranksyar (Wranx Iran) API: microlearning, spaced repetition, gamification and manager analytics."""
import csv
import io
import json
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import Cookie, Depends, FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

import db
import srs

BADGES = ["first_steps", "streak_3", "streak_7", "xp_500", "track_master"]


@asynccontextmanager
async def lifespan(_):
    if db.init():
        con = db.connect()
        with con:
            for (uid,) in con.execute("SELECT id FROM users").fetchall():
                award(con, uid)
        con.close()
    yield


app = FastAPI(title="Ranksyar API", lifespan=lifespan)
L = json.loads


def get_db():
    con = db.connect()
    try:
        yield con
    finally:
        con.close()


def current_user(session: str = Cookie(""), con=Depends(get_db)):
    row = con.execute("SELECT u.* FROM tokens t JOIN users u ON u.id = t.user_id WHERE t.token = ?", (session,)).fetchone()
    if not row:
        raise HTTPException(401, "unauthorized")
    return row


def manager(u=Depends(current_user)):
    if u["role"] != "manager":
        raise HTTPException(403, "managers only")
    return u


def today():
    return date.today()


def ago(n):
    return (today() - timedelta(n)).isoformat()


def active_days(con, uid):
    return {date.fromisoformat(r[0]) for r in con.execute("SELECT DISTINCT day FROM answers WHERE user_id=?", (uid,))}


def track_mastery(con, uid):
    """Per-track mastery = sum of Leitner boxes / (max box * questions)."""
    rows = con.execute("""SELECT l.track_id, COUNT(q.id) n, COALESCE(SUM(r.box), 0) s, COUNT(r.box) seen
        FROM questions q JOIN lessons l ON l.id = q.lesson_id
        LEFT JOIN reviews r ON r.question_id = q.id AND r.user_id = ? GROUP BY l.track_id""", (uid,))
    return {r["track_id"]: {"mastery": r["s"] / (srs.MAX_BOX * r["n"]), "seen": r["seen"], "total": r["n"]} for r in rows}


def total_xp(con, uid, since="0000"):
    return con.execute("SELECT COALESCE(SUM(xp), 0) FROM answers WHERE user_id=? AND day>=?", (uid, since)).fetchone()[0]


def award(con, uid):
    xp, streak = total_xp(con, uid), srs.streak(active_days(con, uid), today())
    best = max((t["mastery"] for t in track_mastery(con, uid).values()), default=0)
    answered = con.execute("SELECT 1 FROM answers WHERE user_id=? LIMIT 1", (uid,)).fetchone()
    earned = {"first_steps": bool(answered), "streak_3": streak >= 3, "streak_7": streak >= 7,
              "xp_500": xp >= 500, "track_master": best >= 0.8}
    have = {r[0] for r in con.execute("SELECT code FROM badges WHERE user_id=?", (uid,))}
    new = [c for c in BADGES if earned[c] and c not in have]
    con.executemany("INSERT INTO badges VALUES(?,?,?)", [(uid, c, today().isoformat()) for c in new])
    return new


def public_user(u):
    return {"id": u["id"], "name": L(u["name"]), "email": u["email"], "role": u["role"]}


# ---------- auth ----------
class Login(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)


@app.post("/api/auth/login")
def login(body: Login, response: Response, con=Depends(get_db)):
    u = con.execute("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),)).fetchone()
    if not u or not db.check_pw(body.password, u["pw"]):
        raise HTTPException(401, "invalid_credentials")
    token = secrets.token_urlsafe(32)
    with con:
        con.execute("INSERT INTO tokens VALUES(?,?)", (token, u["id"]))
    # httpOnly session cookie: JS never sees the token; SameSite=Lax blocks cross-site POSTs
    response.set_cookie("session", token, max_age=30 * 86400, httponly=True, samesite="lax")
    return {"user": public_user(u)}


@app.post("/api/auth/logout")
def logout(response: Response, session: str = Cookie(""), con=Depends(get_db)):
    with con:
        con.execute("DELETE FROM tokens WHERE token=?", (session,))
    response.delete_cookie("session")
    return {"ok": True}


# ---------- learner ----------
@app.get("/api/me")
def me(u=Depends(current_user), con=Depends(get_db)):
    uid, xp = u["id"], total_xp(con, u["id"])
    lvl, progress = srs.level(xp)
    week = dict(con.execute("SELECT day, SUM(xp) FROM answers WHERE user_id=? AND day>=? GROUP BY day", (uid, ago(6))).fetchall())
    team = con.execute("SELECT name FROM teams WHERE id=?", (u["team_id"],)).fetchone()
    badges = dict(con.execute("SELECT code, day FROM badges WHERE user_id=?", (uid,)).fetchall())
    ranking = [r[0] for r in con.execute(
        "SELECT u.id FROM users u LEFT JOIN answers a ON a.user_id=u.id AND a.day>=? GROUP BY u.id ORDER BY COALESCE(SUM(a.xp),0) DESC",
        (ago(6),))]
    return {
        **public_user(u), "team": L(team["name"]) if team else None,
        "xp": xp, "level": lvl, "level_progress": progress, "level_xp": srs.LEVEL_XP,
        "streak": srs.streak(active_days(con, uid), today()),
        "today_xp": week.get(today().isoformat(), 0), "daily_goal": srs.DAILY_GOAL,
        "week": [week.get(ago(i), 0) for i in range(6, -1, -1)],
        "due": con.execute("SELECT COUNT(*) FROM reviews WHERE user_id=? AND due<=?", (uid, today().isoformat())).fetchone()[0],
        "rank": ranking.index(uid) + 1, "rank_of": len(ranking),
        "badges": [{"code": c, "day": badges.get(c)} for c in BADGES],
    }


@app.get("/api/tracks")
def tracks(u=Depends(current_user), con=Depends(get_db)):
    m = track_mastery(con, u["id"])
    rows = con.execute("SELECT t.*, COUNT(l.id) lessons, SUM(l.minutes) minutes FROM tracks t JOIN lessons l ON l.track_id=t.id GROUP BY t.id ORDER BY t.pos")
    return [{"id": r["id"], "title": L(r["title"]), "descr": L(r["descr"]), "color": r["color"], "icon": r["icon"],
             "lessons": r["lessons"], "minutes": r["minutes"], **m[r["id"]]} for r in rows]


def question_out(q, review):
    return {"type": "question", "id": q["id"], "track": q["track_id"], "prompt": L(q["prompt"]),
            "choices": L(q["choices"]), "review": review}  # the answer index never leaves the server


@app.get("/api/session")
def session(track: str | None = None, u=Depends(current_user), con=Depends(get_db)):
    """Today's session: due reviews first, then new material (lesson card before its first question)."""
    uid, tf, ta = u["id"], "AND l.track_id=?" if track else "", (track,) if track else ()
    base = "SELECT q.*, l.track_id, l.id lid FROM questions q JOIN lessons l ON l.id=q.lesson_id JOIN tracks t ON t.id=l.track_id"
    due = con.execute(f"{base} JOIN reviews r ON r.question_id=q.id AND r.user_id=? WHERE r.due<=? {tf} ORDER BY r.due, r.box LIMIT 6",
                      (uid, today().isoformat(), *ta)).fetchall()
    new = con.execute(f"{base} WHERE q.id NOT IN (SELECT question_id FROM reviews WHERE user_id=?) {tf} ORDER BY t.pos, l.pos, q.id LIMIT ?",
                      (uid, *ta, 8 - len(due))).fetchall()
    items, shown = [question_out(q, True) for q in due], set()
    for q in new:
        if q["lid"] not in shown:
            shown.add(q["lid"])
            les = con.execute("SELECT * FROM lessons WHERE id=?", (q["lid"],)).fetchone()
            items.append({"type": "lesson", "id": les["id"], "track": les["track_id"], "title": L(les["title"]),
                          "body": L(les["body"]), "minutes": les["minutes"]})
        items.append(question_out(q, False))
    practice = not items
    if practice:  # all caught up: extra practice on the weakest cards (no XP farming, see /answers)
        items = [question_out(q, True) for q in con.execute(
            f"{base} JOIN reviews r ON r.question_id=q.id AND r.user_id=? WHERE 1 {tf} ORDER BY r.box, RANDOM() LIMIT 5",
            (uid, *ta))]
    return {"items": items, "practice": practice}


class Answer(BaseModel):
    question_id: int
    choice: int = Field(ge=0, le=3)


@app.post("/api/answers")
def answer(a: Answer, u=Depends(current_user), con=Depends(get_db)):
    q = con.execute("SELECT answer, explain FROM questions WHERE id=?", (a.question_id,)).fetchone()
    if not q:
        raise HTTPException(404, "question not found")
    uid, day, correct = u["id"], today().isoformat(), a.choice == q["answer"]
    r = con.execute("SELECT box FROM reviews WHERE user_id=? AND question_id=?", (uid, a.question_id)).fetchone()
    repeat = con.execute("SELECT 1 FROM answers WHERE user_id=? AND question_id=? AND day=?", (uid, a.question_id, day)).fetchone()
    box, gap = srs.review(r["box"] if r else 0, correct)
    gained = 0 if repeat else srs.xp(correct)  # one XP award per card per day keeps the leaderboard honest
    with con:
        con.execute("INSERT OR REPLACE INTO reviews VALUES(?,?,?,?)", (uid, a.question_id, box, (today() + timedelta(gap)).isoformat()))
        con.execute("INSERT INTO answers(user_id,question_id,correct,xp,day) VALUES(?,?,?,?,?)", (uid, a.question_id, correct, gained, day))
        new_badges = award(con, uid)
    return {"correct": correct, "answer": q["answer"], "explain": L(q["explain"]), "xp": gained,
            "box": box, "due_in": gap, "new_badges": new_badges}


@app.get("/api/leaderboard")
def leaderboard(scope: Literal["people", "teams"] = "people", period: Literal["week", "all"] = "week",
                u=Depends(current_user), con=Depends(get_db)):
    since = ago(6) if period == "week" else "0000"
    rows = con.execute("""SELECT u.id, u.name, u.team_id, t.name team, COALESCE(SUM(a.xp), 0) xp
        FROM users u JOIN teams t ON t.id = u.team_id LEFT JOIN answers a ON a.user_id = u.id AND a.day >= ?
        GROUP BY u.id ORDER BY xp DESC, u.id""", (since,)).fetchall()
    if scope == "people":
        return [{"id": r["id"], "name": L(r["name"]), "team": L(r["team"]), "xp": r["xp"], "me": r["id"] == u["id"]} for r in rows]
    teams = {}
    for r in rows:
        t = teams.setdefault(r["team_id"], {"id": r["team_id"], "name": L(r["team"]), "xp": 0, "members": 0, "me": False})
        t["xp"] += r["xp"]
        t["members"] += 1
        t["me"] |= r["id"] == u["id"]
    out = [{**t, "xp": round(t["xp"] / t["members"])} for t in teams.values()]  # average per member: fair across team sizes
    return sorted(out, key=lambda t: -t["xp"])


# ---------- manager ----------
def people_stats(con):
    users = con.execute("SELECT u.*, t.name team FROM users u JOIN teams t ON t.id=u.team_id").fetchall()
    last = dict(con.execute("SELECT user_id, MAX(day) FROM answers GROUP BY user_id").fetchall())
    out = []
    for u in users:
        m = track_mastery(con, u["id"])
        out.append({"id": u["id"], "name": L(u["name"]), "team": L(u["team"]), "team_id": u["team_id"],
                    "xp": total_xp(con, u["id"]), "week_xp": total_xp(con, u["id"], ago(6)),
                    "streak": srs.streak(active_days(con, u["id"]), today()),
                    "mastery": sum(t["mastery"] for t in m.values()) / len(m), "tracks": m, "last": last.get(u["id"])})
    return out


@app.get("/api/dashboard")
def dashboard(_=Depends(manager), con=Depends(get_db)):
    people = people_stats(con)
    n = len(people)

    def window(a, b):  # days [a, b] ago
        r = con.execute("SELECT COUNT(DISTINCT user_id), AVG(correct), COUNT(*) FROM answers WHERE day>=? AND day<=?", (ago(b), ago(a))).fetchone()
        return {"active": r[0], "accuracy": r[1] or 0, "answers": r[2]}

    now, prev = window(0, 6), window(7, 13)
    trend = {r[0]: {"active": r[1], "answers": r[2], "accuracy": r[3]} for r in con.execute(
        "SELECT day, COUNT(DISTINCT user_id), COUNT(*), AVG(correct) FROM answers WHERE day>=? GROUP BY day", (ago(13),))}
    tracks = [{"id": r["id"], "title": L(r["title"]), "color": r["color"]} for r in con.execute("SELECT * FROM tracks ORDER BY pos")]
    teams = [{"id": r["id"], "name": L(r["name"])} for r in con.execute("SELECT * FROM teams ORDER BY id")]
    heat = [[round(sum(p["tracks"][t["id"]]["mastery"] for p in members) / max(len(members), 1), 3) for t in tracks]
            for tm in teams for members in [[p for p in people if p["team_id"] == tm["id"]]]]
    gaps = con.execute("""SELECT q.id, q.prompt, l.track_id, AVG(a.correct) acc, COUNT(*) n FROM answers a
        JOIN questions q ON q.id=a.question_id JOIN lessons l ON l.id=q.lesson_id
        GROUP BY q.id HAVING n >= 5 ORDER BY acc LIMIT 5""").fetchall()
    days_since = lambda p: (today() - date.fromisoformat(p["last"])).days if p["last"] else None
    at_risk = sorted([{**p, "idle": days_since(p)} for p in people if days_since(p) is None or days_since(p) >= 4],
                     key=lambda p: -(p["idle"] or 99))[:6]
    strip = lambda p: {k: p[k] for k in ("id", "name", "team", "xp", "week_xp", "streak", "mastery", "last")}
    return {
        "kpis": {"learners": n, "active": now["active"], "active_prev": prev["active"],
                 "accuracy": now["accuracy"], "accuracy_prev": prev["accuracy"],
                 "answers": now["answers"], "answers_prev": prev["answers"],
                 "mastery": sum(p["mastery"] for p in people) / max(n, 1)},
        "trend": [{"day": ago(i), **trend.get(ago(i), {"active": 0, "answers": 0, "accuracy": 0})} for i in range(13, -1, -1)],
        "tracks": tracks, "teams": teams, "heat": heat,
        "gaps": [{"id": g["id"], "prompt": L(g["prompt"]), "track": g["track_id"], "accuracy": g["acc"], "attempts": g["n"]} for g in gaps],
        "at_risk": [{**strip(p), "idle": p["idle"]} for p in at_risk],
        "top": [strip(p) for p in sorted(people, key=lambda p: -p["week_xp"])[:5]],
    }


@app.get("/api/dashboard/export.csv")
def export(_=Depends(manager), con=Depends(get_db)):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name_fa", "name_en", "team", "xp_total", "xp_week", "streak", "mastery_pct", "last_active"])
    for p in sorted(people_stats(con), key=lambda p: -p["xp"]):
        w.writerow([p["name"]["fa"], p["name"]["en"], p["team"]["en"], p["xp"], p["week_xp"], p["streak"],
                    round(p["mastery"] * 100), p["last"] or ""])
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",  # BOM so Excel reads Persian
                    headers={"Content-Disposition": "attachment; filename=ranksyar-report.csv"})


# ---------- public ----------
class DemoRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    company: str = Field(min_length=2, max_length=120)
    contact: str = Field(min_length=5, max_length=120)
    size: str = Field(max_length=20)


@app.post("/api/demo-requests", status_code=201)
def demo_request(body: DemoRequest, con=Depends(get_db)):
    with con:
        con.execute("INSERT INTO demo_requests(name,company,contact,size,created) VALUES(?,?,?,?,?)",
                    (body.name, body.company, body.contact, body.size, datetime.now().isoformat(timespec="seconds")))
    return {"ok": True}


@app.get("/api/health")
def health():
    return {"ok": True}
