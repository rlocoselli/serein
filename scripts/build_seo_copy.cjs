/* Refresh the server's translations from the UI's existing dictionaries. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const context = vm.createContext({});
const read = name => fs.readFileSync(path.join(root, 'static', name), 'utf8');
vm.runInContext(read('app.js').split('\n')[0], context);
for (const [file, marker] of [
  ['exercises.js', 'let activeStep'], ['mobile.js', 'let soundKey'],
  ['catalog.js', "$('practice-search')"],
  ['natural-voice.js', null], ['sound-studio.js', 'let storedAudio']
]) {
  const source = read(file);
  const boundary = marker === null ? source.length : source.indexOf(marker);
  if (boundary < 0) throw new Error('Dictionary boundary missing: ' + file);
  vm.runInContext(source.slice(0, boundary), context, {filename: file});
}
fs.writeFileSync(path.join(root, 'static/seo-copy.json'),
  vm.runInContext('JSON.stringify(copy,null,2)', context) + '\n');
console.log('Updated server translations for five languages.');
