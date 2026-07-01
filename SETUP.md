# How to publish your GitHub profile README

## What was wrong with the old README

Your images broke because they relied on **shared public services that periodically go down**:

| Element | Old URL | Problem |
|---|---|---|
| Streak stats | `github-readme-streak-stats.herokuapp.com` | Heroku killed its free tier in Nov 2022 — host is dead |
| Stats / trophy cards | `github-readme-stats.vercel.app`, `github-profile-trophy.vercel.app` | Shared public instances hit Vercel's free-tier limit and get **paused** (they were down while this README was built) |

The new README fixes the streak domain, replaces the fragile repo "pin" cards with
hand-built badge cards (shields.io never goes down), and keeps only the stats/trophy
cards that depend on the shared instance — with an easy self-host option below.

---

## 1. Publish it (2 minutes)

The profile README lives in a **special repo named exactly after your username**.

```bash
# create the repo on GitHub named:  omkarrr88/omkarrr88   (Public, add a README)
git clone https://github.com/omkarrr88/omkarrr88.git
cd omkarrr88
cp /home/omkar-kadam/Desktop/github-profile/README.md .
git add README.md
git commit -m "New profile README"
git push
```

Open https://github.com/omkarrr88 — it renders on your profile.

---

## 2. Turn on the contribution snake (2 minutes)

The 🐍 snake image needs a GitHub Action to generate it (otherwise that one image 404s).

```bash
# inside the omkarrr88/omkarrr88 repo
mkdir -p .github/workflows
cp /home/omkar-kadam/Desktop/github-profile/.github/workflows/snake.yml .github/workflows/
git add .github/workflows/snake.yml
git commit -m "Add snake animation workflow"
git push
```

Then: repo → **Actions** tab → "Generate Snake Animation" → **Run workflow**.
It creates an `output` branch with the SVG; the README already points at it.

---

## 3. (Optional) 100% uptime for the stats + trophy cards

The main **GitHub Stats** card and **Trophies** still use the shared public instance.
They usually work, but if you want them to *never* break:

1. Fork **https://github.com/anuraghazra/github-readme-stats**
2. Deploy your fork to **Vercel** (free) — follow its README "Deploy Your Own" section,
   add a `PAT_1` env var (a GitHub personal access token).
3. In your README, replace `github-readme-stats.vercel.app` with your own domain,
   e.g. `omkarrr88-readme-stats.vercel.app`.

Do the same with **github-profile-trophy** for the trophy card if you like.

Everything else in the README (typing banner, streak, summary cards, activity graph,
project cards, badges, your photo) is already on healthy hosts and needs no setup.
