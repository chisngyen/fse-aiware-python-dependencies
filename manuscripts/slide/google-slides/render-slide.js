// render-slide.js — render section(s) of a .dc.html deck to PNG via headless Chrome.
// usage: node render-slide.js <index|all> [deckFile] [outPrefix]
//   deckFile  default "CGAR Deck.dc.html"
//   outPrefix default "slide_"   (PNG => <outPrefix><NN>.png)
const fs = require('fs');
const { execFileSync } = require('child_process');
const path = require('path');

const PROJ = __dirname;
const deckFile = process.argv[3] || 'CGAR Deck.dc.html';
const outPrefix = process.argv[4] || 'slide_';
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const html = fs.readFileSync(path.join(PROJ, deckFile), 'utf8');
const sections = html.match(/<section[\s\S]*?<\/section>/g) || [];
const labels = sections.map(s => (s.match(/data-label="([^"]*)"/) || [, '?'])[1]);

const arg = process.argv[2] || '0';
const targets = arg === 'all' ? sections.map((_, i) => i) : [parseInt(arg, 10)];

const tpl = (sec) => `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>html,body{margin:0;padding:0;background:#fff}section{width:1920px;height:1080px;box-sizing:border-box;overflow:hidden}</style>
</head><body>${sec}</body></html>`;

const tag = outPrefix.replace(/[^a-z0-9]/gi, '') || 'def';
for (const i of targets) {
  const f = path.join(PROJ, `_render_${tag}.html`);
  fs.writeFileSync(f, tpl(sections[i]), 'utf8');
  const out = path.join(PROJ, `${outPrefix}${String(i).padStart(2, '0')}.png`);
  execFileSync(CHROME, ['--headless=new', '--disable-gpu', '--hide-scrollbars',
    `--screenshot=${out}`, '--window-size=1920,1080', '--force-device-scale-factor=1',
    '--virtual-time-budget=2500', f], { stdio: 'ignore' });
  console.log(`[${i}] ${labels[i]} -> ${path.basename(out)}`);
}
