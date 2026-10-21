"""Builds the Wager AU site from data/tips.json and data/results.json.

Run from the repo root: python3 tools/build.py
"""
import datetime as dt
import html
import json
import os
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIPS = json.load(open(os.path.join(ROOT, "data", "tips.json")))
RESULTS = json.load(open(os.path.join(ROOT, "data", "results.json")))

NAV = [("index.html", "Home"), ("tips.html", "Tips"), ("results.html", "Results"),
       ("method.html", "Method"), ("members.html", "Members"), ("about.html", "About")]

HEAD = """<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header>
  <div class="wrap">
    <a class="mark" href="index.html">WAGER<span>AU</span></a>
    <nav aria-label="Main">
{nav}
      <a href="https://www.tiktok.com/@pk_p1cks" target="_blank" rel="noopener">@pk_p1cks</a>
    </nav>
  </div>
</header>
<main>
"""

FOOT = """</main>
<footer>
  <div class="wrap">
    <div class="grid">
      <div>
        <div class="age">18+</div>
        <p><b>Gamble responsibly.</b> Tips are opinion for entertainment, not financial advice. Only bet what you can afford to lose.</p>
        <p>Gambling Help Online: <span class="num">1800 858 858</span> · <a href="https://www.gamblinghelponline.org.au" target="_blank" rel="noopener">gamblinghelponline.org.au</a></p>
        <p>Self-exclude from all licensed bookmakers: <a href="https://www.betstop.gov.au" target="_blank" rel="noopener">BetStop</a></p>
      </div>
      <div>
        <h4>Wager AU</h4>
        <ul>{links}</ul>
      </div>
      <div>
        <h4>Info</h4>
        <ul><li><a href="responsible-gambling.html">Responsible gambling</a></li><li><a href="terms.html">Terms of use</a></li><li><a href="privacy.html">Privacy policy</a></li></ul>
      </div>
    </div>
    <p class="fine">Past results don't guarantee future results. Wager AU gives tips and analysis only. It doesn't take bets and isn't a bookmaker. © 2026 Wager AU.</p>
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
    links = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in NAV[1:])
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
    return dict(w=w, l=l, v=v, staked=staked, pl=pl, roi=(pl / staked if staked else 0),
                pend=sum(r["result"] == "PENDING" for r in rows))


def u(x):
    return f"{'+' if x > 0 else ('−' if x < 0 else '')}{abs(x):.2f}u"


def cls(x):
    return "pos" if x > 0 else ("neg" if x < 0 else "")


def latest_date():
    return max(r["date"] for r in RESULTS if settled(r))


def fmt_date(s):
    return dt.date.fromisoformat(s).strftime("%-d %b %Y")


def ticket(b):
    legs = "".join(f'<li><span class="leg-name">{html.escape(g["name"])}</span><span class="leg-game">{html.escape(g["game"])}</span>'
                   f'<span class="leg-stat">{g["why"]}</span></li>' for g in b["legs"])
    return (f'<article class="ticket"><div class="t-top"><h3>{html.escape(b["title"])}</h3><span class="price">{b["price"]:.2f}</span></div>'
            f'<ul class="legs">{legs}</ul><div class="t-foot stub"><span>{html.escape(b["type"])}</span><span>{b["units"]:g} units</span></div></article>')


def tips_html(limit_days=None):
    out = []
    for d in TIPS["days"][:limit_days]:
        out.append(f'<h3 class="eyebrow" style="margin:28px 0 12px">{html.escape(d["label"])} · {d["sport"]}</h3>'
                   f'<div class="tickets">{"".join(ticket(b) for b in d["bets"])}</div>')
    return "".join(out)


def ledger():
    rows = []
    for sport in ("NFL", "NBA"):
        s = summary([r for r in RESULTS if r["sport"] == sport])
        if s["w"] + s["l"] == 0:
            continue
        rows.append(f'<div class="row"><span class="label">{sport} units profit</span><span class="val {cls(s["pl"])}">{u(s["pl"])}</span></div>'
                    f'<div class="row"><span class="label">{sport} record (W–L)</span><span class="val">{s["w"]}–{s["l"]}</span></div>'
                    f'<div class="row"><span class="label">{sport} return on units staked</span><span class="val {cls(s["roi"])}">{s["roi"]*100:+.1f}%</span></div>')
    return (f'<div class="ledger" aria-label="Season record"><div class="top"><b>Season ledger</b>'
            f'<span class="num">to {fmt_date(latest_date())}</span></div>{"".join(rows)}</div>')


def weekly_table():
    groups = OrderedDict()
    for r in sorted(RESULTS, key=lambda r: (r["sport"] != "NFL", r["week"])):
        groups.setdefault((r["sport"], r["week"]), []).append(r)
    trs = []
    for (sport, wk), rows in groups.items():
        s = summary(rows)
        if s["w"] + s["l"] + s["v"] == 0:
            pill, prof, rec = '<span class="pill p">PENDING</span>', "–", "–"
        else:
            pill = '<span class="pill w">UP</span>' if s["pl"] > 0 else '<span class="pill l">DOWN</span>'
            prof, rec = f'<span class="{cls(s["pl"])}">{u(s["pl"])}</span>', f'{s["w"]}–{s["l"]}–{s["v"]}'
        staked = sum(r["units"] or 0 for r in rows)
        trs.append(f'<tr><td>{sport} week {wk}</td><td class="r num">{len(rows)}</td><td class="r num">{rec}</td>'
                   f'<td class="r num">{staked:.2f}</td><td class="r num">{prof}</td><td>{pill}</td></tr>')
    return ('<div class="tbl"><table><thead><tr><th>Week</th><th class="r">Bets</th><th class="r">W–L–Void</th>'
            '<th class="r">Units staked</th><th class="r">Profit</th><th>Result</th></tr></thead><tbody>'
            + "".join(trs) + "</tbody></table></div>")


def bet_log():
    trs = []
    for r in sorted(RESULTS, key=lambda r: r["date"], reverse=True):
        res = r["result"] or "PENDING"
        p = {"WIN": "w", "LOSS": "l"}.get(res, "p")
        bet = r["bet"] if r["type"] == "Multi" else f'{r["players"]} {r["bet"]}'
        odds = f'{r["odds"]:.2f}' if isinstance(r["odds"], (int, float)) else "–"
        pl = u(r["pl"]) if isinstance(r["pl"], (int, float)) and settled(r) else "–"
        trs.append(f'<tr><td class="num">{fmt_date(r["date"])}</td><td>{r["sport"]}</td><td>{html.escape(r["game"] or "")}</td>'
                   f'<td>{html.escape(bet)}</td><td class="r num">{odds}</td><td class="r num">{r["units"]:g}</td>'
                   f'<td><span class="pill {p}">{res}</span></td><td class="r num {cls(r["pl"] or 0) if settled(r) else ""}">{pl}</td></tr>')
    return ('<div class="tbl"><table style="min-width:820px"><thead><tr><th>Date</th><th>Sport</th><th>Game</th><th>Bet</th>'
            '<th class="r">Odds</th><th class="r">Units</th><th>Result</th><th class="r">Profit</th></tr></thead><tbody>'
            + "".join(trs) + "</tbody></table></div>")


METHOD_STEPS = """<div class="steps">
  <div class="step"><h3>Matchup</h3><p>Start from the defences that give up the most, or the least, to each position, confirmed on the stat the bet pays on.</p></div>
  <div class="step"><h3>Real line</h3><p>Pull the bookmaker's actual main and alternate lines. No guessed prices.</p></div>
  <div class="step"><h3>Research</h3><p>Minutes, shots and targets, injuries and news, coverage and pace, and how the same role has done against this defence.</p></div>
  <div class="step"><h3>Stake</h3><p>The depth of the research sets the units. Every result goes in the ledger, win or lose.</p></div>
</div>"""


def build():
    upd = fmt_date(TIPS["updated"])
    page("index.html", "Wager AU", "Researched NFL and NBA player-prop tips for Australian punters, with every result logged.", f"""
<div class="wrap hero">
  <div class="hero-grid">
    <div>
      <p class="eyebrow">NFL &amp; NBA player props · decimal odds</p>
      <h1>Player props, <em>researched</em>.</h1>
      <p class="lede">Every tip starts from the matchup, gets checked against how that role has done against that defence, and is logged win or lose. No locks, no guarantees, just the work shown.</p>
      <div class="cta"><a class="btn primary" href="tips.html">See today's tips</a><a class="btn ghost" href="results.html">Full record</a></div>
    </div>
    {ledger()}
  </div>
</div>
<section><div class="wrap">
  <div class="sec-head"><div><p class="eyebrow">Updated {upd}</p><h2>Latest tips</h2></div><p>Multis built from alternate lines the players clear most nights.</p></div>
  {tips_html(1)}
  <p class="note"><a href="tips.html">All current tips</a> · Prices move. Check your bookmaker before placing. Times are Melbourne time.</p>
</div></section>
<section><div class="wrap">
  <div class="sec-head"><div><p class="eyebrow">How a tip gets made</p><h2>The method</h2></div><p>The same checks run on every bet. A tip that fails one doesn't go out.</p></div>
  {METHOD_STEPS}
</div></section>
""")

    page("tips.html", "Tips · Wager AU", "Current NFL and NBA player-prop tips from Wager AU.", f"""
<div class="wrap page-head"><p class="eyebrow">Updated {upd}</p><h1>Tips</h1>
<p>Each tip shows the price when it was researched, the stake in units and the main reason behind every leg. Hit rates are from last season's games at normal minutes unless stated.</p></div>
<section style="border-top:0;padding-top:8px"><div class="wrap">{tips_html()}
<p class="note">Prices move. Check your bookmaker before placing. Times are Melbourne time. A unit is whatever amount you choose to bet per standard tip; keep it small.</p></div></section>
""")

    sn, sb = summary([r for r in RESULTS if r["sport"] == "NFL"]), summary([r for r in RESULTS if r["sport"] == "NBA"])
    page("results.html", "Results · Wager AU", "Every Wager AU tip with its result, win or lose.", f"""
<div class="wrap page-head"><p class="eyebrow">To {fmt_date(latest_date())}</p><h1>Results</h1>
<p>Every official tip is logged here, wins and losses. Units are the stake; profit is in units at the price taken.
NFL: {sn['w']}–{sn['l']}, {u(sn['pl'])}. NBA: {sb['w']}–{sb['l']}, {u(sb['pl'])}.</p></div>
<section style="border-top:0;padding-top:8px"><div class="wrap"><h2 style="margin-bottom:16px">By week</h2>{weekly_table()}</div></section>
<section><div class="wrap"><h2 style="margin-bottom:16px">Every bet</h2>{bet_log()}</div></section>
""")

    page("method.html", "Method · Wager AU", "How Wager AU researches and stakes every tip.", f"""
<div class="wrap page-head"><p class="eyebrow">How a tip gets made</p><h1>The method</h1>
<p>The same process runs on every game day, for both sports. Here's what happens before a tip goes out.</p></div>
<section style="border-top:0;padding-top:8px"><div class="wrap">{METHOD_STEPS}</div></section>
<section><div class="wrap prose">
<h2>The checks every bet passes</h2>
<ul>
<li><b>The matchup holds on the stat itself.</b> A defence ranked soft overall can still shut down one position. The bet has to be backed on the exact stat it pays on.</li>
<li><b>The same role clears the line against this defence.</b> We look at how players in the same role did against this opponent, not just the player's own recent games.</li>
<li><b>The defence type and game script fit.</b> Coverage, pace, blitz rate, the spread and the total all have to support the side.</li>
<li><b>News is applied.</b> Injuries, returns, minutes limits and coaching comments are checked for every player they touch.</li>
</ul>
<h2>How stakes are set</h2>
<p>Stakes run from 0.75 to 2.5 units on singles, depending on how much of the research agrees. Multis are usually two legs on lower alternate lines, priced around 1.70 to 2.20. Multis are overs only.</p>
<div class="callout">No tip is a lock. A well-researched bet still loses often. The results page shows every one.</div>
</div></section>
""")

    page("members.html", "Members · Wager AU", "Join the Wager AU list for full NFL and NBA cards.", """
<div class="wrap page-head"><p class="eyebrow">Free and members</p><h1>Get the tips</h1>
<p>Free tips are on this site and on TikTok. A members tier with the full card is coming; pricing isn't set yet.</p></div>
<section style="border-top:0;padding-top:8px"><div class="wrap">
<div class="plans">
  <div class="plan"><h3>Free</h3><p class="tag">This site and TikTok</p>
    <ul><li>Current tips on the Tips page</li><li>Every result on the Results page</li><li>Analysis videos on @pk_p1cks</li></ul>
    <a class="btn ghost" href="https://www.tiktok.com/@pk_p1cks" target="_blank" rel="noopener">Follow on TikTok</a></div>
  <div class="plan feat"><h3>Members</h3><p class="tag">Coming soon · pricing to be announced</p>
    <ul><li>The full card for every NFL and NBA day</li><li>Units and the research behind each bet</li><li>Alerts when lines move</li></ul>
    <form id="join" novalidate>
      <label class="eyebrow" for="email" style="flex-basis:100%">Email</label>
      <input id="email" type="email" placeholder="you@example.com" autocomplete="email" required>
      <button class="btn primary" type="submit">Join the list</button>
    </form>
    <p class="msg" id="msg" aria-live="polite"></p></div>
</div>
<p class="note">18+ only. Wager AU sells tips and analysis, not bets.</p>
</div></section>
""", JOIN_SCRIPT)

    page("about.html", "About · Wager AU", "About Wager AU, an Australian NFL and NBA tipping service.", """
<div class="wrap page-head"><p class="eyebrow">About</p><h1>About Wager AU</h1></div>
<section style="border-top:0;padding-top:8px"><div class="wrap prose">
<p>Wager AU is an Australian tipping service for NFL and NBA player props, priced in decimal odds for local punters.</p>
<p>Every tip comes from the same process: a matchup model, real bookmaker lines, and research into usage, injuries, defence and game script. Nothing goes out on a hunch, and every result is published.</p>
<p>The analysis videos run on TikTok at <a href="https://www.tiktok.com/@pk_p1cks" target="_blank" rel="noopener">@pk_p1cks</a>.</p>
<div class="callout">Wager AU gives tips and analysis only. It doesn't take bets, hold money or act as a bookmaker. You place your own bets with a licensed Australian bookmaker.</div>
</div></section>
""")

    page("responsible-gambling.html", "Responsible gambling · Wager AU", "Support and tools for safer betting.", """
<div class="wrap page-head"><p class="eyebrow">18+ only</p><h1>Responsible gambling</h1></div>
<section style="border-top:0;padding-top:8px"><div class="wrap prose">
<p>Betting should be entertainment. Our tips are opinions, and even well-researched bets lose often. Only bet what you can afford to lose.</p>
<h2>Keep it in check</h2>
<ul>
<li>Set a budget before you bet and stick to it.</li>
<li>Use the deposit limits your bookmaker offers.</li>
<li>Never chase losses.</li>
<li>Take breaks, and don't bet when you're upset, drinking or under pressure.</li>
</ul>
<h2>Free, confidential help</h2>
<ul>
<li><b>Gambling Help Online:</b> <span class="num">1800 858 858</span>, 24/7, or chat at <a href="https://www.gamblinghelponline.org.au" target="_blank" rel="noopener">gamblinghelponline.org.au</a></li>
<li><b>BetStop, the National Self-Exclusion Register:</b> block yourself from all licensed Australian online bookmakers at <a href="https://www.betstop.gov.au" target="_blank" rel="noopener">betstop.gov.au</a></li>
</ul>
<div class="callout">You must be 18 or over to bet in Australia. Wager AU content isn't intended for anyone under 18.</div>
</div></section>
""")

    page("terms.html", "Terms of use · Wager AU", "Terms of use for the Wager AU website.", """
<div class="wrap page-head"><p class="eyebrow">Draft · last updated 21 Oct 2026</p><h1>Terms of use</h1></div>
<section style="border-top:0;padding-top:8px"><div class="wrap prose">
<div class="callout">This is a first draft. Have it reviewed before you take payments or run a paid membership.</div>
<h3>1. What we provide</h3><p>Wager AU publishes sports betting tips and analysis. We don't accept bets, hold money or act as a bookmaker.</p>
<h3>2. Not advice</h3><p>Tips are general opinion for entertainment. They aren't financial advice and don't take your circumstances into account. You decide whether to bet and how much.</p>
<h3>3. No guarantees</h3><p>Past results don't guarantee future results. Prices and lines change, and a tip may no longer be available at the price shown.</p>
<h3>4. Age</h3><p>You must be 18 or over to use this site.</p>
<h3>5. Liability</h3><p>To the extent the law allows, Wager AU isn't liable for losses from bets you place. Nothing in these terms excludes rights you have under the Australian Consumer Law.</p>
<h3>6. Content</h3><p>The content on this site belongs to Wager AU. Don't republish it without permission.</p>
<h3>7. Changes</h3><p>We may update these terms. The date at the top shows the latest version.</p>
</div></section>
""")

    page("privacy.html", "Privacy policy · Wager AU", "How Wager AU handles personal information.", """
<div class="wrap page-head"><p class="eyebrow">Draft · last updated 21 Oct 2026</p><h1>Privacy policy</h1></div>
<section style="border-top:0;padding-top:8px"><div class="wrap prose">
<div class="callout">This is a first draft. Update it when you add a mailing list, analytics or payments.</div>
<h3>What we collect</h3><p>Right now this site collects no personal information. When sign-ups open, we'll collect the email address you give us to send tips and updates.</p>
<h3>How we use it</h3><p>Only to send the content you signed up for. We won't sell or rent your details.</p>
<h3>Third parties</h3><p>The site loads fonts from Google Fonts. A mailing-list provider will hold sign-up emails once that's added.</p>
<h3>Your choices</h3><p>You can unsubscribe from any email, or ask us to delete your details.</p>
<h3>Contact</h3><p>Contact details will be added before sign-ups open.</p>
</div></section>
""")


if __name__ == "__main__":
    build()
    print("built", [f for f in os.listdir(ROOT) if f.endswith(".html")])
