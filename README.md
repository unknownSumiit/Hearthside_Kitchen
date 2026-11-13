# Hearthside Kitchen — Recipe Website

A fast, static recipe website for US home cooks over 50. It is built mobile-first for **iPhone Safari**, structured to meet **Google AdSense** site requirements, and ready to deploy to **Azure Static Web Apps** from **GitHub**.

## What's included

```
.
├── .github/workflows/azure-static-web-apps.yml   ← deploys to Azure automatically on every push
├── site/                                         ← THE WEBSITE (Azure publishes this folder)
│   ├── index.html                                ← home page
│   ├── viral-recipes.html  11 viral recipes (Marry Me Chicken, Baked Feta Pasta, Mississippi Pot Roast…)
│   ├── recipes/          29 recipes + searchable recipe index
│   ├── category/         5 category pages
│   ├── articles/         4 kitchen guides + guide index
│   ├── about.html, contact.html, privacy-policy.html, terms-of-use.html, disclaimer.html, 404.html
│   ├── sitemap.xml, robots.txt, ads.txt, site.webmanifest, apple-touch-icon.png
│   ├── staticwebapp.config.json                  ← Azure settings (404 page, caching, security headers)
│   └── assets/  css, js, icons, img/recipes/ (put your food photos here)
└── tools/
    ├── build.py              ← regenerates every page
    ├── content_recipes.py    ← classic recipes and categories
    ├── content_viral.py      ← viral recipes
    ├── photos.py             ← photo for each recipe (Unsplash IDs)
    └── content_articles.py   ← all articles
```

### Built for iPhone users over 50
- 18px base text, high contrast, and big tap targets (44px or larger, following Apple's guideline)
- **Text size** button on every page
- **Cook mode** keeps the iPhone screen awake while cooking (Safari on iOS 16.4 and later)
- Tap-to-check ingredient list
- **Half / 1× / 2×** batch buttons that rescale every ingredient amount
- **Share** button opens the iPhone share sheet (Messages, Mail, Facebook) and helps recipes spread to family
- **Print** button prints only the recipe card
- Support for notches and the home bar (safe areas), dark mode, Apple system fonts (no font downloads), an iPhone home-screen icon, and a search box that doesn't zoom the page
- Google `Recipe` structured data on every recipe, for rich results in Google Search

---

## Step 1: Add your details

| Placeholder | Replace with |
|---|---|
| `https://www.yourdomain.com` | your real domain |
| `contact@yourdomain.com` | your real email (ideally on your own domain) |
| `Hearthside Kitchen` | your site name, if you choose a different one |
| `the Hearthside Kitchen team` | your name or team name |

**Easiest way:** edit the `SETTINGS` block at the top of `tools/build.py`, then run:

```bash
python3 tools/build.py
```

**Without Python:** open the folder in VS Code and use **Edit → Replace in Files**.

## Step 2: Photos

All 29 recipes already show real food photos from **Unsplash**. The [Unsplash License](https://unsplash.com/license) allows free commercial use without asking permission, and Unsplash+ (paid) photos were excluded. Photos load directly from Unsplash's fast image servers in sizes suited to iPhone screens. If a photo ever fails to load, the page shows a colored tile instead.

The photo list is in `tools/photos.py`. A few are **stand-ins**, close matches rather than the exact dish: egg muffins, overnight oats, meatloaf, cornbread, Zuppa Toscana and peach cobbler. These are marked in the file.

**To use your own photo** (best for the stand-ins, and for AdSense and Pinterest generally):
1. Save it landscape, about **1200 × 900 px**, JPG under 250 KB.
2. Name it after the recipe's web address, for example `site/assets/img/recipes/classic-meatloaf.jpg`.
3. Run `python3 tools/build.py`. Your photo replaces the Unsplash one everywhere: the recipe page, cards, social sharing previews and Google's structured data.

**To swap in a different Unsplash photo:** open the photo on unsplash.com, right-click the image and copy its address. Paste the part after `photo-` and before `?` into `tools/photos.py`, then rebuild. Skip photos marked "Unsplash+".

## Step 3: Upload to GitHub

Create a new repository (branch **main**) and upload **everything**, including the hidden `.github` folder.

```bash
git init
git add .
git commit -m "First version of the website"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/recipe-site.git
git push -u origin main
```

## Step 4: Create the Azure Static Web App

1. In the Azure Portal, search **Static Web Apps** → **Create** → **Free** plan.
2. Under **Deployment details**, choose **Other**. Then **Review + create** → **Create**.
3. Open the app → **Overview** → **Manage deployment token** → copy the token.
4. In GitHub, go to **Settings → Secrets and variables → Actions → New repository secret**. Name it `AZURE_STATIC_WEB_APPS_API_TOKEN` and paste the token.
5. In GitHub, go to **Actions → Deploy website to Azure Static Web Apps → Run workflow** (or push any change).

*Alternative:* choose **GitHub** as the source in Azure with **App location `/site`** and blank **Api location** and **Output location**. If you do this, delete the included workflow file so the site doesn't deploy twice.

## Step 5: Connect your domain

**Static Web App → Custom domains → Add**, then add the DNS record Azure shows you at your domain registrar. Azure sets up SSL for free. AdSense will not approve an `azurestaticapps.net` address.

## Step 6: Get indexed, then apply to AdSense

1. Add the site in [Google Search Console](https://search.google.com/search-console) and submit `/sitemap.xml`.
2. Wait until pages show as indexed, which usually takes 1 to 4 weeks.
3. Apply at [adsense.google.com](https://adsense.google.com). Put your `ca-pub-…` ID in `adsense_client` in `tools/build.py` and rebuild, and replace the publisher ID in `site/ads.txt`.
4. In AdSense, go to **Privacy & messaging** and turn on the **European regulations** message (required) and the **US state regulations** message (recommended).
5. Turn on **Auto ads**. Recipe pages have clear headings and sections, so Auto ads can place ads between them.

**Approval checklist**
- [x] 48 pages of original content: 29 recipes with photos, categories, guides, and policy pages
- [x] About, Contact, Privacy (with Google's required ad disclosures), Terms, and Disclaimer pages, all linked from every footer
- [x] No broken links, mobile-friendly, fast loading, sitemap, robots.txt, and ads.txt
- [ ] Your custom domain and a real contact email
- [x] Food photos on every recipe (replace the stand-ins with your own when you can)
- [ ] Keep adding 2 to 3 recipes a week. Copy a recipe block in `tools/content_recipes.py`, edit it, and rebuild.

---

## Google Ads: reaching iPhone users over 50 in the US

Create a **Display campaign** with the goal **Website traffic**. Use these settings:

| Setting | What to choose |
|---|---|
| **Locations** | United States. Under *Location options*, choose **Presence: people in or regularly in your included locations**. |
| **Languages** | English |
| **Devices** | Show ads on **Mobile phones** only. Uncheck Computers, Tablets, and TV screens. |
| **Device targeting (advanced)** | **Operating systems → iOS**, and **Device models → Apple → iPhone**. |
| **Demographics → Age** | **55–64** and **65+**. Google has no 50–54 bracket. Add **45–54** only if you want to include people in their early 50s, knowing it also includes ages 45–49. |
| **Audience segments** | Affinity: **Food & Dining → Cooking Enthusiasts**. Also create a **custom segment** of people who searched terms such as *easy dinner recipes*, *meatloaf recipe*, *chicken pot pie recipe*, *slow cooker recipes*, or *recipes for two*. |
| **Optimized targeting** | **Off** at first, so your age, device, and audience settings stay strict. |
| **Content → Topics** (optional) | **Food & Drink → Cooking & Recipes** |
| **Content → Exclusions** | Exclude sensitive content categories. Under **Placements**, exclude **mobile app categories**, so ads appear on websites rather than inside iPhone games and apps, where accidental clicks are common. |
| **Bidding** | Start with **Maximize clicks** and a maximum CPC limit, on a small daily budget. Raise the budget only after you check the results. |
| **Landing pages** | Send each ad to a specific recipe page, not the home page. Viral recipes such as Marry Me Chicken and Mississippi Pot Roast make the strongest landing pages. |
| **Ads** | Responsive display ads with real food photos and short, plain headlines such as "Classic Meatloaf, Easy Steps." |

Add UTM tags to your ad URLs (for example `?utm_source=google&utm_medium=display&utm_campaign=iphone50`) so you can see in Analytics how ad visitors behave.

**Things to know before you buy traffic**
- **Invalid traffic:** if you pay for visitors to a site that shows AdSense ads, Google holds *you* responsible for the quality of that traffic. Start only after AdSense approval and with small budgets. Watch for very short visits or unusually high ad click rates, and never click your own ads.
- **Arbitrage policy:** Google limits AdSense on pages whose main purpose is to show ads to paid visitors. Real recipes, photos, and steady new content are what keep the site compliant.
- **iPhone privacy features:** Safari limits third-party cookies, so remarketing audiences built from iPhone visitors will be smaller than on other devices. Rely on demographic, affinity, and custom-segment targeting instead.

## Preview locally

```bash
cd site && python3 -m http.server 8000   # then open http://localhost:8000
```

## Legal note

The policy pages are a solid starting template that covers Google's requirements, but they are not legal advice. Review them for your situation. Food safety guidance follows USDA recommendations.
