# Novel Reader — Cloudflare Pages + R2 (development branch)

This branch preserves the GitHub Pages production site on `main`. Deploy this **branch** as a separate Cloudflare Pages project, not as the current GitHub Pages workflow.

## Cloudflare Pages
- Connect repository: `sakondev/novel-reader`
- Production branch **for the new Cloudflare project only**: `feature/cloudflare-audiobook`
- Framework preset: None
- Build command: `python reader/build.py --out dist`
- Build output directory: `dist`
- Root directory: repository root
- Python 3.12 recommended. No Node.js or npm necessary.
- Do not modify the existing GitHub Pages deployment on `main`.

## Cloudflare R2
1. Create an R2 Standard bucket (e.g. `novel-audio`). Keep credentials out of Git.
2. Upload an approved MP3 at key `pick-up-grimoire/chapter-0001.mp3` with `Content-Type: audio/mpeg`.
3. Use an R2 custom domain such as `audio.example.com` for public playback. `r2.dev` is for development, not production.
4. Confirm HTTPS streaming, seeking (HTTP Range requests), mobile playback, and content rights before public release. Public object URLs are not access controlled.
5. Put the public URL in the novel's `audio.json` manifest. No secrets are required in the static site.

Example `Pick Up Grimoire - Become a Mage/audio.json`:
```json
{
  "chapters": {
    "1": {"url": "https://audio.example.com/pick-up-grimoire/chapter-0001.mp3"},
    "2": {"url": "https://audio.example.com/pick-up-grimoire/chapter-0002.mp3"}
  }
}
```
Only chapters with an explicit HTTPS MP3 URL show the audio button. Unlisted chapters remain reading-only. The browser's native audio controls provide play/pause/scrubbing, with a saved listening position and speed selection. No browser TTS or paid voice synthesis is used.

## Local verification
```powershell
py -m unittest discover -s tests -v
py reader/build.py --out dist
py -m http.server 8000 -d dist
```

## Deployment protection
Publishing to R2 and Cloudflare Pages requires rights clearance for the text and audio. GitHub Pages stays unchanged until separately approved. Do not upload MP3 into the Git repository. Do not put API tokens or R2 keys in client-side code.
