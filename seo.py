"""Indexable, localized pages for the public catalog; playback stays in the app."""
import json
import os
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element, SubElement, tostring

from flask import Response, abort, redirect, render_template, request

ROOT = Path(__file__).parent
LANGUAGES = ('pt', 'en', 'fr', 'it', 'es')
NAMES = {'pt': 'Português', 'en': 'English', 'fr': 'Français', 'it': 'Italiano', 'es': 'Español'}
SOCIAL_LOCALES = {'pt': 'pt_BR', 'en': 'en_US', 'fr': 'fr_FR', 'it': 'it_IT', 'es': 'es_ES'}
COPY = json.loads((ROOT / 'static/seo-copy.json').read_text())
META = {
    'pt': ('Meditação guiada, respiração e relaxamento | Serein',
           'Meditações guiadas gratuitas, exercícios de respiração, histórias para relaxar e sons de fundo. Áudios em português, inglês, francês, italiano e espanhol.',
           'Meditações guiadas', 'Ouvir esta meditação', 'Voltar às meditações', 'Como praticar', 'Sobre esta prática', 'Referência', 'Idiomas'),
    'en': ('Guided meditation, breathing and relaxation | Serein',
           'Free guided meditations, breathing exercises, relaxing stories and background sounds. Audio in English, Portuguese, French, Italian and Spanish.',
           'Guided meditations', 'Listen to this meditation', 'Back to meditations', 'How to practice', 'About this practice', 'Reference', 'Languages'),
    'fr': ('Méditation guidée, respiration et relaxation | Serein',
           'Méditations guidées gratuites, exercices de respiration, histoires relaxantes et sons d’ambiance. Audios en français, anglais, portugais, italien et espagnol.',
           'Méditations guidées', 'Écouter cette méditation', 'Retour aux méditations', 'Comment pratiquer', 'À propos de cette pratique', 'Référence', 'Langues'),
    'it': ('Meditazione guidata, respirazione e relax | Serein',
           'Meditazioni guidate gratuite, esercizi di respirazione, storie rilassanti e suoni di fondo. Audio in italiano, inglese, portoghese, francese e spagnolo.',
           'Meditazioni guidate', 'Ascolta questa meditazione', 'Torna alle meditazioni', 'Come praticare', 'Informazioni sulla pratica', 'Riferimento', 'Lingue'),
    'es': ('Meditación guiada, respiración y relajación | Serein',
           'Meditaciones guiadas gratuitas, ejercicios de respiración, historias relajantes y sonidos de fondo. Audios en español, inglés, portugués, francés e italiano.',
           'Meditaciones guiadas', 'Escuchar esta meditación', 'Volver a las meditaciones', 'Cómo practicar', 'Sobre esta práctica', 'Referencia', 'Idiomas'),
}


def home_path(lang):
    return '/' if lang == 'pt' else f'/{lang}/'


def meditation_path(lang, slug):
    return f'/{lang}/meditations/{slug}/'


def origin():
    # Never derive canonical links from the request Host or forwarded headers.
    value = os.getenv('SEREIN_SITE_URL', 'https://serein.audeladedonnees.fr').rstrip('/')
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('SEREIN_SITE_URL must be an HTTP(S) origin without a path')
    return value


def json_ld(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>'


def head(lang, title, description, paths, structured):
    base = origin()
    canonical = base + paths[lang]
    image = base + f'/assets/seo/{lang}.png'
    tags = [f'<title>{escape(title)}</title>',
            f'<meta name="description" content="{escape(description, quote=True)}">',
            '<meta name="robots" content="index,follow,max-image-preview:large">',
            f'<link rel="canonical" href="{escape(canonical, quote=True)}">']
    for locale, path in paths.items():
        tags.append(f'<link rel="alternate" hreflang="{locale}" href="{escape(base + path, quote=True)}">')
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{escape(base + paths["pt"], quote=True)}">')
    for name, value in {'og:type': 'website', 'og:site_name': 'Serein', 'og:title': title,
                        'og:description': description, 'og:url': canonical, 'og:locale': SOCIAL_LOCALES[lang],
                        'og:image': image, 'og:image:width': '1200', 'og:image:height': '630',
                        'og:image:alt': 'Serein · Lumi', 'twitter:card': 'summary_large_image',
                        'twitter:title': title, 'twitter:description': description, 'twitter:image': image,
                        'twitter:image:alt': 'Serein · Lumi'}.items():
        attribute = 'property' if name.startswith('og:') else 'name'
        tags.append(f'<meta {attribute}="{name}" content="{escape(value, quote=True)}">')
    for locale in paths:
        if locale != lang:
            tags.append(f'<meta property="og:locale:alternate" content="{SOCIAL_LOCALES[locale]}">')
    return '\n'.join(tags) + json_ld(structured)


class LocalizedHTML(HTMLParser):
    """Translate existing UI markup without a second, divergent home template."""
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, lang):
        super().__init__(convert_charrefs=False)
        self.lang, self.parts, self.depth = lang, [], 0

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag not in self.VOID:
                self.depth += 1
            return
        values = dict(attrs)
        if tag == 'html':
            values.update(lang=self.lang, **{'data-page-language': self.lang})
            self.parts.append('<html' + ''.join(f' {k}="{escape(v or "", quote=True)}"' for k, v in values.items()) + '>')
        else:
            self.parts.append(self.get_starttag_text())
        key = values.get('data-i')
        if key in COPY[self.lang] and tag not in self.VOID:
            self.parts.append(COPY[self.lang][key])
            self.depth = 1

    def handle_startendtag(self, tag, attrs):
        if not self.depth:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1
            if self.depth:
                return
        self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)

    def handle_entityref(self, name):
        self.handle_data('&' + name + ';')

    def handle_charref(self, name):
        self.handle_data('&#' + name + ';')

    def handle_comment(self, data):
        if not self.depth:
            self.parts.append('<!--' + data + '-->')

    def handle_decl(self, data):
        self.parts.append('<!' + data + '>')


def setup_seo(app, connect):
    def sessions(lang):
        with connect() as db:
            return [dict(row) for row in db.execute('''SELECT s.*, t.title, t.subtitle, t.script,
                p.content AS protocol FROM sessions s JOIN translations t ON t.session_id=s.id AND t.lang=?
                LEFT JOIN exercise_protocols p ON p.session_id=s.id AND p.lang=t.lang
                WHERE s.published=1 ORDER BY s.id''', (lang,))]

    def language_links(paths, lang):
        return '<nav class="seo-languages" aria-label="' + META[lang][8] + '">' + ' · '.join(
            f'<a href="{escape(path, quote=True)}" hreflang="{locale}" lang="{locale}"' +
            (' aria-current="page"' if lang == locale else '') + f'>{NAMES[locale]}</a>' for locale, path in paths.items()) + '</nav>'

    def render_home(lang):
        rows = sessions(lang)
        paths = {locale: home_path(locale) for locale in LANGUAGES}
        links = ''.join(f'<li><a href="{meditation_path(lang, row["slug"])}">{escape(row["title"])}</a>'
                        f'<span>{row["duration"]} min · {escape(row["subtitle"])}</span></li>' for row in rows)
        directory = f'<section class="section seo-directory"><h2>{META[lang][2]}</h2><ul>{links}</ul>{language_links(paths, lang)}</section>'
        cards = ''.join(f'<article class="card"><div class="card-body"><h3><a href="{meditation_path(lang, row["slug"])}">'
                        f'{escape(row["title"])}</a></h3><p>{escape(row["subtitle"])}</p><span>{row["duration"]} min</span></div></article>' for row in rows)
        markup = (ROOT / 'static/index.html').read_text()
        markup = re.sub(r'<title>.*?</title>', '', markup, flags=re.S)
        # The static fallback description belongs to the offline Android page.
        markup = re.sub(r'<meta name="description"[^>]*>', '', markup)
        translator = LocalizedHTML(lang)
        translator.feed(markup)
        markup = ''.join(translator.parts)
        structured = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'WebSite', '@id': origin() + '/#website', 'name': 'Serein', 'url': origin() + '/',
             'inLanguage': list(LANGUAGES)},
            {'@type': 'CollectionPage', '@id': origin() + paths[lang], 'name': META[lang][0],
             'description': META[lang][1], 'url': origin() + paths[lang], 'inLanguage': lang,
             'isPartOf': {'@id': origin() + '/#website'}, 'mainEntity': {'@type': 'ItemList',
             'numberOfItems': len(rows), 'itemListElement': [{'@type': 'ListItem', 'position': i + 1,
             'name': row['title'], 'url': origin() + meditation_path(lang, row['slug'])} for i, row in enumerate(rows)]}}]}
        markup = markup.replace('</head>', head(lang, META[lang][0], META[lang][1], paths, structured) + '</head>')
        markup = markup.replace('<div id="cards" class="cards"></div>', '<div id="cards" class="cards">' + cards + '</div>')
        return markup.replace('<footer>', directory + '<footer>')

    # Keep the original root endpoint used by existing links.
    def homepage():
        if request.args.get('lang') in LANGUAGES:
            args = request.args.to_dict()
            locale = args.pop('lang')
            from urllib.parse import urlencode
            return redirect(home_path(locale) + ('?' + urlencode(args) if args else ''), 301)
        return render_home('pt')
    app.view_functions['home'] = homepage

    @app.get('/<any(pt,en,fr,it,es):lang>/')
    def localized_home(lang):
        if lang not in LANGUAGES:
            abort(404)
        if lang == 'pt':
            return redirect('/' + ('?' + request.query_string.decode() if request.query_string else ''), 301)
        return render_home(lang)

    @app.get('/index.html')
    def canonical_home():
        return redirect('/' + ('?' + request.query_string.decode() if request.query_string else ''), 301)

    @app.get('/<lang>/meditations/<slug>/')
    def meditation_page(lang, slug):
        if lang not in LANGUAGES:
            abort(404)
        item = next((row for row in sessions(lang) if row['slug'] == slug), None)
        if not item:
            abort(404)
        protocol = json.loads(item['protocol']) if item['protocol'] else None
        paths = {locale: meditation_path(locale, slug) for locale in LANGUAGES}
        title = f'{item["title"]} · {item["duration"]} min | Serein'
        description = f'{item["title"]}. {item["subtitle"]}. {item["duration"]} min · {META[lang][2]}. '
        structured = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'WebPage', '@id': origin() + paths[lang], 'url': origin() + paths[lang],
             'name': title, 'description': description.strip(), 'inLanguage': lang,
             'isPartOf': {'@id': origin() + '/#website'}},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Serein', 'item': origin() + home_path(lang)},
                {'@type': 'ListItem', 'position': 2, 'name': item['title'], 'item': origin() + paths[lang]}]}]}
        return render_template('meditation.html', lang=lang, item=item, protocol=protocol,
                               home=home_path(lang), labels=META[lang], copy=COPY[lang],
                               seo_head=head(lang, title, description.strip(), paths, structured),
                               languages=language_links(paths, lang))

    @app.get('/robots.txt')
    def robots():
        return Response('User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: ' + origin() + '/sitemap.xml\n', mimetype='text/plain')

    @app.get('/sitemap.xml')
    def sitemap():
        root = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        for locale in LANGUAGES:
            paths = [home_path(locale)] + [meditation_path(locale, item['slug']) for item in sessions(locale)]
            for path in paths:
                SubElement(SubElement(root, 'url'), 'loc').text = origin() + path
        return Response(tostring(root, encoding='utf-8', xml_declaration=True), mimetype='application/xml')

    @app.after_request
    def seo_headers(response):
        if request.path.startswith(('/api/', '/media/')) or response.status_code >= 400 or request.path.endswith(('.json', '.html')):
            response.headers['X-Robots-Tag'] = 'noindex'
        if response.mimetype == 'text/html':
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Content-Language'] = request.view_args.get('lang', 'pt') if request.view_args else 'pt'
        return response
