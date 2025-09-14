import fs from 'fs';
import path from 'path';
import { marked } from 'marked';

// Read the main README.md
const readmePath = path.join(process.cwd(), '..', 'README.md');
const readmeContent = fs.readFileSync(readmePath, 'utf-8');

// Convert markdown to HTML
const readmeHtml = marked(readmeContent);

// Read the HTML template
const templatePath = path.join(process.cwd(), 'src', 'index.template.html');
const template = fs.readFileSync(templatePath, 'utf-8');

// Replace the placeholder with README content
const finalHtml = template.replace('{{README_CONTENT}}', readmeHtml);

// Write the final index.html
const outputPath = path.join(process.cwd(), 'src', 'index.html');
fs.writeFileSync(outputPath, finalHtml);

console.log('✅ Generated index.html from README.md');
