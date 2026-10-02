#!/usr/bin/env python3
"""Dựng bản HTML của note nghiên cứu UI Spec cho SI.

Nguồn duy nhất là note markdown trong vault; file này chỉ render.
    python3 Attachments/build-uispec-artifact.py            # dùng đường dẫn mặc định
    python3 Attachments/build-uispec-artifact.py <note.md> <out.html>
"""
import os, re, sys, html

CSS = """
  :root {
    --paper:#F3F4F8; --surface:#FFFFFF; --surface-2:#EDEFF5;
    --ink:#151A29; --ink-2:#4B5468; --ink-3:#78819A;
    --rule:#DCE0EA; --rule-2:#BEC5D6;
    --accent:#2B3F9E; --accent-2:#E6EAF8;
    --shadow:0 1px 0 rgba(21,26,41,.04);
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --paper:#0F1220; --surface:#161A28; --surface-2:#1D2231;
      --ink:#E8EBF3; --ink-2:#AEB6C8; --ink-3:#7F889D;
      --rule:#272D3E; --rule-2:#3A4256;
      --accent:#9AACFF; --accent-2:#1B2140; --shadow:none;
    }
  }
  :root[data-theme="dark"] {
    --paper:#0F1220; --surface:#161A28; --surface-2:#1D2231;
    --ink:#E8EBF3; --ink-2:#AEB6C8; --ink-3:#7F889D;
    --rule:#272D3E; --rule-2:#3A4256;
    --accent:#9AACFF; --accent-2:#1B2140; --shadow:none;
  }
  * { box-sizing: border-box; }
  body {
    background: var(--paper); color: var(--ink); margin: 0;
    font-family: "Be Vietnam Pro", "Helvetica Neue", Arial, sans-serif;
    font-size: 16px; line-height: 1.65; -webkit-font-smoothing: antialiased;
  }
  .page {
    display: grid;
    grid-template-columns:
      [full-start] minmax(20px,1fr)
      [text-start] min(70ch, calc(100% - 40px))
      [text-end] minmax(20px,1fr) [full-end];
    padding: 0 0 96px;
  }
  .page > * { grid-column: text; }
  .wide { grid-column: full; width: min(1080px, calc(100% - 40px)); margin-inline: auto; }
  h1,h2,h3 { font-family: Newsreader, Georgia, "Times New Roman", serif; font-weight:500; text-wrap:balance; margin:0; }
  h1 { font-size: clamp(2.1rem,5.2vw,3.05rem); line-height:1.1; letter-spacing:-.015em; }
  h2 { font-size: clamp(1.5rem,3.2vw,1.95rem); line-height:1.2; letter-spacing:-.01em; }
  h3 { font-size:1.16rem; line-height:1.35; font-weight:600; margin:34px 0 8px; }
  p { margin: 0 0 1rem; }
  a { color: var(--accent); text-underline-offset:.18em; text-decoration-thickness:.5px; }
  a:focus-visible { outline:2px solid var(--accent); outline-offset:3px; border-radius:2px; }
  strong { font-weight:600; }
  code { font-family:"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace; font-size:.855em; font-variant-ligatures:none; }
  p code, li code, td code, th code {
    background: var(--surface-2); border:1px solid var(--rule);
    border-radius:3px; padding:.06em .34em; white-space:nowrap;
  }
  .masthead { padding: 72px 0 0; }
  .eyebrow { font-size:.74rem; font-weight:600; letter-spacing:.13em; text-transform:uppercase; color:var(--accent); margin:0 0 18px; }
  .dek { font-family: Newsreader, Georgia, serif; font-size:1.24rem; line-height:1.5; color:var(--ink-2); margin:20px 0 0; max-width:58ch; }
  .intro { margin-top: 26px; padding-top:16px; border-top:1px solid var(--rule); color:var(--ink-2); font-size:.94rem; }
  section { margin-top: 62px; }
  .sec-head { display:flex; align-items:baseline; gap:14px; margin-bottom:10px; }
  .sec-num { font-family:"IBM Plex Mono",monospace; font-size:.82rem; font-weight:500; color:var(--accent); padding-top:.35em; flex:none; }
  .scroll { overflow-x:auto; margin:22px 0; border:1px solid var(--rule); background:var(--surface); box-shadow:var(--shadow); }
  table { border-collapse:collapse; width:100%; font-size:.875rem; }
  thead th {
    text-align:left; vertical-align:bottom; font-size:.7rem; font-weight:600;
    letter-spacing:.09em; text-transform:uppercase; color:var(--ink-3);
    background:var(--surface-2); padding:10px 14px; border-bottom:1px solid var(--rule-2); white-space:nowrap;
  }
  tbody td { padding:11px 14px; border-bottom:1px solid var(--rule); vertical-align:top; line-height:1.5; }
  tbody tr:last-child td { border-bottom:0; }
  tbody td:first-child { font-weight:500; }
  td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
  pre {
    margin:20px 0; padding:16px 18px; background:var(--surface); border:1px solid var(--rule);
    overflow-x:auto; box-shadow:var(--shadow); font-size:.82rem; line-height:1.6;
  }
  pre code { background:none; border:0; padding:0; white-space:pre; }
  .note { margin:24px 0; padding:16px 18px 6px; background:var(--surface); border:1px solid var(--rule-2); border-top:3px solid var(--ink-3); }
  .note p:last-child { margin-bottom:1rem; }
  ul, ol { margin:0 0 1rem; padding-left:1.25rem; }
  li { margin-bottom:.4rem; }
  li::marker { color:var(--ink-3); }
  ol li::marker { color:var(--accent); font-variant-numeric:tabular-nums; }
"""

HEAD = ('<title>Đường ống UI Spec cho SI</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Newsreader:opsz,wght@6..72,400;6..72,500&'
        'family=Be+Vietnam+Pro:wght@300;400;500;600&'
        'family=IBM+Plex+Mono:wght@400;500&display=swap">\n'
        '<style>' + CSS + '</style>\n')


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', lambda m: '<code>' + m.group(1) + '</code>', t)
    t = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', lambda m: m.group(2), t)
    t = re.sub(r'\[\[([^\]]+)\]\]', lambda m: '/'.join(m.group(1).split('/')[-2:]), t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: '<a href="' + m.group(2) + '">' + m.group(1) + '</a>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', lambda m: '<strong>' + m.group(1) + '</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', lambda m: '<em>' + m.group(1) + '</em>', t)
    return t


def cells(row):
    return [c.strip() for c in row.strip().strip('|').split('|')]


def build(md):
    md = re.sub(r'^---\n.*?\n---\n', '', md, flags=re.S)   # bỏ frontmatter
    lines = md.split('\n')
    out, i, in_section = [], 0, False
    n = len(lines)
    first_h1_done = False

    while i < n:
        ln = lines[i]

        if ln.startswith('```'):                            # code fence
            lang = ln[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].startswith('```'):
                buf.append(lines[i]); i += 1
            i += 1
            out.append('<pre><code>' + html.escape('\n'.join(buf), quote=False) + '</code></pre>')
            continue

        if ln.startswith('# ') and not first_h1_done:       # masthead
            first_h1_done = True
            title = ln[2:].strip()
            name, _, sub = title.partition(' — ')
            out.append('<header class="masthead">')
            out.append('<p class="eyebrow">Nghiên cứu khả thi · cập nhật 21-08-2026</p>')
            out.append('<h1>' + inline(name) + '</h1>')
            if sub:
                sub = sub[0].upper() + sub[1:]
                out.append('<p class="dek">' + inline(sub) + '</p>')
            out.append('</header>')
            i += 1
            # đoạn dẫn: mọi đoạn văn tới heading tiếp theo
            intro = []
            while i < n and not lines[i].startswith('#'):
                if lines[i].strip():
                    intro.append(inline(lines[i].strip()))
                i += 1
            if intro:
                out.append('<div class="intro">' + ''.join('<p>' + p + '</p>' for p in intro) + '</div>')
            continue

        if ln.startswith('## '):                            # section
            if in_section:
                out.append('</section>')
            in_section = True
            t = ln[3:].strip()
            m = re.match(r'^(\d+)\.\s*(.*)$', t)
            num, txt = (m.group(1).zfill(2), m.group(2)) if m else ('', t)
            out.append('<section><div class="sec-head">')
            if num:
                out.append('<span class="sec-num">' + num + '</span>')
            out.append('<h2>' + inline(txt) + '</h2></div>')
            i += 1
            continue

        if ln.startswith('### '):
            out.append('<h3>' + inline(ln[4:].strip()) + '</h3>')
            i += 1
            continue

        if ln.startswith('|') and i + 1 < n and re.match(r'^\|[\s:\-|]+\|$', lines[i + 1].strip()):
            head = cells(ln)
            align = ['num' if c.strip().endswith(':') and c.strip().startswith('-') else ''
                     for c in cells(lines[i + 1])]
            i += 2
            body = []
            while i < n and lines[i].strip().startswith('|'):
                body.append(cells(lines[i])); i += 1
            wide = ' wide' if len(head) >= 4 else ''
            t = ['<div class="scroll' + wide + '"><table><thead><tr>']
            for k, h in enumerate(head):
                cls = ' class="num"' if k < len(align) and align[k] else ''
                t.append('<th' + cls + '>' + inline(h) + '</th>')
            t.append('</tr></thead><tbody>')
            for r in body:
                t.append('<tr>')
                for k, c in enumerate(r):
                    cls = ' class="num"' if k < len(align) and align[k] else ''
                    t.append('<td' + cls + '>' + inline(c) + '</td>')
                t.append('</tr>')
            t.append('</tbody></table></div>')
            out.append(''.join(t))
            continue

        if ln.startswith('> '):                             # blockquote → hộp ghi chú
            buf = []
            while i < n and lines[i].startswith('>'):
                buf.append(lines[i].lstrip('>').strip()); i += 1
            out.append('<div class="note"><p>' + inline(' '.join(x for x in buf if x)) + '</p></div>')
            continue

        m = re.match(r'^(\d+)\.\s+(.*)$', ln)               # danh sách đánh số
        if m:
            items = []
            while i < n:
                mm = re.match(r'^(\d+)\.\s+(.*)$', lines[i])
                if not mm:
                    if lines[i].startswith('   ') and items:
                        items[-1] += ' ' + lines[i].strip(); i += 1; continue
                    break
                items.append(mm.group(2)); i += 1
            out.append('<ol>' + ''.join('<li>' + inline(x) + '</li>' for x in items) + '</ol>')
            continue

        if ln.startswith('- '):                             # danh sách gạch đầu dòng
            items = []
            while i < n and (lines[i].startswith('- ') or (lines[i].startswith('  ') and items)):
                if lines[i].startswith('- '):
                    items.append(lines[i][2:])
                else:
                    items[-1] += ' ' + lines[i].strip()
                i += 1
            out.append('<ul>' + ''.join('<li>' + inline(x) + '</li>' for x in items) + '</ul>')
            continue

        if ln.strip():                                      # đoạn văn
            buf = [ln.strip()]
            i += 1
            while i < n and lines[i].strip() and not re.match(r'^(#|\||>|- |\d+\.\s|```)', lines[i]):
                buf.append(lines[i].strip()); i += 1
            out.append('<p>' + inline(' '.join(buf)) + '</p>')
            continue

        i += 1

    if in_section:
        out.append('</section>')
    return HEAD + '<div class="page">\n' + '\n'.join(out) + '\n</div>\n'


VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(VAULT, '10_Projects', 'sapo-invoice', 'duong-ong-uispec-si.md')
DST = os.path.join(VAULT, 'Attachments', 'duong-ong-uispec-si.html')

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    dst = sys.argv[2] if len(sys.argv) > 2 else DST
    open(dst, 'w', encoding='utf-8').write(build(open(src, encoding='utf-8').read()))
    print('đã dựng', dst)
