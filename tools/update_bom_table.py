"""Rebuild the BOM table at the top of README.md from bom.csv.

Run from the repo root:  python3 tools/update_bom_table.py
"""
import csv

START, END = "<!-- BOM:START -->", "<!-- BOM:END -->"

def money(v):
    if v == "":
        return ""
    f = float(v)
    return f"{f:,.0f}" if f == int(f) else f"{f:,.2f}"

rows = list(csv.reader(open("bom.csv", newline="")))[1:]
lines = ["| Item | Qty | Rs each | Store | Status | Link |", "|---|---:|---:|---|---|---|"]
for item, qty, price, store, status, link in rows:
    if item.startswith("TOTAL"):
        lines.append(f"| **{item}** | | **{money(price)}** | | {status} | |")
    else:
        lk = "owned" if link == "owned" else (f"[link]({link})" if link else "none yet")
        lines.append(f"| {item} | {qty} | {money(price)} | {store} | {status} | {lk} |")
table = "\n".join(lines)

s = open("README.md").read()
a, b = s.index(START), s.index(END)
s = s[:a] + START + "\n" + table + "\n" + s[b:]
open("README.md", "w").write(s)
print("updated", len(rows), "rows")
