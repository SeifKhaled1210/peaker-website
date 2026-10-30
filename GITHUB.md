# Preview the site on GitHub Pages

No coding tools needed: everything is done in the browser. About 10 minutes.
GitHub builds the site for you and republishes it whenever you change a file.

## 1. Create the repository

1. Go to github.com and sign in.
2. Click **+** (top right) → **New repository**.
3. Name it **peaker-website**. Choose **Public** (free GitHub Pages needs a public repo
   unless you're on a paid plan).
4. Don't add a README. Click **Create repository**.

## 2. Upload the files

1. On the new repo page, click **uploading an existing file**.
2. Open the unzipped `peaker-website` folder on your computer, select **everything inside it**
   (build.py, src, server, deploy, README.md, DEPLOY.md, GITHUB.md…) and drag it onto the page.
3. Click **Commit changes**.

## 3. Add the publishing workflow

Hidden folders (starting with a dot) often get skipped when dragging, so create this one by hand:

1. In the repo, click **Add file → Create new file**.
2. In the name box, type exactly: `.github/workflows/deploy.yml`
3. Open the file `.github/workflows/deploy.yml` from this package in any text editor,
   copy everything, and paste it into GitHub.
4. Click **Commit changes**.

## 4. Turn on GitHub Pages

1. Go to the repo's **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Open the **Actions** tab. If the workflow already ran and failed (because Pages was off),
   click it and press **Re-run all jobs**.

After 1–2 minutes your site is live at:

**https://YOUR-GITHUB-USERNAME.github.io/peaker-website/**

The Arabic version is at `/peaker-website/ar/`.

## Good to know

- **The contact form won't send on GitHub.** GitHub Pages only hosts files; the form needs
  the small Python service on your VPS. On the preview it shows the "couldn't send" message,
  which is expected.
- **Search engines are told to ignore the preview**, so it won't compete with your real domain later.
- **To change text**, open `src/content/en.json` or `ar.json` on GitHub, click the pencil icon,
  edit, and commit. The site rebuilds itself in about a minute.
