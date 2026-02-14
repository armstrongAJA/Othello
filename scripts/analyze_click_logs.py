import re
from datetime import datetime

DEBUG_LOG = 'othello_ui_debug.log'
EVENT_LOG = 'othello_ui.log'

# parse debug log for CANVAS PRESS/RELEASE
press_re = re.compile(r'^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*CANVAS PRESS x=(?P<x>[-\d]+) y=(?P<y>[-\d]+)')
release_re = re.compile(r'^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*CANVAS RELEASE x=(?P<x>[-\d]+) y=(?P<y>[-\d]+)')
click_re = re.compile(r'^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*CLICK pixels=\((?P<x>[-\d]+),(?P<y>[-\d]+)\)')

presses = []
releases = []
clicks = []

with open(DEBUG_LOG, 'r') as f:
    for line in f:
        m = press_re.search(line)
        if m:
            ts = datetime.strptime(m.group('ts'), '%Y-%m-%d %H:%M:%S')
            presses.append((ts, int(m.group('x')), int(m.group('y')), line.strip()))
        m = release_re.search(line)
        if m:
            ts = datetime.strptime(m.group('ts'), '%Y-%m-%d %H:%M:%S')
            releases.append((ts, int(m.group('x')), int(m.group('y')), line.strip()))

with open(EVENT_LOG, 'r') as f:
    for line in f:
        m = click_re.search(line)
        if m:
            ts = datetime.strptime(m.group('ts'), '%Y-%m-%d %H:%M:%S')
            clicks.append((ts, int(m.group('x')), int(m.group('y')), line.strip()))

# For each release, find a matching click within 1s and within 10px
issues = []
for rel in releases[-200:]:  # analyze last 200 releases for speed
    r_ts, rx, ry, r_line = rel
    matched = False
    for clk in clicks:
        c_ts, cx, cy, c_line = clk
        delta = (c_ts - r_ts).total_seconds()
        if 0 <= delta <= 1.0 and abs(cx - rx) <= 10 and abs(cy - ry) <= 10:
            matched = True
            break
    if not matched:
        issues.append(rel)

print(f'Total releases analyzed: {len(releases[-200:])}, unmatched releases: {len(issues)}')
for ts, x, y, line in issues[:50]:
    print(ts, x, y, line)

# Summary of PRESS without RELEASE nearby
# (find presses with no release within 1s)
prs_issues = []
for pr in presses[-200:]:
    p_ts, px, py, p_line = pr
    matched = False
    for rl in releases:
        r_ts, rx, ry, r_line = rl
        delta = (r_ts - p_ts).total_seconds()
        if 0 <= delta <= 1.0 and abs(px - rx) <= 10 and abs(py - ry) <= 10:
            matched = True
            break
    if not matched:
        prs_issues.append(pr)

print(f'Presses without release (last 200): {len(prs_issues)}')
for ts, x, y, line in prs_issues[:50]:
    print(ts, x, y, line)
