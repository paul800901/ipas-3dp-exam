"""從官方學習指引 PDF 擷取樣題、答案與官方解析，並把需要看圖的題目截成圖片。

用法：python -I tools/parse_guides.py
輸出：tools/official_questions.json、app/img/*.png
"""
import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IMG = ROOT / "app" / "img"
OUT = ROOT / "tools" / "official_questions.json"

ANS_RE = re.compile(r"^\s*(\d+)\.\s*Ans\s*\(?\s*([A-D])\s*\)?")
Q_RE = re.compile(r"^\s*(\d+)\.\s*(\S.*)$")
OPT_RE = re.compile(r"^\s*\(([A-D])\)\s*(.*)$")
PAGE_RE = re.compile(r"^=== PAGE (\d+) ===")
HEADER_RE = re.compile(r"^[\s-]*(第.章\s.*|\d-\d+\s*|Source：.*)$")
STOP_RE = re.compile(r"^\s*(\d\.\d+\s|第.章|參考文獻|\[\d+\])")
FIG_HINT = re.compile(r"如圖|附圖|下圖|圖中|如下圖")


def load_lines(path):
    """回傳 [(page, text)]，去掉頁首與頁碼。"""
    out, page = [], 0
    skip_header = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = PAGE_RE.match(raw)
        if m:
            page = int(m.group(1))
            skip_header = True
            continue
        if skip_header and raw.strip():
            skip_header = False
            if HEADER_RE.match(raw):
                continue
        if HEADER_RE.match(raw):
            continue
        out.append((page, raw.rstrip()))
    return out


def join(parts):
    s = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if s and re.match(r"[A-Za-z0-9(（]", p[:1]) and re.search(r"[A-Za-z0-9,.)）]$", s):
            s += " "
        s += p
    return s.strip()


def parse(path):
    lines = load_lines(path)
    n = len(lines)
    # 找出答案群組
    ans_idx = [i for i, (_, t) in enumerate(lines) if ANS_RE.match(t)]
    groups, cur = [], []
    for i in ans_idx:
        num = int(ANS_RE.match(lines[i][1]).group(1))
        if num == 1 and cur:
            groups.append(cur)
            cur = []
        cur.append(i)
    if cur:
        groups.append(cur)

    results = []
    for g in groups:
        count = len(g)
        # 往回找題目 1..count
        q_starts = {}
        expect = count
        j = g[0] - 1
        while j >= 0 and expect >= 1:
            m = Q_RE.match(lines[j][1])
            if m and not ANS_RE.match(lines[j][1]) and int(m.group(1)) == expect:
                q_starts[expect] = j
                expect -= 1
            j -= 1
        if expect != 0:
            print(f"[warn] {path.name}: 群組起於第 {g[0]} 行，題目只找到 {count - expect}/{count}", file=sys.stderr)
        for k in range(1, count + 1):
            if k not in q_starts:
                continue
            s = q_starts[k]
            e = q_starts.get(k + 1, g[0])
            block = lines[s:e]
            stem, opts, cur_opt = [], {}, None
            first = Q_RE.match(block[0][1]).group(2)
            stem.append(first)
            for _, t in block[1:]:
                mo = OPT_RE.match(t)
                if mo:
                    cur_opt = mo.group(1)
                    opts[cur_opt] = [mo.group(2)]
                elif cur_opt:
                    opts[cur_opt].append(t)
                else:
                    stem.append(t)
            # 答案與解析
            ai = g[k - 1]
            am = ANS_RE.match(lines[ai][1])
            ae = g[k] if k < count else min(ai + 40, n)
            expl = []
            rest = lines[ai][1][am.end():].strip()
            if rest:
                expl.append(rest)
            for _, t in lines[ai + 1:ae]:
                if k == count and STOP_RE.match(t):
                    break
                expl.append(t)
            options = {key: re.sub(r"[；;。]\s*$", "", join(v)) for key, v in opts.items()}
            q_text = join(stem)
            needs_fig = bool(FIG_HINT.search(q_text)) or any(not v for v in options.values()) or len(options) < 4
            results.append({
                "page": block[0][0],
                "end_page": max(p for p, t in block if t.strip()),
                "num": k,
                "q": q_text,
                "options": [options.get(x, "") for x in "ABCD"],
                "answer": am.group(2),
                "official": join(expl),
                "needs_fig": needs_fig,
            })
    return results


def locate(page, items, idx):
    """回傳題目在頁面上的 y；同頁題目依序往下找，避免開頭字被前一題內文誤中。"""
    pno = page.number + 1
    prev_y, y = -1.0, None
    for i, it in enumerate(items[:idx + 1]):
        if it["page"] != pno:
            continue
        hits = sorted(page.search_for(it["q"][:10]), key=lambda r: r.y0)
        y = next((r.y0 for r in hits if r.y0 > prev_y + 5), None)
        if y is None:
            return None
        prev_y = y
    return y


def crop_figures(pdf_path, items, prefix):
    doc = fitz.open(pdf_path)
    for idx, it in enumerate(items):
        if not it["needs_fig"]:
            continue
        page = doc[it["page"] - 1]
        y = locate(page, items, idx)
        if y is None:
            print(f"[warn] 找不到題目位置 {prefix}-{idx}", file=sys.stderr)
            continue
        top = y - 4
        bottom = page.rect.height - 40
        # 同頁下一題的位置
        nxt = items[idx + 1] if idx + 1 < len(items) else None
        if nxt and nxt["page"] == it["page"]:
            y2 = locate(page, items, idx + 1)
            if y2:
                bottom = y2 - 2
        clip = fitz.Rect(page.rect.x0 + 30, top, page.rect.x1 - 30, bottom)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip)
        name = f"{prefix}-{idx + 1:03d}.png"
        pix.save(IMG / name)
        it["img"] = f"img/{name}"
        if it["end_page"] != it["page"]:
            page2 = doc[it["end_page"] - 1]
            b2 = page2.rect.height - 40
            if nxt and nxt["page"] == it["end_page"]:
                y3 = locate(page2, items, idx + 1)
                if y3:
                    b2 = y3 - 2
            clip2 = fitz.Rect(page2.rect.x0 + 30, 75, page2.rect.x1 - 30, b2)
            pix2 = page2.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip2)
            name2 = f"{prefix}-{idx + 1:03d}b.png"
            pix2.save(IMG / name2)
            it["img2"] = f"img/{name2}"


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    all_items = []
    for subj, fname in ((1, "guide1"), (2, "guide2")):
        items = parse(DATA / f"{fname}_text.txt")
        crop_figures(DATA / f"{fname}.pdf", items, f"s{subj}")
        for i, it in enumerate(items):
            it["id"] = f"s{subj}-{i + 1:03d}"
            it["subject"] = subj
        all_items += items
    OUT.write_text(json.dumps(all_items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"共 {len(all_items)} 題；需圖 {sum(1 for x in all_items if x['needs_fig'])} 題")


if __name__ == "__main__":
    main()
