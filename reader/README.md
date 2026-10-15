# Novel Reader v1
A static, mobile-first library built from each novel's `translated/chapter-NNNN.md`.

## Preview locally
```powershell
cd D:\Novel
py reader\build.py
py -m http.server 8000 -d _site
```
Open http://localhost:8000 on this computer. For another device on the same network, use the computer's LAN IP and ensure the firewall permits access.

## Automatic deploy
1. Create a GitHub repository, push the chosen public-site files to its `main` branch.
2. Repo Settings → Pages → Build and deployment → Source: **GitHub Actions**.
3. Each later push changing `*/translated/**`, `*/novel.yaml` or `reader/**` rebuilds and publishes the site.
4. Generated HTML lives in `_site/` (ignored), not in Git. No web server, API, database or extra Python packages required.

Only canonical translated Markdown is published. Never put a source manuscript, private editorial notes, keys or personal metadata in the website repo. For GitHub repository contents use selective git add or a dedicated publishing repo; use `.gitignore` guards.
