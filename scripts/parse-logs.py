#!/usr/bin/env python3
"""
parse-logs.py — Parser de logs Nginx pour mesurer le crawl des bots IA.

Lit un fichier access.log au format Nginx combined, identifie les hits
des bots IA listés dans config/bots.json, agrège les volumes par bot,
page, jour, statut HTTP, puis produit un CSV brut + un rapport HTML.

Usage rapide :
    python parse-logs.py access.log --out ./report
    open report/report.html
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


NGINX_REGEX = re.compile(
    r'^(?P<ip>\S+) - (?P<user>\S+) '
    r'\[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>.+?) (?P<protocol>\S+)" '
    r'(?P<status>\d+) (?P<size>\d+|-) '
    r'"(?P<referer>[^"]*)" '
    r'"(?P<ua>[^"]*)"'
)

NGINX_TIME_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def load_bots(config_path):
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    bots = []
    for cat_id, cat in config['categories'].items():
        for bot in cat['bots']:
            bots.append({
                'id': bot['id'],
                'name': bot['name'],
                'pattern': re.compile(bot['pattern'], re.IGNORECASE),
                'category': cat_id,
                'category_label': cat['label'],
                'color': cat['color'],
                'purpose': bot['purpose'],
                'respects_robots': bot['respects_robots'],
            })
    return bots, config


def identify_bot(user_agent, bots):
    for bot in bots:
        if bot['pattern'].search(user_agent):
            return bot
    return None


def parse_line(line):
    m = NGINX_REGEX.match(line.strip())
    if not m:
        return None
    return m.groupdict()


def main():
    parser = argparse.ArgumentParser(
        description="Parse Nginx access logs et produit un rapport bot IA.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples :\n"
            "  python parse-logs.py access.log --out ./report\n"
            "  python parse-logs.py /var/log/nginx/access.log --out ./out --top-pages 30\n"
            "  python parse-logs.py access.log --csv-only --out ./csv\n"
        ),
    )
    parser.add_argument('logfile', help="Chemin vers le fichier access.log Nginx (format combined)")
    parser.add_argument('--out', '-o', default='./report', help="Dossier de sortie (defaut: ./report)")
    parser.add_argument('--top-pages', type=int, default=20, help="Top N pages affichees par bot (defaut: 20)")
    parser.add_argument('--config', default=None, help="Chemin vers bots.json (defaut: <script>/config/bots.json)")
    parser.add_argument('--csv-only', action='store_true', help="Ne produire que le CSV (pas de HTML)")

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    config_path = Path(args.config) if args.config else script_dir / 'config' / 'bots.json'

    if not config_path.exists():
        sys.exit(f"Erreur : config introuvable : {config_path}")

    log_path = Path(args.logfile)
    if not log_path.exists():
        sys.exit(f"Erreur : fichier log introuvable : {log_path}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    bots, _config = load_bots(config_path)

    total_lines = 0
    parsed_lines = 0
    bot_hits = []
    counter_bot = Counter()
    counter_bot_page = defaultdict(Counter)
    counter_bot_day = defaultdict(Counter)
    counter_bot_status = defaultdict(Counter)

    print(f"Parsing {log_path}...", file=sys.stderr)

    with open(log_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            total_lines += 1
            parsed = parse_line(line)
            if not parsed:
                continue
            parsed_lines += 1
            bot = identify_bot(parsed['ua'], bots)
            if not bot:
                continue
            try:
                dt = datetime.strptime(parsed['time'], NGINX_TIME_FORMAT)
                day = dt.strftime('%Y-%m-%d')
            except ValueError:
                day = 'unknown'
            hit = {
                'date': day,
                'time': parsed['time'],
                'bot_id': bot['id'],
                'bot_name': bot['name'],
                'category': bot['category'],
                'path': parsed['path'],
                'status': parsed['status'],
                'ip': parsed['ip'],
                'ua': parsed['ua'],
            }
            bot_hits.append(hit)
            counter_bot[bot['id']] += 1
            counter_bot_page[bot['id']][parsed['path']] += 1
            counter_bot_day[bot['id']][day] += 1
            counter_bot_status[bot['id']][parsed['status']] += 1

    print(f"Total lines  : {total_lines}", file=sys.stderr)
    print(f"Parsed lines : {parsed_lines}", file=sys.stderr)
    print(f"Bot hits     : {len(bot_hits)}", file=sys.stderr)

    csv_path = out_dir / 'hits.csv'
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['date', 'time', 'bot_id', 'bot_name', 'category', 'path', 'status', 'ip']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for hit in bot_hits:
            writer.writerow({k: hit[k] for k in fieldnames})
    print(f"CSV ecrit    : {csv_path}", file=sys.stderr)

    if args.csv_only:
        return

    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        sys.exit("Jinja2 manquant. Install : pip install jinja2 (ou pip install -r requirements.txt)")

    env = Environment(
        loader=FileSystemLoader(str(script_dir / 'templates')),
        autoescape=select_autoescape(['html']),
    )
    template = env.get_template('report.html')

    bots_by_id = {b['id']: b for b in bots}

    bot_stats = []
    for bot_id, count in counter_bot.most_common():
        bot = bots_by_id[bot_id]
        top_pages = counter_bot_page[bot_id].most_common(args.top_pages)
        days_data = sorted(counter_bot_day[bot_id].items())
        status_data = dict(counter_bot_status[bot_id])
        bot_stats.append({
            'id': bot_id,
            'name': bot['name'],
            'category_label': bot['category_label'],
            'category': bot['category'],
            'color': bot['color'],
            'purpose': bot['purpose'],
            'respects_robots': bot['respects_robots'],
            'total': count,
            'top_pages': top_pages,
            'days': days_data,
            'status': status_data,
        })

    ia_total = sum(counter_bot[b['id']] for b in bots if b['category'] != 'seo_classique')
    seo_total = sum(counter_bot[b['id']] for b in bots if b['category'] == 'seo_classique')

    all_days = sorted(set(h['date'] for h in bot_hits if h['date'] != 'unknown'))
    period_start = all_days[0] if all_days else 'N/A'
    period_end = all_days[-1] if all_days else 'N/A'

    daily_by_bot = {bot_id: [counter_bot_day[bot_id].get(d, 0) for d in all_days] for bot_id in counter_bot}

    html_path = out_dir / 'report.html'
    html = template.render(
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M'),
        period_start=period_start,
        period_end=period_end,
        total_lines=total_lines,
        parsed_lines=parsed_lines,
        bot_hits_total=len(bot_hits),
        ia_total=ia_total,
        seo_total=seo_total,
        bot_stats=bot_stats,
        all_days=all_days,
        daily_by_bot=daily_by_bot,
        bots_by_id=bots_by_id,
    )
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML ecrit   : {html_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
