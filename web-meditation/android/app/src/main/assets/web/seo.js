/* Public language URLs and deep links; Android keeps its local, offline navigation. */
(() => {
  const serverLanguage = document.documentElement.dataset.pageLanguage;
  if (!serverLanguage) return;
  const home = locale => locale === 'pt' ? '/' : `/${locale}/`;
  $('language').onchange = event => {
    const locale = event.target.value;
    localStorage.setItem('serein-lang', locale);
    resetAudio();
    const params = new URLSearchParams(location.search);
    params.delete('lang');
    const search = params.toString();
    location.assign(home(locale) + (search ? '?' + search : '') + location.hash);
  };
  let opened = false;
  window.sereinOpenLinkedSession = () => {
    if (opened || !items.length) return;
    const slug = new URLSearchParams(location.search).get('session');
    const selected = items.find(item => item.slug === slug);
    if (selected) { opened = true; openPlayer(selected); }
  };
  window.sereinOpenLinkedSession();
})();
