# Amaris storefront replica

Run `npm run dev` (Python 3.10+ required), then open http://localhost:4173.

The generated `storefront/` cache is excluded from Git. After cloning, pages and
assets download on first use; run `npm run capture` to rebuild the local snapshot.

## Vercel deployment

Import this repository with the project root set to `.`. `vercel.json` sets the
framework to Other, builds static browser assets, and routes pages to the Python
function in `api/index.py`. Do not use the local `npm start` command as a build.

The homepage is bundled, so it renders without fetching a remote page. Other
pages use an ephemeral `/tmp` cache on Vercel; the function never writes into its
read-only source directory. Images, videos, fonts and CDN scripts use external
edge rewrites, keeping large media outside the Python function response.

This project preserves the reference storefront's actual HTML, theme stylesheets,
fonts, imagery, videos, responsive breakpoints and browser-side theme components.
The completed capture contains 1,382 public page routes with no missing pages,
plus the original theme and cached assets. See `capture-report.json` for totals.
`routes.json` lists the public routes discovered in the sitemap and navigation.
It is a captured storefront, not an editable Shopify Liquid theme export.

## Files

- `mirror.py`: repeatable public-page and asset capture; run `npm run capture`.
- `server.py`: local server, URL rewriting, and on-demand asset cache.
- `storefront/`: captured source responses and metadata, keyed by request URL hash.
- `reference.html`: original homepage snapshot.
- `replica.js`: local preview form handling.
- `capture-report.json`: capture totals and any URLs that could not be fetched.

All internal page links and same-origin assets stay on localhost. A missing cached
page, query variant, collection filter, search result or asset is fetched from the
public reference site on first use and cached. Therefore an internet connection is
needed for uncached resources. Third-party embeds may also need the internet.

## Service boundaries

The cart uses browser-local storage and the original theme drawer, with quantity
updates, removal and totals. It does not submit orders to the reference store.

Live checkout, customer login, wishlists, newsletter delivery,
appointment submissions and third-party app services require their own connected
backend. POST requests are deliberately not forwarded to the reference shop.
The local preview cannot create real orders or customer accounts.

## Verification

`npm run check` checks Python syntax. `verify-pages.cjs`, `verify-interactions.cjs`
and `verify-cart.cjs` check representative pages, menus, filters, accordions, mobile
navigation and local cart behavior. These use this machine's Playwright installation; its runtime
path is specific to this workstation. Screenshot assets are saved at project root.
