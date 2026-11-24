"""
Export the AI chat history the submission asks for.

The course requires the prompts used and the chat history to be submitted with
the supplementary file. Claude Code keeps a JSONL transcript of every session
under ~/.claude/projects/<encoded-cwd>/, so the export is produced from those
rather than retyped - which is the only way it can be an accurate record.

Writes two files to the project root:

  ai_chat_history.md   the readable conversation: every prompt verbatim, every
                       reply, and a one-line note of the tools each turn used.
                       Tool arguments and outputs are summarised rather than
                       dumped - the three transcripts total ~36 MB of mostly
                       file contents and command output, which is the code,
                       not the conversation.

  ai_prompts.md        the prompts on their own, verbatim, in order.

Both are regenerated from scratch on each run. Nothing is paraphrased: if a
line appears in quotation marks in either file, it was typed.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

ROOT = CM.ROOT
TRANSCRIPTS = Path.home() / ".claude" / "projects" / "C--Users-Siva-Desktop-AIBT"

# In chronological order, with the label used in the report.
SESSIONS = [
    ("0c98e32e-6b9c-4c3a-aaf0-8dd8c969c9c6",
     "Session 1", "inspection, cleaning decisions, EDA, the EDA report"),
    ("41d80354-5db1-46dc-a9e6-04faed0e1583",
     "Session 2", "hypothesis testing, PCA, clustering, progress report and slides"),
    ("f2d7441d-16b5-4913-aaa5-1ba4faf91d69",
     "Session 3", "step-8 validation, the 8-page report, the supplementary file"),
]

# Light scrub: the transcripts are submitted to a course, so anything that
# identifies an account rather than the work is removed.
SCRUB = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email removed]"),
    (re.compile(r"(sk-|ghp_|github_pat_)[A-Za-z0-9_-]{10,}"), "[token removed]"),
]

MAX_REPLY_CHARS = 2600          # a long reply is trimmed, never silently cut


def scrub(t):
    for pat, rep in SCRUB:
        t = pat.sub(rep, t)
    return t


def clean(t):
    """Strip the harness's own injections, which were never typed by anyone."""
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"<local-command-[^>]*>.*?</local-command-[^>]*>", "", t, flags=re.S)
    t = re.sub(r"<task-notification>.*?</task-notification>", "", t, flags=re.S)
    # a typed slash command is a harness instruction, not a prompt about the work
    t = re.sub(r"<command-\w+>.*?</command-\w+>", "", t, flags=re.S)
    return t.strip()


def blocks(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return [("text", c)]
    out = []
    for b in c or []:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text":
            out.append(("text", b.get("text", "")))
        elif b.get("type") == "tool_use":
            out.append(("tool", b.get("name", "?")))
    return out


def read_session(path):
    """Yield (role, timestamp, text, tools) in order, prompts and replies only."""
    turns = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("isSidechain"):
                continue
            kind = r.get("type")
            if kind not in ("user", "assistant"):
                continue
            ts = (r.get("timestamp") or "")[:19]
            texts, tools = [], []
            for btype, val in blocks(r.get("message", {})):
                if btype == "tool":
                    tools.append(val)
                else:
                    t = clean(val)
                    if t:
                        texts.append(t)
            body = "\n\n".join(texts).strip()
            if kind == "user":
                # tool results and image placeholders are not conversation
                if not body or body.startswith(("Caveat:", "[Image:",
                                                "[Request interrupted")):
                    continue
                if r.get("promptSource") not in ("typed", None):
                    continue
                if r.get("promptSource") is None and len(body) > 1500:
                    continue          # an injected skill or attachment, not a prompt
                turns.append(("user", ts, body, []))
            elif body or tools:
                turns.append(("assistant", ts, body, tools))
    return turns


def fmt_date(ts):
    try:
        return datetime.fromisoformat(ts).strftime("%d %B %Y, %H:%M")
    except Exception:
        return ts


def main():
    if not TRANSCRIPTS.is_dir():
        raise SystemExit("transcript directory not found: %s" % TRANSCRIPTS)

    hist = ["# AI chat history",
            "",
            "Complete conversation record for the BT3041 term project, exported "
            "from the Claude Code session transcripts by "
            "`analysis/13_export_ai_history.py`.",
            "",
            "Every prompt below is verbatim, including its typos. Assistant "
            "replies are reproduced in full up to %d characters and marked "
            "`[reply trimmed]` beyond that. Tool calls are listed by name: the "
            "arguments and outputs are the code and the data, which are in the "
            "repository rather than here. Email addresses and tokens are "
            "removed." % MAX_REPLY_CHARS,
            ""]
    prompts = ["# AI prompts used during the project",
               "",
               "Every prompt typed to the AI assistant, verbatim and in order, "
               "exported by `analysis/13_export_ai_history.py`.",
               ""]

    total_p = 0
    for sid, label, topic in SESSIONS:
        path = TRANSCRIPTS / (sid + ".jsonl")
        if not path.exists():
            print("  missing transcript:", path.name)
            continue
        turns = read_session(path)
        ptimes = [t for role, t, _, _ in turns if role == "user"]
        span = ("%s to %s" % (fmt_date(ptimes[0]), fmt_date(ptimes[-1]))
                if ptimes else "")
        n_p = len(ptimes)
        total_p += n_p

        head = "## %s - %s" % (label, topic)
        hist += [head, "", "*%s - %d prompts - session `%s`*" % (span, n_p, sid[:8]), ""]
        prompts += [head, "", "*%s*" % span, ""]

        i = 0
        for role, ts, body, tools in turns:
            body = scrub(body)
            if role == "user":
                i += 1
                hist += ["### Prompt %d  <small>(%s)</small>" % (i, fmt_date(ts)),
                         "", "> " + body.replace("\n", "\n> "), ""]
                prompts += ["**%d.** (%s)" % (i, fmt_date(ts)), "",
                            "> " + body.replace("\n", "\n> "), ""]
            else:
                if body:
                    if len(body) > MAX_REPLY_CHARS:
                        body = body[:MAX_REPLY_CHARS].rsplit(" ", 1)[0] + \
                               "\n\n*[reply trimmed]*"
                    hist += [body, ""]
                if tools:
                    uniq = []
                    for t in tools:
                        if not uniq or uniq[-1][0] != t:
                            uniq.append([t, 1])
                        else:
                            uniq[-1][1] += 1
                    listed = ", ".join("%s%s" % (n, "" if c == 1 else " x%d" % c)
                                       for n, c in uniq)
                    hist += ["<sub>tools used: %s</sub>" % listed, ""]
        hist += ["---", ""]
        prompts += ["---", ""]
        print("  %s: %d prompts, %d turns" % (label, n_p, len(turns)))

    (ROOT / "ai_chat_history.md").write_text("\n".join(hist), encoding="utf-8")
    (ROOT / "ai_prompts.md").write_text("\n".join(prompts), encoding="utf-8")
    for f in ("ai_chat_history.md", "ai_prompts.md"):
        print("  wrote %s (%.0f kB)" % (f, (ROOT / f).stat().st_size / 1024))
    print("  %d prompts across %d sessions" % (total_p, len(SESSIONS)))


if __name__ == "__main__":
    main()
