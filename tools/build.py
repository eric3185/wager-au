"""Builds the Wager AU site from data/tips.json and data/results.json.

Run from the repo root: python3 tools/build.py
"""
import datetime as dt
import html
import json
import os
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIPS = json.load(open(os.path.join(ROOT, "data", "tips.json")))
RESULTS = json.load(open(os.path.join(ROOT, "data", "results.json")))

NAV = [("index.html", "Home"), ("tips.html", "Tips"), ("results.html", "Results"),
       ("model.html", "The model"), ("members.html", "Members")]

HEAD = """<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header>
  <div class="wrap">
    <a class="brand" href="index.html"><img src="assets/mark.png" alt="" width="36" height="36">WAGER AU</a>
    <nav aria-label="Main">
{nav}
      <a class="btn primary nav-cta" href="https://discord.gg/CXUwYuUku" target="_blank" rel="noopener">Join Discord</a>
    </nav>
  </div>
</header>
<main>
"""

FOOT = """</main>
<footer>
  <div class="wrap">
    <div class="grid">
      <div><img src="assets/logo.png" alt="Wager AU" width="110" height="110"></div>
      <div><h4>Site</h4><ul>{links}</ul></div>
      <div><h4>Follow</h4><ul><li><a href="https://discord.gg/CXUwYuUku" target="_blank" rel="noopener">Discord</a></li><li><a href="https://www.tiktok.com/@pk_p1cks" target="_blank" rel="noopener">TikTok @pk_p1cks</a></li>
        <li><a href="responsible-gambling.html">Responsible gambling</a></li><li><a href="terms.html">Terms</a></li><li><a href="privacy.html">Privacy</a></li></ul></div>
    </div>
    <p class="rg">18+ · Gamble responsibly · Gambling Help Online 1800 858 858 · © 2026 Wager AU</p>
  </div>
</footer>
{script}
</body>
</html>
"""

JOIN_SCRIPT = """<script>
var f=document.getElementById('join');
if(f){f.addEventListener('submit',function(e){
  e.preventDefault();
  var el=document.getElementById('email'), msg=document.getElementById('msg');
  if(!el.value||!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(el.value)){msg.textContent='Enter an email address like name@example.com.';el.focus();return;}
  msg.textContent='Sign-ups open soon. Follow @pk_p1cks on TikTok in the meantime.';
});}
</script>"""


def page(fname, title, desc, body, script=""):
    nav = "\n".join(f'      <a href="{h}"{" aria-current=\"page\"" if h == fname else ""}>{t}</a>' for h, t in NAV)
    links = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in NAV)
    out = HEAD.format(title=html.escape(title), desc=html.escape(desc), nav=nav) + body + FOOT.format(links=links, script=script)
    open(os.path.join(ROOT, fname), "w").write(out)


def settled(r):
    return r["result"] in ("WIN", "LOSS")


def summary(rows):
    w = sum(r["result"] == "WIN" for r in rows)
    l = sum(r["result"] == "LOSS" for r in rows)
    v = sum(r["result"] in ("VOID", "PUSH") for r in rows)
    staked = sum(r["units"] or 0 for r in rows if settled(r))
    pl = sum(r["pl"] or 0 for r in rows if settled(r))
    return dict(w=w, l=l, v=v, staked=staked, pl=pl, roi=(pl / staked if staked else 0))


def u(x):
    return f"{'+' if x > 0 else ('−' if x < 0 else '')}{abs(x):.2f}u"


def tone(x):
    return "pos" if x > 0 else "flat"


def fmt_date(s, year=True):
    return dt.date.fromisoformat(s).strftime("%-d %b %Y" if year else "%a %-d %b")


def latest_date():
    return max(r["date"] for r in RESULTS if settled(r))


def days(sport):
    d = defaultdict(list)
    for r in RESULTS:
        if r["sport"] == sport and settled(r):
            d[r["date"]].append(r)
    return {k: summary(v) for k, v in sorted(d.items())}


def winning_days_html(sport="NFL", limit=None):
    wins = sorted(((k, s) for k, s in days(sport).items() if s["pl"] > 0), key=lambda x: -x[1]["pl"])[:limit]
    return '<div class="days">' + "".join(
        f'<div class="day"><div class="d">{fmt_date(k, False)} · {sport}</div><div class="pl">{u(s["pl"])}</div>'
        f'<div class="rec">{s["w"]}–{s["l"]} on the day</div></div>' for k, s in wins) + "</div>"


def stats_html():
    s = summary([r for r in RESULTS if r["sport"] == "NFL"])
    dd = days("NFL")
    up = sum(x["pl"] > 0 for x in dd.values())
    return (f'<div class="stats">'
            f'<div class="stat"><b>{u(s["pl"])}</b><span>NFL season profit</span></div>'
            f'<div class="stat"><b>{s["w"] / (s["w"] + s["l"]) * 100:.0f}%</b><span>Bets won ({s["w"]}–{s["l"]})</span></div>'
            f'<div class="stat"><b>{s["roi"] * 100:+.1f}%</b><span>Return on units staked</span></div>'
            f'<div class="stat"><b>{up}/{len(dd)}</b><span>Winning NFL betting days</span></div>'
            f'</div><p class="asof">NFL 2026 season to {fmt_date(latest_date())}. Every bet is on the Results page.</p>')


def ticket(b):
    legs = "".join(f'<li><span class="leg-name">{html.escape(g["name"])}</span><span class="leg-game">{html.escape(g["game"])}</span>'
                   f'<span class="leg-stat">{g["why"]}</span></li>' for g in b["legs"])
    return (f'<article class="ticket"><div class="t-top"><h3>{html.escape(b["title"])}</h3><span class="price">{b["price"]:.2f}</span></div>'
            f'<ul class="legs">{legs}</ul><div class="t-foot"><span>{html.escape(b["type"])}</span><span>{b["units"]:g} units</span></div></article>')


def tips_html(limit_days=None):
    return "".join(f'<span class="eyebrow day-label">{html.escape(d["label"])} · {d["sport"]}</span>'
                   f'<div class="tickets">{"".join(ticket(b) for b in d["bets"])}</div>' for d in TIPS["days"][:limit_days])


def weekly_table():
    groups = OrderedDict()
    for r in sorted(RESULTS, key=lambda r: (r["sport"] != "NFL", r["week"])):
        groups.setdefault((r["sport"], r["week"]), []).append(r)
    trs = []
    for (sport, wk), rows in groups.items():
        s = summary(rows)
        done = s["w"] + s["l"] + s["v"] > 0
        rec = f'{s["w"]}–{s["l"]}' if done else "–"
        prof = f'<span class="{tone(s["pl"])}">{u(s["pl"])}</span>' if done else '<span class="tag">PENDING</span>'
        trs.append(f'<tr><td>{sport} week {wk}</td><td class="r num">{len(rows)}</td><td class="r num">{rec}</td><td class="r num">{prof}</td></tr>')
    return ('<div class="tbl"><table style="min-width:420px"><thead><tr><th>Week</th><th class="r">Bets</th><th class="r">W–L</th>'
            '<th class="r">Profit</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")


def bet_log():
    trs = []
    for r in sorted(RESULTS, key=lambda r: r["date"], reverse=True):
        res = r["result"] or "PENDING"
        bet = r["bet"] if r["type"] == "Multi" else f'{r["players"]} {r["bet"]}'
        odds = f'{r["odds"]:.2f}' if isinstance(r["odds"], (int, float)) else "–"
        pl = u(r["pl"]) if isinstance(r["pl"], (int, float)) and settled(r) else "–"
        trs.append(f'<tr><td class="num">{fmt_date(r["date"])}</td><td>{r["sport"]}</td><td>{html.escape(bet)}</td>'
                   f'<td class="r num">{odds}</td><td class="r num">{r["units"]:g}</td>'
                   f'<td><span class="tag{" w" if res == "WIN" else ""}">{res}</span></td>'
                   f'<td class="r num {tone(r["pl"] or 0) if settled(r) else "flat"}">{pl}</td></tr>')
    return ('<div class="tbl"><table style="min-width:760px"><thead><tr><th>Date</th><th>Sport</th><th>Bet</th>'
            '<th class="r">Odds</th><th class="r">Units</th><th>Result</th><th class="r">Profit</th></tr></thead><tbody>'
            + "".join(trs) + "</tbody></table></div>")


MODEL_CARDS = """<div class="model">
  <div class="mcard"><span class="k">Ratings</span><h3>Every defence, every position</h3><p>All 32 NFL defences rated against QBs, RBs, WRs and TEs each week, and every NBA team against guards, forwards and centres.</p></div>
  <div class="mcard"><span class="k">Usage</span><h3>Real roles</h3><p>Target, carry and minute shares refreshed before every betting day from the latest box scores and news.</p></div>
  <div class="mcard"><span class="k">Pricing</span><h3>Every line priced</h3><p>Sportsbet main and alternate lines run through the model to get a projection and a win probability for each bet.</p></div>
  <div class="mcard"><span class="k">Gates</span><h3>Research checks</h3><p>A bet goes out only when the matchup, the role against this defence, the game script and the news all line up.</p></div>
</div>"""


def build():
    upd = fmt_date(TIPS["updated"])
    page("index.html", "Wager AU", "Model-driven NFL and NBA player-prop tips for Australian punters.", f"""
<div class="wrap hero">
  <div class="hero-grid">
    <div>
      <p class="eyebrow">NFL &amp; NBA player props</p>
      <h1 style="margin-top:14px">Built on a <em>model</em>.<br>Backed by research.</h1>
      <p class="lede">Every tip is priced by the Wager AU model, then checked against the matchup, the minutes and the game script.</p>
      <div class="cta"><a class="btn primary" href="https://discord.gg/CXUwYuUku" target="_blank" rel="noopener">Join the Discord</a><a class="btn ghost" href="tips.html">Today's tips</a><a class="btn ghost" href="results.html">Results</a></div>
    </div>
    <img class="hero-logo" src="assets/logo.png" alt="Wager AU logo" width="380" height="380">
  </div>
  <div style="margin-top:56px">{stats_html()}</div>
</div>
<section><div class="wrap">
  <div class="sec-head"><div><span class="eyebrow">The model</span><h2>How the picks are made</h2></div><a class="btn ghost" href="model.html">More on the model</a></div>
  {MODEL_CARDS}
</div></section>
<section><div class="wrap">
  <div class="sec-head"><div><span class="eyebrow">Best days</span><h2>Winning days</h2></div></div>
  {winning_days_html(limit=4)}
</div></section>
<section><div class="wrap">
  <div class="sec-head"><div><span class="eyebrow">Updated {upd}</span><h2>Latest tips</h2></div><a class="btn ghost" href="tips.html">All tips</a></div>
  {tips_html(1)}
  <div class="discord-band"><div><h3>Get every tip first in the Discord</h3><p class="muted">Cards, line moves and results, posted as they happen.</p></div><a class="btn primary" href="https://discord.gg/CXUwYuUku" target="_blank" rel="noopener">Join Discord</a></div>
</div></section>
""")

    page("tips.html", "Tips · Wager AU", "Current NFL and NBA player-prop tips from Wager AU.", f"""
<div class="wrap page-head"><span class="eyebrow">Updated {upd}</span><h1 style="margin-top:12px">Tips</h1>
<p>The price, the stake and the reason behind every leg.</p></div>
<section style="border-top:0;padding-top:8px"><div class="wrap">{tips_html()}
<p class="note">Times are Melbourne time. Check the price with your bookmaker before placing.</p>
<div class="discord-band"><div><h3>Get every tip first in the Discord</h3><p class="muted">Cards, line moves and results, posted as they happen.</p></div><a class="btn primary" href="https://discord.gg/CXUwYuUku" target="_blank" rel="noopener">Join Discord</a></div></div></section>
""")

    page("results.html", "Results · Wager AU", "Wager AU results: profit, winning days and every bet.", f"""
<div class="wrap page-head"><span class="eyebrow">Track record</span><h1 style="margin-top:12px">Results</h1></div>
<section style="border-top:0;padding-top:8px"><div class="wrap">{stats_html()}</div></section>
<section><div class="wrap"><div class="sec-head"><div><span class="eyebrow">Best days</span><h2>Winning days</h2></div></div>{winning_days_html()}</div></section>
<section><div class="wrap"><div class="sec-head"><div><span class="eyebrow">By week</span><h2>Weekly record</h2></div></div>{weekly_table()}</div></section>
<section><div class="wrap"><div class="sec-head"><div><span class="eyebrow">Full log</span><h2>Every bet</h2></div></div>{bet_log()}</div></section>
""")

    page("model.html", "The model · Wager AU", "How the Wager AU model rates matchups, prices lines and picks bets.", f"""
<div class="wrap page-head"><span class="eyebrow">The model</span><h1 style="margin-top:12px">The Wager AU model</h1>
<p>A matchup model for NFL and NBA player props, run before every betting day.</p></div>
<section style="border-top:0;padding-top:8px"><div class="wrap">{MODEL_CARDS}</div></section>
<section><div class="wrap prose">
<h2>Step by step</h2>
<ul>
<li><b>Rate the matchups.</b> Each defence is ranked against each position on the stat the bet pays on: yards, receptions, points, rebounds, assists, threes.</li>
<li><b>Set the roles.</b> Each player's share of targets, carries or minutes comes from the latest games and team news.</li>
<li><b>Price the lines.</b> The model projects each player's number and turns it into a win probability for the exact line and price on offer.</li>
<li><b>Run the checks.</b> The same role has to clear the line against this defence, and the coverage, pace and expected game script have to fit.</li>
<li><b>Stake by confidence.</b> The more the research agrees, the bigger the stake. Multis use lower alternate lines priced around 1.70 to 2.20.</li>
</ul>
</div></section>
""")

    page("members.html", "Members · Wager AU", "Join the Wager AU list for full NFL and NBA cards.", """
<div class="wrap page-head"><span class="eyebrow">Free and members</span><h1 style="margin-top:12px">Get the tips</h1>
<p>Free tips here and on TikTok. Members get the full card. Coming soon.</p></div>
<section style="border-top:0;padding-top:8px"><div class="wrap">
<div class="plans">
  <div class="plan"><h3>Free</h3><p class="sub">This site and TikTok</p>
    <ul><li>The Wager AU Discord</li><li>Latest tips</li><li>Full results</li><li>Analysis videos on @pk_p1cks</li></ul>
    <div class="cta"><a class="btn primary" href="https://discord.gg/CXUwYuUku" target="_blank" rel="noopener">Join Discord</a><a class="btn ghost" href="https://www.tiktok.com/@pk_p1cks" target="_blank" rel="noopener">Follow on TikTok</a></div></div>
  <div class="plan feat"><h3>Members</h3><p class="sub">Coming soon</p>
    <ul><li>The full card for every NFL and NBA day</li><li>Units and the research behind each bet</li><li>Alerts when lines move</li></ul>
    <form id="join" novalidate>
      <label class="eyebrow" for="email" style="flex-basis:100%">Email</label>
      <input id="email" type="email" placeholder="you@example.com" autocomplete="email" required>
      <button class="btn primary" type="submit">Join the list</button>
    </form>
    <p class="msg" id="msg" aria-live="polite"></p></div>
</div>
</div></section>
""", JOIN_SCRIPT)

    page("responsible-gambling.html", "Responsible gambling · Wager AU", "Support and tools for safer betting.", """
<div class="wrap page-head"><span class="eyebrow">18+</span><h1 style="margin-top:12px">Responsible gambling</h1></div>
<section style="border-top:0;padding-top:8px"><div class="wrap prose">
<ul>
<li>Set a budget before you bet and stick to it.</li>
<li>Use your bookmaker's deposit limits.</li>
<li>Don't chase losses.</li>
</ul>
<h2>Free, confidential help</h2>
<ul>
<li><b>Gambling Help Online:</b> <span class="num">1800 858 858</span>, 24/7 · <a href="https://www.gamblinghelponline.org.au" target="_blank" rel="noopener">gamblinghelponline.org.au</a></li>
<li><b>BetStop:</b> self-exclude from all licensed Australian online bookmakers · <a href="https://www.betstop.gov.au" target="_blank" rel="noopener">betstop.gov.au</a></li>
</ul>
</div></section>
""")

    page("terms.html", "Terms · Wager AU", "Terms of use for the Wager AU website.", """
<div class="wrap page-head"><span class="eyebrow">Last updated 21 Oct 2026</span><h1 style="margin-top:12px">Terms of use</h1></div>
<section style="border-top:0;padding-top:8px"><div class="wrap prose">
<h3>What we provide</h3><p>Wager AU publishes sports betting tips and analysis. We don't take bets or hold money.</p>
<h3>Your decisions</h3><p>Tips are general opinion, not financial advice. You decide whether to bet and how much.</p>
<h3>Age</h3><p>You must be 18 or over to use this site.</p>
<h3>Liability</h3><p>To the extent the law allows, Wager AU isn't liable for losses from bets you place. Nothing here excludes your rights under the Australian Consumer Law.</p>
<h3>Content</h3><p>Content on this site belongs to Wager AU. Don't republish it without permission.</p>
</div></section>
""")

    page("privacy.html", "Privacy · Wager AU", "How Wager AU handles personal information.", """
<div class="wrap page-head"><span class="eyebrow">Last updated 21 Oct 2026</span><h1 style="margin-top:12px">Privacy policy</h1></div>
<section style="border-top:0;padding-top:8px"><div class="wrap prose">
<h3>What we collect</h3><p>This site doesn't collect personal information yet. When sign-ups open, we'll collect the email you give us to send tips.</p>
<h3>How we use it</h3><p>Only to send what you signed up for. We won't sell your details.</p>
<h3>Third parties</h3><p>The site loads fonts from Google Fonts.</p>
<h3>Your choices</h3><p>Unsubscribe from any email at any time, or ask us to delete your details.</p>
</div></section>
""")

    for old in ("method.html", "about.html"):
        p = os.path.join(ROOT, old)
        if os.path.exists(p):
            os.remove(p)


if __name__ == "__main__":
    build()
    print("built", sorted(f for f in os.listdir(ROOT) if f.endswith(".html")))
