const fs = require('node:fs');
const path = require('node:path');
const output = path.join(__dirname, 'public');
fs.mkdirSync(output, {recursive:true});
fs.copyFileSync(path.join(__dirname, 'replica.js'), path.join(output, 'replica.js'));
console.log('Prepared static assets. Page routes are served by api/index.py.');
