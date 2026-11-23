const assert = require('node:assert/strict');
const { items } = require('../static/js/skill-utils.js');

assert.deepEqual(items(['Python', { canonical_skill: 'REST API' }, { name: 'Git' }, {}]), ['Python', 'REST API', 'Git']);
assert.equal(items(['Python', { canonical_skill: 'REST API' }]).join(' '), 'Python REST API');
assert.equal(items([{ arbitrary: 'ignored' }]).join(' ').includes('[object Object]'), false);
process.stdout.write('Frontend skill utility regression checks passed.\n');
