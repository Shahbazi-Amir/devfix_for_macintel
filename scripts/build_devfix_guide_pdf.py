#!/usr/bin/env python3
from pathlib import Path
import html
import re
import sys

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "DevFix_User_Guide_FA.md"
OUT = ROOT / "docs" / "DevFix_User_Guide_FA.pdf"

text = SRC.read_text(encoding="utf-8")
body = markdown.markdown(text, extensions=["fenced_code", "tables", "sane_lists"])

css = r'''
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
html, body, main, article, section { direction: rtl; text-align: right; }
body { font-family: "Amiri", serif; font-size: 12pt; line-height: 1.75; color: #111; }
h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption,caption,th,td { direction: rtl; text-align: right; }
h1 { font-size: 22pt; margin: 0 0 12pt; }
h2 { font-size: 16pt; margin-top: 18pt; break-after: avoid; }
h3 { font-size: 13.5pt; margin-top: 14pt; break-after: avoid; }
p { margin: 0 0 8pt; }
ul,ol { margin: 6pt 0 10pt; padding-right: 22pt; padding-left: 0; }
li { margin: 2pt 0; }
pre, code { direction: ltr; text-align: left; font-family: "DejaVu Sans Mono", monospace; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #f5f5f5; border: 1px solid #ddd; padding: 8pt; border-radius: 4pt; break-inside: avoid; }
code { font-size: 9.3pt; }
hr { border: 0; border-top: 1px solid #ddd; margin: 14pt 0; }
table { width: 100%; border-collapse: collapse; direction: rtl; margin: 8pt 0 12pt; }
th,td { border: 1px solid #bbb; padding: 5pt; vertical-align: top; }
a { direction: ltr; unicode-bidi: isolate; }
'''

doc = f'''<!doctype html>
<html lang="fa" dir="rtl">
<head><meta charset="utf-8"><title>راهنمای استفاده از DevFix روی Mac Intel</title><style>{css}</style></head>
<body><main><article>{body}</article></main></body>
</html>'''

OUT.parent.mkdir(parents=True, exist_ok=True)
HTML(string=doc, base_url=str(ROOT)).write_pdf(str(OUT))
print(OUT)
