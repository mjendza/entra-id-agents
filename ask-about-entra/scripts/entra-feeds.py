#!/usr/bin/env python3
"""Fetch, window-filter and de-duplicate Microsoft Entra ID change feeds.

Used by the `agent-entra-change-tracker` subagent (slash command
`/last-entra-changes`). The agent does the judgement work — classifying scope,
deciding change type, writing the short and long summaries — while this script
does the mechanical work that has to be exact: fetching every configured
RSS/Atom channel, dropping anything outside the requested time window, and
merging items that appear in more than one channel so the final report never
lists the same change twice.

Standard library only. No third-party dependencies; honours the usual
HTTPS_PROXY / SSL_CERT_FILE environment variables.

Usage
-----
    python3 scripts/entra-feeds.py --window 7d
    python3 scripts/entra-feeds.py --window 30d --out /tmp/changes.json
    python3 scripts/entra-feeds.py --list-feeds

Emits a single JSON document on stdout (or to --out).
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

DEFAULT_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".claude", "feeds", "entra-feeds.json",
)

USER_AGENT = "entra-change-tracker/1.0 (+https://github.com/mjendza/entra-id-agents)"

# Query parameters carrying only campaign/tracking data. Stripping them lets the
# same article arriving from two channels collapse onto one canonical URL.
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ocid", "cid", "wt.mc_id", "wt_mc_id", "epi", "irgwc", "irclickid",
    "ranmid", "ransiteid", "s_cid", "msockid", "source", "referrer",
}

# Leading status decorations that differ between channels for the same item,
# e.g. "[In preview] Public preview: ..." vs "Public preview: ...". Both forms
# are peeled off the title, but the *status they encode* is folded back into the
# key so a preview announcement never merges with the later GA announcement of
# the same feature.
BRACKET_PREFIX_RE = re.compile(r"^\s*\[([^\]]{1,40})\]\s*")

# Only a closed vocabulary is stripped — a generic "<words>:" rule would eat
# legitimate titles like "Microsoft Entra ID: new sign-in logs".
STATUS_PREFIX_RE = re.compile(
    r"^\s*(generally available|general availability|in development|rolling out|"
    r"public preview|private preview|in preview|preview|launched|retirement|"
    r"retiring|deprecated|deprecation)\s*[:\-–—]\s*",
    re.IGNORECASE,
)

STATUS_CLASSES = (
    ("retire", r"retirement|retiring|deprecat|sunset|end of (?:support|life)"),
    ("preview", r"preview"),
    ("ga", r"generally available|general availability|launched"),
    ("dev", r"in development|rolling out"),
)

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

# A normalised title shorter than this is too collision-prone to merge on.
MIN_TITLE_KEY_LEN = 12


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------

def load_config(path: str) -> dict:
    if not os.path.exists(path):
        raise SystemExit(
            f"feed config not found: {path}\n"
            "Create it, or pass --config <path>. See ask-about-entra/README.md "
            "for the schema."
        )
    with open(path, encoding="utf-8") as fh:
        try:
            cfg = json.load(fh)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"feed config is not valid JSON ({path}): {exc}") from exc
    if not isinstance(cfg.get("feeds"), list):
        raise SystemExit(f"feed config has no 'feeds' array: {path}")
    return cfg


def parse_window(raw: str) -> tuple[str, int]:
    """Accept 7d / 30d / 7 / week / month / quarter and return (label, days)."""
    value = (raw or "7d").strip().lower()
    aliases = {
        "week": 7, "1w": 7, "last week": 7, "7": 7,
        "fortnight": 14, "2w": 14,
        "month": 30, "1m": 30, "last month": 30, "30": 30,
        "quarter": 90, "3m": 90,
    }
    if value in aliases:
        days = aliases[value]
    else:
        m = re.fullmatch(r"(\d+)\s*(d|day|days|w|week|weeks|m|month|months)?", value)
        if not m:
            raise SystemExit(f"cannot parse --window {raw!r}; try 7d or 30d")
        days = int(m.group(1)) * {"d": 1, "w": 7, "m": 30}[(m.group(2) or "d")[0]]
    if days < 1:
        raise SystemExit("--window must cover at least one day")
    return f"{days}d", days


# --------------------------------------------------------------------------
# fetching
# --------------------------------------------------------------------------

def ssl_context() -> ssl.SSLContext:
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        bundle = os.environ.get(var)
        if bundle and os.path.exists(bundle):
            return ssl.create_default_context(cafile=bundle)
    if os.path.exists("/root/.ccr/ca-bundle.crt"):
        return ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
    return ssl.create_default_context()


def fetch(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    })
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
        return resp.read()


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower() if "}" in tag else str(tag).lower()


def clean_text(raw: str) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return WS_RE.sub(" ", text).strip()


def text_of(el) -> str:
    return "" if el is None else clean_text("".join(el.itertext()))


def parse_date(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed is not None:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def child(el, *names):
    wanted = {n.lower() for n in names}
    for sub in el:
        if localname(sub.tag) in wanted:
            return sub
    return None


def parse_feed(payload: bytes) -> list[dict]:
    """Parse RSS 2.0 <item> and Atom <entry> elements into plain dicts."""
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError(f"malformed XML: {exc}") from exc

    entries: list[dict] = []
    for el in root.iter():
        if localname(el.tag) not in ("item", "entry"):
            continue

        title = text_of(child(el, "title"))

        link = ""
        for sub in el:
            if localname(sub.tag) != "link":
                continue
            href = sub.get("href") or text_of(sub)
            if not href:
                continue
            if (sub.get("rel") or "alternate").lower() == "alternate":
                link = href
                break
            if not link:
                link = href
        if not link:
            guid_text = text_of(child(el, "guid", "id"))
            if guid_text.startswith("http"):
                link = guid_text

        summary = ""
        for name in ("description", "summary", "content", "encoded"):
            summary = text_of(child(el, name))
            if summary:
                break

        published = None
        for name in ("pubdate", "published", "updated", "date", "modified"):
            published = parse_date(text_of(child(el, name)))
            if published:
                break

        categories: list[str] = []
        for sub in el:
            if localname(sub.tag) not in ("category", "term"):
                continue
            label = clean_text(sub.get("term") or sub.get("label") or text_of(sub))
            if label and label not in categories:
                categories.append(label)

        if not (title or link):
            continue

        entries.append({
            "title": title,
            "url": link.strip(),
            "published": published,
            "summary_raw": summary,
            "categories": categories,
        })
    return entries


# --------------------------------------------------------------------------
# filtering + de-duplication
# --------------------------------------------------------------------------

def compile_patterns(patterns) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in (patterns or [])]


def matches_topic(item: dict, include: list, exclude: list) -> bool:
    text = " ".join([
        item.get("title", ""),
        item.get("summary_raw", ""),
        " ".join(item.get("categories") or []),
        item.get("url", ""),
    ])
    if any(p.search(text) for p in exclude):
        return False
    return True if not include else any(p.search(text) for p in include)


def canonical_url(url: str) -> str:
    if not url:
        return ""
    try:
        parts = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return url.strip().lower()
    host = (parts.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    query = sorted(
        (k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=False)
        if k.lower() not in TRACKING_PARAMS
    )
    return urllib.parse.urlunsplit((
        (parts.scheme or "https").lower(), host, parts.path.rstrip("/") or "/",
        urllib.parse.urlencode(query), "",
    ))


def status_class(text: str) -> str:
    low = (text or "").lower()
    for name, pattern in STATUS_CLASSES:
        if re.search(pattern, low):
            return name
    return ""


def title_key(title: str) -> str:
    """Normalise a headline into a merge key of the form '<status>|<body>'.

    Peels leading '[In preview]'-style brackets and 'Public preview:'-style
    prefixes — repeatedly, since channels stack both — then re-attaches the
    status class so 'Public preview: X' and 'Generally available: X' stay apart
    while '[In preview] Public preview: X' and 'Public preview: X' merge.
    """
    raw = title or ""
    decorations: list[str] = []
    for _ in range(4):  # bounded: titles never stack more than a couple
        match = BRACKET_PREFIX_RE.match(raw) or STATUS_PREFIX_RE.match(raw)
        if not match:
            break
        decorations.append(match.group(1))
        raw = raw[match.end():]

    body = NON_ALNUM_RE.sub(" ", raw.lower()).strip()
    if len(body) < MIN_TITLE_KEY_LEN:
        return ""
    return f"{status_class(' '.join(decorations))}|{body}"


def dedupe(items: list[dict]) -> list[dict]:
    """Merge items sharing a canonical URL or a normalised title.

    The surviving record keeps the earliest publication date (when the change was
    first announced), the richest description, the union of categories, and every
    channel that carried it.
    """
    merged: list[dict] = []
    by_url: dict[str, int] = {}
    by_title: dict[str, int] = {}

    for item in items:
        url_key = canonical_url(item.get("url", ""))
        t_key = title_key(item.get("title", ""))

        index = by_url.get(url_key) if url_key else None
        if index is None and t_key:
            index = by_title.get(t_key)

        source = {
            "feed": item.get("_feed", ""),
            "feed_url": item.get("_feed_url", ""),
            "item_url": item.get("url", ""),
        }

        if index is None:
            record = {k: v for k, v in item.items() if not k.startswith("_")}
            record["sources"] = [source]
            record["duplicate_count"] = 1
            merged.append(record)
            index = len(merged) - 1
        else:
            record = merged[index]
            record["duplicate_count"] += 1
            if source not in record["sources"]:
                record["sources"].append(source)
            if item.get("published") and (
                not record.get("published") or item["published"] < record["published"]
            ):
                record["published"] = item["published"]
            if len(item.get("summary_raw") or "") > len(record.get("summary_raw") or ""):
                record["summary_raw"] = item["summary_raw"]
            for cat in item.get("categories") or []:
                if cat not in record["categories"]:
                    record["categories"].append(cat)

        if url_key:
            by_url.setdefault(url_key, index)
        if t_key:
            by_title.setdefault(t_key, index)

    return merged


# --------------------------------------------------------------------------
# collection
# --------------------------------------------------------------------------

def collect(cfg: dict, since: dt.datetime, timeout: int, include_all: bool):
    global_include = compile_patterns(cfg.get("global_include"))
    global_exclude = compile_patterns(cfg.get("global_exclude"))

    feed_status: list[dict] = []
    windowed: list[dict] = []
    raw_total = 0

    for feed in cfg["feeds"]:
        name = feed.get("name") or feed.get("url", "<unnamed>")
        url = feed.get("url", "")
        status = {
            "name": name, "url": url, "status": "ok",
            "items_fetched": 0, "items_in_window": 0, "items_off_topic": 0,
            "error": None,
        }

        if not feed.get("enabled", True):
            status["status"] = "disabled"
            status["error"] = feed.get("note") or "disabled in feed config"
            feed_status.append(status)
            continue
        if not url:
            status["status"] = "error"
            status["error"] = "feed entry has no url"
            feed_status.append(status)
            continue

        try:
            entries = parse_feed(fetch(url, timeout))
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError) as exc:
            status["status"] = "error"
            status["error"] = f"{type(exc).__name__}: {exc}"
            feed_status.append(status)
            continue

        include = global_include + compile_patterns(feed.get("include"))
        exclude = global_exclude + compile_patterns(feed.get("exclude"))
        status["items_fetched"] = len(entries)
        raw_total += len(entries)

        for entry in entries:
            published = entry.get("published")
            if published is None or published < since:
                continue
            if not include_all and not matches_topic(entry, include, exclude):
                status["items_off_topic"] += 1
                continue
            entry["_feed"] = name
            entry["_feed_url"] = url
            if feed.get("scope_hint"):
                entry["feed_scope_hint"] = feed["scope_hint"]
            windowed.append(entry)
            status["items_in_window"] += 1

        feed_status.append(status)

    return feed_status, windowed, raw_total


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fetch and de-duplicate Entra ID change feeds.")
    ap.add_argument("--window", default="7d",
                    help="look-back window: 7d, 30d, week, month (default 7d)")
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="path to the feed config JSON")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap the number of items returned (0 = no cap)")
    ap.add_argument("--include-all", action="store_true",
                    help="skip the topic filters and keep every item in the window")
    ap.add_argument("--list-feeds", action="store_true",
                    help="print the configured channels and exit without fetching")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)

    if args.list_feeds:
        if not cfg["feeds"]:
            print(f"no feeds configured in {args.config}")
            print("Add your RSS/Atom channels to the 'feeds' array to enable "
                  "/last-entra-changes.")
            return 0
        for feed in cfg["feeds"]:
            state = "on " if feed.get("enabled", True) else "off"
            print(f"[{state}] {feed.get('name', '?')}  {feed.get('url', '')}")
        return 0

    label, days = parse_window(args.window)
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=days)
    timeout = int(cfg.get("defaults", {}).get("timeout_seconds", 30))

    feed_status, windowed, raw_total = collect(cfg, since, timeout, args.include_all)

    items = dedupe(sorted(windowed, key=lambda i: i["published"], reverse=True))
    items.sort(key=lambda i: i["published"], reverse=True)
    if args.limit > 0:
        items = items[: args.limit]

    for item in items:
        published = item.pop("published").astimezone(dt.timezone.utc)
        item["published"] = published.isoformat()
        item["published_date"] = published.strftime("%Y-%m-%d")
        item["canonical_url"] = canonical_url(item.get("url", ""))

    document = {
        "generated_at": now.isoformat(),
        "window": {"label": label, "days": days,
                   "since": since.isoformat(), "until": now.isoformat()},
        "stats": {
            "feeds_configured": len(feed_status),
            "feeds_ok": len([f for f in feed_status if f["status"] == "ok"]),
            "feeds_failed": len([f for f in feed_status if f["status"] == "error"]),
            "feeds_disabled": len([f for f in feed_status if f["status"] == "disabled"]),
            "raw_items_fetched": raw_total,
            "items_in_window": len(windowed),
            "items_after_dedup": len(items),
            "duplicates_merged": len(windowed) - len(items),
        },
        "feed_status": feed_status,
        "items": items,
    }

    if not cfg["feeds"]:
        document["warning"] = (
            f"No RSS/Atom channels are configured in {args.config}. Add entries to "
            "the 'feeds' array before running /last-entra-changes."
        )

    payload = json.dumps(document, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"wrote {len(items)} de-duplicated items ({label}) to {args.out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
