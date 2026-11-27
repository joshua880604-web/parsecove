"""Linked, factual JSON-LD entities for the statically generated site."""
import json

SITE_DESCRIPTION = 'Free browser-local developer tools for data formats, encoded text, images, CSS and Unix timestamps.'
LOGO_PATH = '/assets/parsecove-logo.svg'


def reference(identifier):
    return {'@id': identifier}


def breadcrumb(identifier, items):
    return {
        '@type': 'BreadcrumbList', '@id': identifier,
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': name, 'item': url}
            for i, (name, url) in enumerate(items)
        ],
    }


def directory(identifier, name, entries):
    return {
        '@type': 'ItemList', '@id': identifier, 'name': name,
        'itemListOrder': 'https://schema.org/ItemListUnordered',
        'numberOfItems': len(entries),
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': title,
             'url': url, 'item': reference(entity)}
            for i, (title, url, entity) in enumerate(entries)
        ],
    }


def page_schema(slug, title, description, tools, guides, groups, origin):
    # Error responses are not presented as an indexable content entity.
    if slug == '404':
        return None
    origin = origin.rstrip('/')
    home = origin + '/'
    canonical = home if slug == 'home' else f'{origin}/{slug}/'
    org_id, site_id, logo_id = home + '#organization', home + '#website', home + '#logo'
    page_id, breadcrumb_id = canonical + '#webpage', canonical + '#breadcrumb'
    organization = {
        '@type': 'Organization', '@id': org_id, 'name': 'ParseCove',
        'url': home, 'description': SITE_DESCRIPTION, 'logo': reference(logo_id),
    }
    logo = {
        '@type': 'ImageObject', '@id': logo_id, 'url': origin + LOGO_PATH,
        'contentUrl': origin + LOGO_PATH, 'width': 512, 'height': 512,
        'caption': 'ParseCove logo', 'inLanguage': 'en',
    }
    website = {
        '@type': 'WebSite', '@id': site_id, 'url': home, 'name': 'ParseCove',
        'description': SITE_DESCRIPTION, 'inLanguage': 'en',
        'publisher': reference(org_id),
    }
    page = {
        '@type': 'AboutPage' if slug == 'about' else 'CollectionPage' if slug == 'guides' else 'WebPage',
        '@id': page_id, 'url': canonical, 'name': title + ' | ParseCove',
        'description': description, 'inLanguage': 'en',
        'isPartOf': reference(site_id), 'publisher': reference(org_id),
    }
    common = [organization, logo, website]
    extra = []
    primary = page
    tool = next((t for t in tools if t[0] == slug), None)
    guide = next((g for g in guides if g['slug'] == slug), None)

    if slug == 'home':
        lookup = {t[0]: t for t in tools}
        ordered = [lookup[s] for _, slugs, _ in groups for s in slugs]
        entries = [(t[1], f'{origin}/{t[0]}/', f'{origin}/{t[0]}/#webpage') for t in ordered]
        listing = directory(home + '#tools', 'Developer tools', entries)
        page['mainEntity'] = reference(listing['@id'])
        extra.append(listing)
    elif tool:
        app_id, offer_id = canonical + '#application', canonical + '#offer'
        primary = {
            '@type': 'WebApplication', '@id': app_id, 'name': title,
            'url': canonical, 'description': description, 'inLanguage': 'en',
            'applicationCategory': 'DeveloperApplication', 'operatingSystem': 'Any',
            'browserRequirements': 'Requires JavaScript and a modern browser.',
            'isAccessibleForFree': True, 'publisher': reference(org_id),
            'mainEntityOfPage': reference(page_id), 'offers': reference(offer_id),
        }
        page['mainEntity'] = reference(app_id)
        extra.append({
            '@type': 'Offer', '@id': offer_id, 'url': canonical,
            'price': '0', 'priceCurrency': 'USD', 'seller': reference(org_id),
            'itemOffered': reference(app_id),
        })
    elif guide:
        primary = {
            '@type': 'TechArticle', '@id': canonical + '#article',
            'headline': guide['heading'], 'description': guide['description'],
            'url': canonical, 'mainEntityOfPage': reference(page_id),
            'inLanguage': 'en', 'datePublished': guide['published'],
            'dateModified': guide.get('modified', guide['published']),
            'author': reference(org_id), 'publisher': reference(org_id),
            'articleSection': guide['category'], 'isAccessibleForFree': True,
        }
        page['mainEntity'] = reference(primary['@id'])
    elif slug == 'guides':
        entries = [(g['title'], f'{origin}/{g["slug"]}/', f'{origin}/{g["slug"]}/#article') for g in guides]
        listing = directory(canonical + '#guide-list', 'Developer guides', entries)
        page['mainEntity'] = reference(listing['@id'])
        extra.append(listing)
    elif slug == 'about':
        page['mainEntity'] = reference(org_id)

    if slug != 'home':
        if guide:
            trail = [('Home', home), ('Guides', origin + '/guides/'), (guide['label'], canonical)]
        else:
            trail = [('Toolbox', home), (title, canonical)]
        page['breadcrumb'] = reference(breadcrumb_id)
        extra.append(breadcrumb(breadcrumb_id, trail))
    graph = [primary] + common + ([] if primary is page else [page]) + extra
    return {'@context': 'https://schema.org', '@graph': graph}


def schema_script(document):
    if document is None:
        return ''
    payload = json.dumps(document, ensure_ascii=False, separators=(',', ':'))
    payload = payload.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    payload = payload.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    return '<script type="application/ld+json">' + payload + '</script>'
