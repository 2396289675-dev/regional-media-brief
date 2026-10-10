#!/usr/bin/env python3
"""
区域媒体情况简报 markdown -> 单文件 HTML

产出特点：
  - 零第三方依赖（只用标准库），Python 3.8+ 可跑
  - 单个 .html 文件，不引任何 CDN / 外部字体 / 外部图片，双击即可打开
  - 版式自适应（<=720px 转单列），可直接用 iframe 嵌入任意网站
  - 左侧 sticky 目录，右侧正文；打印友好

用法:
    python3 build_html.py brief.md ~/Desktop/浙江媒体情况简报.html

支持的 markdown 语法（与 build_docx.py 同一子集）:
    # 一级标题（封面大标题，全篇一次）
    ## 二级标题（体系章节）
    ### 三级标题
    **加粗**（含段首「定位：」这类标签）
    ==红色加粗==（现场重点句）
    1. 有序列表
    | a | b |  连续行 -> 表格，首行为表头
"""

import datetime
import html
import os
import re
import sys

# --------------------------------------------------------------------------
# 行内标记：先转义，再还原 ** 与 ==
# --------------------------------------------------------------------------
def inline(text):
    """把含 **bold** / ==red== 的文本转成 HTML 行内片段。"""
    out = []
    i = 0
    n = len(text)
    # 先把 &<> 转义，注意后面匹配基于转义后的文本（标记符号不受影响）
    text = html.escape(text, quote=False)
    while i < n:
        if text.startswith("==", i):
            j = text.find("==", i + 2)
            if j != -1 and j > i + 2:
                out.append('<em class="hl">%s</em>' % text[i + 2 : j])
                i = j + 2
                continue
        if text.startswith("**", i):
            j = text.find("**", i + 2)
            if j != -1 and j > i + 2:
                out.append("<strong>%s</strong>" % text[i + 2 : j])
                i = j + 2
                continue
        # 普通字符：吃到下一个标记起点
        nxt = n
        for mark in ("**", "=="):
            k = text.find(mark, i)
            if k != -1:
                nxt = min(nxt, k)
        if nxt <= i:
            nxt = i + 1
        out.append(text[i:nxt])
        i = nxt
    return "".join(out)


LABEL_RE = re.compile(r"^<strong>([^<]{1,20}[：:])</strong>")


def paragraph_html(text):
    """段首「**定位：**」这类标签渲染成独立小标。"""
    s = inline(text)
    m = LABEL_RE.match(s)
    if m:
        return '<p class="tagged"><span class="lbl">%s</span>%s</p>' % (
            m.group(1),
            s[m.end() :],
        )
    return "<p>%s</p>" % s


def is_table_row(line):
    s = line.strip()
    return s.startswith("|") and s.endswith("|") and len(s) > 1


def is_separator_row(line):
    return bool(re.fullmatch(r"\|[\s:\-|]+\|", line.strip()))


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


# --------------------------------------------------------------------------
# markdown -> 结构化块
# --------------------------------------------------------------------------
def parse(md_text):
    """返回 (title, blocks)。blocks 元素为 dict: type/h2/h3/p/table/list。"""
    title = ""
    blocks = []
    buf = []
    rows = []
    items = []

    def flush_p():
        if buf:
            t = "".join(buf).strip()
            if t:
                blocks.append({"type": "p", "text": t})
            buf.clear()

    def flush_table():
        if rows:
            blocks.append({"type": "table", "rows": [r[:] for r in rows]})
            rows.clear()

    def flush_list():
        if items:
            blocks.append({"type": "list", "items": items[:]})
            items.clear()

    for raw in md_text.splitlines():
        line = raw.rstrip()
        s = line.strip()

        if not s:
            flush_p()
            flush_table()
            flush_list()
            continue

        if is_table_row(s):
            flush_p()
            flush_list()
            if not is_separator_row(s):
                rows.append(split_row(s))
            continue
        flush_table()

        m = re.match(r"^(1|[2-9])\.\s+(.*)$", s)
        if m:
            flush_p()
            items.append(m.group(2))
            continue
        flush_list()

        if s.startswith("### "):
            flush_p()
            blocks.append({"type": "h3", "text": s[4:].strip()})
        elif s.startswith("## "):
            flush_p()
            blocks.append({"type": "h2", "text": s[3:].strip()})
        elif s.startswith("# "):
            flush_p()
            title = s[2:].strip()
        else:
            buf.append(s)

    flush_p()
    flush_table()
    flush_list()
    return title, blocks


# --------------------------------------------------------------------------
# 渲染
# --------------------------------------------------------------------------
CSS = """
:root{
  --bg:#f4f5f7; --card:#ffffff; --ink:#1f2329; --ink-2:#4e5969; --ink-3:#86909c;
  --line:#e5e6eb; --brand:#0052d9; --brand-soft:#eef3ff; --hl:#c4281b; --hl-soft:#fdf0ee;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; padding:0; background:var(--bg); color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",
    "Microsoft YaHei","Source Han Sans SC","Noto Sans CJK SC",sans-serif;
  font-size:15px; line-height:1.75;
}
.wrap{max-width:1180px; margin:0 auto; padding:28px 20px 64px; display:grid;
  grid-template-columns:236px minmax(0,1fr); gap:28px; align-items:start}
.card{background:var(--card); border:1px solid var(--line); border-radius:14px}

/* ---- 封面 ---- */
.hero{grid-column:1/-1; padding:34px 34px 26px;
  background:linear-gradient(135deg,#0b3fa8 0%,#0052d9 52%,#2b7bf0 100%);
  border:none; color:#fff; border-radius:16px; position:relative; overflow:hidden}
.hero::after{content:""; position:absolute; right:-70px; top:-90px; width:280px; height:280px;
  border-radius:50%; background:rgba(255,255,255,.10)}
.hero h1{margin:0 0 10px; font-size:29px; line-height:1.3; font-weight:700; letter-spacing:.5px}
.hero .sub{font-size:14px; color:rgba(255,255,255,.92); margin-bottom:20px}
.hero .stats{display:flex; flex-wrap:wrap; gap:10px; position:relative}
.hero .stat{background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.22);
  border-radius:10px; padding:8px 14px; min-width:96px}
.hero .stat b{display:block; font-size:20px; line-height:1.2; font-weight:700}
.hero .stat span{font-size:12px; color:rgba(255,255,255,.85)}

/* ---- 目录 ---- */
.toc{position:sticky; top:20px; padding:16px 14px; max-height:calc(100vh - 48px); overflow:auto}
.toc h4{margin:2px 8px 12px; font-size:12px; letter-spacing:1.5px; color:var(--ink-3); font-weight:600}
.toc a{display:block; padding:7px 10px; margin-bottom:2px; border-radius:8px; color:var(--ink-2);
  text-decoration:none; font-size:13.5px; line-height:1.5}
.toc a:hover{background:var(--brand-soft); color:var(--brand)}
.toc a.lv3{padding-left:24px; font-size:12.5px; color:var(--ink-3)}
.toc a.on{background:var(--brand-soft); color:var(--brand); font-weight:600}

/* ---- 正文 ---- */
.doc{padding:8px 34px 30px; min-width:0}
h2{font-size:20px; margin:32px 0 14px; padding:0 0 10px; border-bottom:2px solid var(--line);
  color:var(--ink); font-weight:700; scroll-margin-top:20px}
h2:first-child{margin-top:22px}
h2 .num{display:inline-block; min-width:30px; height:30px; line-height:30px; text-align:center;
  background:var(--brand); color:#fff; border-radius:8px; font-size:15px; margin-right:10px}
h3{font-size:16px; margin:24px 0 10px; color:var(--brand); font-weight:700; scroll-margin-top:20px}
p{margin:0 0 12px; color:var(--ink-2); text-align:justify}
p.tagged{background:#fafbfc; border-left:3px solid var(--brand); padding:12px 14px; border-radius:0 8px 8px 0}
.lbl{display:inline-block; margin-right:8px; padding:1px 8px; border-radius:5px;
  background:var(--brand-soft); color:var(--brand); font-weight:700; font-size:13.5px}
strong{color:var(--ink); font-weight:700}
em.hl{font-style:normal; font-weight:700; color:var(--hl); background:var(--hl-soft);
  padding:1px 4px; border-radius:4px; box-shadow:inset 0 -1px 0 rgba(196,40,27,.25)}
ol{margin:0 0 14px; padding-left:22px}
ol li{margin-bottom:10px; color:var(--ink-2); text-align:justify}
ol li::marker{color:var(--brand); font-weight:700}

table{width:100%; border-collapse:collapse; margin:6px 0 18px; font-size:13.5px;
  display:block; overflow-x:auto; white-space:nowrap}
@media(min-width:900px){table{white-space:normal; display:table}}
th,td{border:1px solid var(--line); padding:9px 12px; text-align:left; vertical-align:top; line-height:1.7}
th{background:#f2f5fa; color:var(--ink); font-weight:700; white-space:nowrap}
td{color:var(--ink-2)}
tbody tr:nth-child(even) td{background:#fcfcfd}

.foot{grid-column:1/-1; margin-top:6px; padding:16px 20px; font-size:12.5px; color:var(--ink-3);
  background:transparent; border:none; text-align:center; line-height:1.9}

@media(max-width:860px){
  .wrap{grid-template-columns:1fr; padding:16px 12px 48px; gap:16px}
  .hero{padding:24px 20px 20px} .hero h1{font-size:23px}
  .toc{position:static; max-height:none}
  .doc{padding:6px 18px 24px}
  h2{font-size:18px} .toc a.lv3{padding-left:20px}
}
@media print{
  body{background:#fff} .wrap{display:block; max-width:none; padding:0}
  .toc,.foot{display:none} .card{border:none}
  .hero{background:#0052d9 !important; -webkit-print-color-adjust:exact; print-color-adjust:exact}
  h2{page-break-after:avoid} table{page-break-inside:avoid}
}
"""

JS = """
(function(){
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  var heads = links.map(function(a){ return document.getElementById(a.getAttribute('href').slice(1)); });
  function onScroll(){
    var idx = 0;
    for (var i = 0; i < heads.length; i++){
      if (heads[i] && heads[i].getBoundingClientRect().top <= 90) idx = i;
    }
    links.forEach(function(a, i){ a.classList.toggle('on', i === idx); });
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();
})();
"""


def render(md_text, src_path=None):
    title, blocks = parse(md_text)

    # 统计
    n_sys = sum(1 for b in blocks if b["type"] == "h2") - 1
    n_tbl = sum(1 for b in blocks if b["type"] == "table")
    chars = sum(
        len(b.get("text", ""))
        or sum(len(c) for r in b.get("rows", []) for c in r)
        for b in blocks
    )
    n_sys = max(n_sys, 0)
    stamp = datetime.date.today().strftime("%Y-%m-%d")

    # 正文
    body = []
    toc = []
    seq = 0
    h2_seq = 0
    for b in blocks:
        t = b["type"]
        if t == "h2":
            h2_seq += 1
            seq += 1
            aid = "s%d" % seq
            toc.append((aid, b["text"], 2))
            num = '<span class="num">%d</span>' % h2_seq if h2_seq > 1 else ""
            body.append('<h2 id="%s">%s%s</h2>' % (aid, num, html.escape(b["text"])))
        elif t == "h3":
            seq += 1
            aid = "s%d" % seq
            toc.append((aid, b["text"], 3))
            body.append('<h3 id="%s">%s</h3>' % (aid, html.escape(b["text"])))
        elif t == "p":
            body.append(paragraph_html(b["text"]))
        elif t == "list":
            lis = "".join("<li>%s</li>" % inline(x) for x in b["items"])
            body.append("<ol>%s</ol>" % lis)
        elif t == "table":
            rows = b["rows"]
            head = "".join("<th>%s</th>" % inline(c) for c in rows[0])
            trs = []
            for r in rows[1:]:
                tds = "".join("<td>%s</td>" % inline(c) for c in r)
                trs.append("<tr>%s</tr>" % tds)
            body.append(
                '<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
                % (head, "".join(trs))
            )

    toc_html = "".join(
        '<a class="%s" href="#%s">%s</a>' % ("lv3" if lv == 3 else "", aid, html.escape(t))
        for aid, t, lv in toc
    )

    doc = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{title}——区域媒体生态、经营现状与拜访切入点">
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <header class="card hero">
    <h1>{title}</h1>
    <div class="sub">区域媒体生态摸底 · 主管单位与性质 / 近年战绩 / 奖项 / 经营与技术 / 腾讯可谈的切入点</div>
    <div class="stats">
      <div class="stat"><b>{n_sys}</b><span>覆盖体系</span></div>
      <div class="stat"><b>{n_tbl}</b><span>数据表格</span></div>
      <div class="stat"><b>{chars}</b><span>正文字数</span></div>
      <div class="stat"><b>{stamp}</b><span>生成日期</span></div>
    </div>
  </header>
  <nav class="card toc">
    <h4>目 录</h4>
    {toc}
  </nav>
  <main class="card doc">
{body}
  </main>
  <div class="foot">
    本页由区域媒体情况简报生成器自动渲染，单文件、无外部依赖，可直接嵌入内网或站点。<br>
    文中「待现场核实」及红色标记项，需在拜访前确认。
  </div>
</div>
<script>{js}</script>
</body>
</html>
""".format(
        title=html.escape(title or "区域媒体情况简报"),
        css=CSS,
        js=JS,
        toc=toc_html,
        body="\n".join(body),
        n_sys=n_sys,
        n_tbl=n_tbl,
        chars=chars,
        stamp=stamp,
    )
    return doc


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".html"
    with open(os.path.expanduser(src), encoding="utf-8") as f:
        md_text = f.read()
    out = os.path.expanduser(dst)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(md_text, src))
    print("saved:", out)


if __name__ == "__main__":
    main()
