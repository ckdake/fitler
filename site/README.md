# Fitler Website

Static website for [fitler.net](https://fitler.net), automatically built from the main README.md.

## Development

```bash
npm install      # Install dependencies
npm run dev      # Start dev server (localhost:3000)
npm run build    # Build for production
./dev.sh         # Helper script with more options
```

## How it works

1. `scripts/build.js` converts `../README.md` to HTML
2. Injects it into `src/index.template.html`
3. Vite builds the final static site
4. GitHub Actions deploys to Pages automatically

-   Changes are pushed to the `site/` directory
-   Changes are made to the main `README.md` file

The deployment workflow is defined in `.github/workflows/deploy-site.yml`.

## Custom Domain

The site is served at `fitler.net` via the `CNAME` file in `public/`.

## Files

-   `src/index.template.html` - HTML template with placeholder for README content
-   `src/assets/css/style.css` - Stylesheet for the site
-   `src/assets/js/main.js` - JavaScript functionality
-   `scripts/build.js` - Build script that processes README.md
-   `vite.config.js` - Vite configuration
-   `public/CNAME` - Custom domain configuration
