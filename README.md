# Peaker website

Bilingual (English / Arabic) website for Peaker. Static, fast, self-hosted on your VPS.
The contact form sends leads straight into Odoo CRM.

## What's in this folder

| Folder / file | What it is |
| --- | --- |
| `dist/` | The finished website. This is what goes on the server. |
| `src/content/en.json`, `src/content/ar.json` | **All the text on the site.** Edit these to change wording. |
| `src/site.json` | Domain, email, phone, WhatsApp, social links, founder details. |
| `src/templates/` | Page layouts (HTML). |
| `src/assets/` | Styles, script, fonts, logos, social preview images. |
| `build.py` | Turns `src/` into `dist/`. |
| `server/lead_server.py` | The contact form service (creates Odoo CRM leads). Python standard library only. |
| `deploy/` | nginx config, the service file and the settings template. |
| `DEPLOY.md` | Step-by-step server setup. |
| `previews/` | Screenshots of the site. |

## Changing the site

```bash
pip install jinja2        # once
python3 build.py          # rebuilds dist/
```

Then upload `dist/` again (DEPLOY.md, step 2).

## Before launch: checklist

- [ ] `src/site.json`: real domain (with https://www.). Email is currently your Gmail; switch to hello@yourdomain once the domain email exists
- [ ] `src/site.json`: LinkedIn / Instagram / Facebook links once the pages exist (empty ones are hidden)
- [ ] Read your bio on the About page and the Work page case studies, and correct anything
- [ ] Confirm every claim matches what you deliver, especially the ETA e-invoicing line on the Odoo page
- [ ] Run `python3 build.py`, deploy, and send a test lead
- [ ] Add Google Search Console and an analytics tool if you want visitor stats (update the
      Content-Security-Policy in the nginx config to allow the analytics domain)

## Pages

English: `/`, `/services/`, `/work/`, `/odoo/`, `/about/`, `/contact/` — Arabic: the same under `/ar/`.
Portfolio demo pages live in `src/static/work/demos/`; Work page images in `src/assets/img/work/`.
Each page links to its translation, and search engines are told the two versions belong together.

## Built in

Responsive down to small phones · right-to-left Arabic layout · self-hosted fonts (no Google requests) ·
strict security headers · spam trap and rate limiting on the form · leads never lost (CSV backup) ·
sitemap, robots.txt, social preview images, structured data for Google · keyboard and screen-reader
friendly · respects reduced-motion settings.
