const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { items } = require('../static/js/skill-utils.js');

assert.deepEqual(items(['Python', { canonical_skill: 'REST API' }, { name: 'Git' }, {}]), ['Python', 'REST API', 'Git']);
assert.equal(items(['Python', { canonical_skill: 'REST API' }]).join(' '), 'Python REST API');
assert.equal(items([{ arbitrary: 'ignored' }]).join(' ').includes('[object Object]'), false);
const resultRenderer = fs.readFileSync(path.join(__dirname, '../static/js/script.js'), 'utf8');
const baseTemplate = fs.readFileSync(path.join(__dirname, '../templates/base.html'), 'utf8');
assert.match(resultRenderer, /skillSummary\.matched_count/);
assert.match(resultRenderer, /skillSummary\.partial_count/);
assert.match(resultRenderer, /skillSummary\.missing_count/);
assert.doesNotMatch(baseTemplate, /<script[^>]+src=["']https?:/i);
assert.doesNotMatch(baseTemplate, /fonts\.googleapis\.com/i);
process.stdout.write('Frontend skill utility regression checks passed.\n');
