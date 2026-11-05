"""Render public contribution totals and WakaTime language totals as local SVGs."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


def request_json(url, token, payload=None):
    if not token:
        raise RuntimeError('Required token is missing')
    req = Request(url, data=json.dumps(payload).encode() if payload else None,
                  headers={'Authorization': 'Bearer ' + token,
                           'Content-Type': 'application/json',
                           'User-Agent': 'YEY11-profile-cards'})
    with urlopen(req, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError('API data is not ready; rerun this workflow later')
        result = json.load(response)
    if result.get('errors') or result.get('error'):
        raise RuntimeError('API returned an error; check token permissions')
    return result


def frame(title, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" '
            f'viewBox="0 0 900 {height}" role="img"><title>{escape(title)}</title>'
            '<style>text{font-family:Arial,sans-serif;fill:#24292f;font-size:14px}'
            '.title{font-size:20px;font-weight:600}.muted{fill:#57606a}</style>'
            f'<rect x="1" y="1" width="898" height="{height-2}" rx="10" '
            'fill="#ffffff" stroke="#d0d7de"/>'
            f'<text class="title" x="24" y="34">{escape(title)}</text>{body}</svg>')


def activity_card(calendar):
    days = [d for week in calendar['weeks'] for d in week['contributionDays']][-90:]
    if not days:
        raise RuntimeError('GitHub returned no contribution dates')
    peak = max(1, max(d['contributionCount'] for d in days))
    coords = [(50 + i * 820 / max(1, len(days)-1),
               190 - 125 * d['contributionCount'] / peak) for i, d in enumerate(days)]
    points = ' '.join(f'{x:.1f},{y:.1f}' for x, y in coords)
    body = '<path d="M50 60V190H870" fill="none" stroke="#d0d7de"/>'
    body += f'<polygon points="50,190 {points} 870,190" fill="#dafbe1"/>'
    body += f'<polyline points="{points}" fill="none" stroke="#1a7f37" stroke-width="2"/>'
    body += f'<text x="24" y="65">{peak}</text><text x="24" y="194">0</text>'
    for (x, y), day in zip(coords, days):
        body += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#1a7f37">'
                 f'<title>{escape(day["date"])}: {day["contributionCount"]} contributions</title></circle>')
    body += f'<text class="muted" x="50" y="218">{escape(days[0]["date"])}</text>'
    body += f'<text class="muted" x="870" y="218" text-anchor="end">{escape(days[-1]["date"])}</text>'
    return frame('GitHub contributions · Last 90 days', 240, body)


def waka_card(data):
    if data.get('is_up_to_date') is False:
        raise RuntimeError('WakaTime is calculating stats; rerun later')
    languages = data.get('languages')
    if not isinstance(languages, list):
        raise RuntimeError('WakaTime did not return language statistics')
    body = ''
    for i, lang in enumerate(languages[:20]):
        y = 68 + i * 30
        pct = max(0, min(100, float(lang['percent'])))
        name = escape(str(lang['name']))
        body += f'<text x="24" y="{y}">{name}</text>'
        body += f'<rect x="205" y="{y-12}" width="440" height="12" rx="6" fill="#eaeef2"/>'
        body += f'<rect x="205" y="{y-12}" width="{4.4*pct:.2f}" height="12" rx="6" fill="#0969da"/>'
        detail = escape(str(lang.get('text', '')))
        body += f'<text x="665" y="{y}">{pct:.1f}% · {detail}</text>'
    if not languages:
        body = '<text class="muted" x="24" y="70">No coding activity recorded.</text>'
    return frame('WakaTime · All-time languages', max(100, 85 + 30*min(20, len(languages))), body)


def main():
    query = '''query($login:String!){user(login:$login){contributionsCollection{
      contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
    result = request_json('https://api.github.com/graphql', os.environ['GH_TOKEN'],
                          {'query': query, 'variables': {'login': os.environ['PROFILE_USER']}})
    calendar = result['data']['user']['contributionsCollection']['contributionCalendar']
    waka = request_json('https://api.wakatime.com/api/v1/users/current/stats/all_time',
                        os.environ['WAKA_TOKEN'])['data']
    # Write only after both APIs have returned valid data.
    cards = {'activity.svg': activity_card(calendar), 'wakatime.svg': waka_card(waka)}
    Path('profile').mkdir(exist_ok=True)
    for name, svg in cards.items():
        Path('profile', name).write_text(svg, encoding='utf-8')


if __name__ == '__main__':
    main()
