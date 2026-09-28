#!/usr/bin/env python3
"""Rewrite the contributor avatars in both READMEs from the GitHub API.

Contributors are the union of GitHub's contributor list (commit authors whose
email is linked to an account) and authors of merged pull requests, so people
whose commit email is not linked still appear. Standard library only.
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
READMES = [ROOT / "README.md", ROOT / "README.zh.md"]
START, END = "<!-- contributors:start -->", "<!-- contributors:end -->"
API = "https://api.github.com"


def get(path, token):
    request = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def pages(path, token):
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        items = get(f"{path}{separator}per_page=100&page={page}", token)
        if not items:
            return
        yield from items
        page += 1


def is_bot(user):
    return user.get("type") == "Bot" or user["login"].endswith("[bot]")


def collect(repo, token):
    people = {}
    for user in pages(f"/repos/{repo}/contributors", token):
        if not is_bot(user):
            people[user["login"]] = (user["contributions"], user["avatar_url"])
    for pull in pages(f"/repos/{repo}/pulls?state=closed", token):
        user = pull.get("user")
        if pull.get("merged_at") and user and not is_bot(user):
            people.setdefault(user["login"], (0, user["avatar_url"]))
    return [(login, avatar) for login, (_, avatar) in
            sorted(people.items(), key=lambda item: (-item[1][0], item[0].lower()))]


def render(people):
    lines = [START]
    for login, avatar in people:
        joiner = "&" if "?" in avatar else "?"
        lines.append(f'<a href="https://github.com/{login}" title="{login}">'
                     f'<img src="{avatar}{joiner}s=96" width="48" height="48" alt="{login}" /></a>')
    lines.append(END)
    return "\n".join(lines)


def update(text, block):
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if len(pattern.findall(text)) != 1:
        raise SystemExit("README must contain exactly one contributors block")
    return pattern.sub(lambda _: block, text)


def main():
    repo, token = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"]
    block = render(collect(repo, token))
    changed = False
    for path in READMES:
        text = path.read_text(encoding="utf-8")
        new = update(text, block)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed = True
    print("updated" if changed else "unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
