const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function page(serverLanguage, sessions = []) {
  const select = {onchange: () => 'offline'};
  const calls = {opened: [], saved: [], urls: [], resets: 0};
  const context = vm.createContext({
    document: {documentElement: {dataset: {pageLanguage: serverLanguage}}},
    $: () => select, items: sessions, URLSearchParams,
    location: {search: '?session=respirar', hash: '#home', assign: value => calls.urls.push(value)},
    localStorage: {setItem: (...values) => calls.saved.push(values)},
    resetAudio: () => calls.resets++, openPlayer: item => calls.opened.push(item), window: {}
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/seo.js'), 'utf8'), context);
  return {select, calls, context};
}

test('offline Android keeps its existing local language handler', () => {
  const p = page(undefined);
  assert.equal(p.select.onchange(), 'offline');
  assert.equal(p.context.window.sereinOpenLinkedSession, undefined);
  assert.equal(p.calls.urls.length, 0);
});

test('language selection navigates to a real URL while retaining the chosen meditation', () => {
  const p = page('fr');
  p.select.onchange({target: {value: 'en'}});
  p.select.onchange({target: {value: 'pt'}});
  assert.deepEqual(p.calls.urls, ['/en/?session=respirar#home', '/?session=respirar#home']);
  assert.equal(p.calls.resets, 2);
  assert.deepEqual(p.calls.saved[0], ['serein-lang', 'en']);
});

test('session deep links wait for the catalog and open once without autoplay', () => {
  const p = page('fr');
  assert.equal(p.calls.opened.length, 0);
  p.context.items.push({slug: 'respirar'});
  p.context.window.sereinOpenLinkedSession();
  p.context.window.sereinOpenLinkedSession();
  assert.equal(p.calls.opened.length, 1);
  assert.equal(p.calls.opened[0].slug, 'respirar');
});
