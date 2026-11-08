#!/usr/bin/env python3
"""ARCHIUM: publish approved new articles from news.json to Telegram.
The bot token is read from GitHub Actions secrets, never from public files.
Initial news.json import is deliberately silent.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CHANNEL = '@archium_horizon'
MAX_POSTS_PER_PUSH = 8

def load_posts(text: str) -> dict:
    raw = json.loads(text)
    posts = raw.get('posts') if isinstance(raw, dict) else raw
    if not isinstance(posts, list):
        raise ValueError('news.json должен содержать массив posts')
    result = {}
    for post in posts:
        if not isinstance(post, dict):
            raise ValueError('Элемент posts должен быть объектом')
        post_id = post.get('id')
        if not isinstance(post_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{3,100}', post_id):
            raise ValueError('Недопустимый id новости')
        if post_id in result:
            raise ValueError('Повторный id: ' + post_id)
        result[post_id] = post
    return result

def previous_posts(before_sha: str) -> dict | None:
    if not before_sha or re.fullmatch(r'0+', before_sha):
        print('Первый коммит: начальная загрузка без анонсов.')
        return None
    check = subprocess.run(['git', 'cat-file', '-e', before_sha+'^{commit}'], capture_output=True)
    if check.returncode != 0:
        raise RuntimeError('Предыдущий коммит недоступен: остановка во избежание дублей')
    p = subprocess.run(['git', 'show', before_sha+':news.json'],
                       capture_output=True, text=True, encoding='utf-8')
    if p.returncode != 0:
        print('Первая загрузка news.json: старые статьи не рассылаем.')
        return None
    return load_posts(p.stdout)

def outgoing(before: dict, after: dict) -> list:
    new = []
    for id_, post in after.items():
        if post.get('status') != 'published' or post.get('telegram_announce') is not True:
            continue
        old = before.get(id_)
        was_announced = old is not None and old.get('status') == 'published' and old.get('telegram_announce') is True
        if not was_announced:
            new.append(post)
    return new

def telegram_message(post: dict, site_url: str) -> tuple[str, str]:
    title = str(post.get('title') or 'Новость ARCHIUM').strip()[:120]
    intro = str(post.get('intro') or '').strip()[:330]
    category = str(post.get('category') or 'ARCHIUM').strip()[:55]
    text = f'📡 СВОДКИ ARCHIUM · {category}\n\n{title}'
    if intro:
        text += '\n\n' + intro
    text += '\n\nЧитать полностью на портале ARCHIUM.'
    url = site_url.rstrip('/') + '/?' + urlencode({'news': post['id']})
    return text[:3900], url

def send(token: str, chat_id: str, message: str, link: str) -> None:
    payload = json.dumps({
        'chat_id': chat_id,
        'text': message,
        'link_preview_options': {'is_disabled': True},
        'reply_markup': {'inline_keyboard': [[{'text': 'Читать в ARCHIUM', 'url': link}]]}
    }, ensure_ascii=False).encode('utf-8')
    req = Request('https://api.telegram.org/bot' + token + '/sendMessage',
                  data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urlopen(req, timeout=25) as resp:
            result = json.load(resp)
    except HTTPError as exc:
        raise RuntimeError(f'Telegram вернул HTTP {exc.code}; проверь бота и права публикации') from None
    except URLError:
        raise RuntimeError('Telegram недоступен') from None
    if not result.get('ok'):
        raise RuntimeError('Telegram отклонил публикацию; проверь права бота')

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--before-sha', default=os.getenv('BEFORE_SHA', ''))
    parser.add_argument('--after-file', default='news.json')
    parser.add_argument('--before-file', help='Для локального теста вместо git history')
    parser.add_argument('--site-url', default=os.getenv('ARCHIUM_SITE_URL', 'https://666danya.github.io/archium-beta/'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    after = load_posts(Path(args.after_file).read_text(encoding='utf-8'))
    if args.before_file:
        before = load_posts(Path(args.before_file).read_text(encoding='utf-8'))
    else:
        before = previous_posts(args.before_sha)
    if before is None:
        print('Пропуск первой загрузки новостного файла.')
        return 0
    posts = outgoing(before, after)
    print(f'Новых одобренных для Telegram публикаций: {len(posts)}')
    if len(posts) > MAX_POSTS_PER_PUSH:
        raise RuntimeError('Больше 8 анонсов за раз: остановлено для защиты от спама')
    if not posts:
        return 0
    token = os.getenv('ARCHIUM_TELEGRAM_BOT_TOKEN', '')
    if not args.dry_run and not token:
        print('Секрет ARCHIUM_TELEGRAM_BOT_TOKEN не задан, анонсы пропущены.')
        return 0
    for post in posts:
        message, link = telegram_message(post, args.site_url)
        print('Анонс:', post['id'], post.get('title', ''))
        if args.dry_run:
            print('--- ПРЕДПРОСМОТР ---\n' + message + '\nСсылка: ' + link + '\n---')
        else:
            send(token, CHANNEL, message, link)
            print('Успешно опубликовано в канале:', post['id'])
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print('Ошибка:', exc, file=sys.stderr)
        sys.exit(1)
