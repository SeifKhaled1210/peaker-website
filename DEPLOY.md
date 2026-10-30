# Deploying the Peaker website to your VPS

Tested setup: Ubuntu 22.04 or 24.04, nginx, Python 3 (already on Ubuntu). About 20 minutes.

The site is plain static files (fast, nothing to hack), plus one small Python service that
receives the contact form and creates a lead in your Odoo CRM.

---

## 0. Before you start

1. Point your domain's DNS to the VPS: an **A record** for `yourdomain.com` and one for
   `www.yourdomain.com`, both to the server's IP.
2. Fill in **src/site.json** (domain, email, phone, WhatsApp number) and run the build
   (see README.md). The `dist/` folder in this package still has placeholder contacts.

## 1. Install nginx and certbot

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

## 2. Upload the website

From your computer, in this folder:

```bash
rsync -av --delete dist/ youruser@YOUR_SERVER_IP:/tmp/peaker-dist/
```

On the server:

```bash
sudo mkdir -p /var/www/peaker
sudo rsync -a --delete /tmp/peaker-dist/ /var/www/peaker/
sudo chown -R www-data:www-data /var/www/peaker
```

## 3. Set up the contact form service

Create a user for it and copy the files:

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin peaker
sudo mkdir -p /opt/peaker /etc/peaker /var/lib/peaker
sudo cp server/lead_server.py /opt/peaker/
sudo cp deploy/lead.env.example /etc/peaker/lead.env
sudo chown peaker:peaker /var/lib/peaker
sudo chmod 600 /etc/peaker/lead.env && sudo chown peaker:peaker /etc/peaker/lead.env
```

**Create an Odoo API key** for the website:

1. In Odoo, create a user such as "Website Leads" with access to CRM (Salesman is enough).
2. Log in as that user, open **Preferences → Account Security → New API Key**.
3. Copy the key into `/etc/peaker/lead.env` with your Odoo URL, database and the user's login:

```bash
sudo nano /etc/peaker/lead.env
```

Start the service:

```bash
sudo cp deploy/peaker-lead.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now peaker-lead
curl http://127.0.0.1:8081/api/health      # should print {"ok": true}
```

## 4. Configure nginx

```bash
sudo cp deploy/nginx-peaker.conf /etc/nginx/sites-available/peaker
sudo sed -i 's/yourdomain.com/YOURREALDOMAIN.com/g' /etc/nginx/sites-available/peaker
sudo ln -s /etc/nginx/sites-available/peaker /etc/nginx/sites-enabled/peaker
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

## 5. Turn on HTTPS

```bash
sudo certbot --nginx -d YOURREALDOMAIN.com -d www.YOURREALDOMAIN.com
```

Choose the option to redirect HTTP to HTTPS. Certificates renew automatically.

## 6. Test

- Open `https://www.YOURREALDOMAIN.com` and `/ar/` on your phone and laptop.
- Send a test message from the contact page. It should appear in **Odoo → CRM → Leads**
  within seconds.
- If Odoo is ever unreachable, leads are kept in `/var/lib/peaker/leads.csv`, so nothing is lost.
  Check that file once after launch, then occasionally.
- Paste your URL into https://www.opengraph.xyz to check the WhatsApp and LinkedIn preview.
- Submit `https://www.YOURREALDOMAIN.com/sitemap.xml` in Google Search Console.

## Updating the site later

Edit the text, run `python3 build.py`, then repeat the `rsync` in step 2. No restart needed.

## Useful commands

```bash
sudo systemctl status peaker-lead        # is the form service running?
sudo journalctl -u peaker-lead -n 50     # its recent log
sudo tail -f /var/log/nginx/error.log    # web server errors
```
