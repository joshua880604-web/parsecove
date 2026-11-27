"""Guide navigation, static content and comparison with real browser CSS."""
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('PARSECOVE_TEST_URL', 'http://127.0.0.1:3000').rstrip('/')
OUT = Path('/workspace/work/parsecove-guides-qa')
OUT.mkdir(parents=True, exist_ok=True)
ROUTE = '/guides/rem-vs-em/'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000},
                                  permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, external, mutations = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: external.append(r.url) if not r.url.startswith((BASE, 'blob:', 'data:')) else None)
    page.on('request', lambda r: mutations.append(r.url) if r.method != 'GET' else None)

    assert page.goto(BASE + '/guides/').status == 200
    expect(page.locator('h1')).to_have_text('Developer guides')
    expect(page.locator('.guide-card')).to_have_count(4)
    page.screenshot(path=str(OUT / 'guides-desktop.png'), full_page=True)
    page.locator('.guide-card[href="/guides/rem-vs-em/"]').click()
    expect(page.locator('h1')).to_have_text('REM vs EM: what changes, and why')
    expect(page.locator('#unit-summary')).to_have_text('Child font size: 20px × 1.25 = 25px.')
    expect(page.locator('#unit-rem-length')).to_have_text('16px')
    expect(page.locator('#unit-em-length')).to_have_text('25px')
    expect(page.locator('#unit-font-em')).to_have_text('20px')
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path=str(OUT / 'rem-vs-em-desktop.png'), full_page=True)
    page.locator('#try-units').screenshot(path=str(OUT / 'unit-demo-desktop.png'), style='.skip:not(:focus){visibility:hidden}')
    site_root = page.evaluate('getComputedStyle(document.documentElement).fontSize')

    # An isolated document lets CSS resolve the exact declarations shown in the guide.
    def browser_css(root, parent, ratio):
        return page.evaluate('''({root,parent,ratio})=>{
          const frame=document.createElement('iframe');
          frame.style.cssText='position:absolute;left:-10000px;width:600px;visibility:hidden';
          document.body.append(frame);const d=frame.contentDocument;
          d.open();d.write(`<!doctype html><style>
            html{font-size:${root}px}.parent{font-size:${parent}px}
            .child{font-size:${ratio}em;padding:1em}
            .rem{padding:1rem}.fixed{padding:16px}
            .font-em{font-size:1em}.font-rem{font-size:1rem}
            </style><div class="parent"><span class="font-em">em</span>
            <span class="font-rem">rem</span><div class="child">
            <div class="rem">rem padding</div><div class="fixed">fixed</div></div></div>`);d.close();
          const get=(sel,property)=>parseFloat(frame.contentWindow.getComputedStyle(d.querySelector(sel))[property]);
          const result={fontEm:get('.font-em','fontSize'),fontRem:get('.font-rem','fontSize'),
            paddingEm:get('.child','paddingTop'),paddingRem:get('.rem','paddingTop'),
            paddingPx:get('.fixed','paddingTop'),childFont:get('.child','fontSize')};
          frame.remove();return result;
        }''', {'root': root, 'parent': parent, 'ratio': ratio})

    scenarios = [(16, 20, 1.25), (20, 20, 1.25), (18, 24, 1.5),
                 (20, 18, 0.875), (12, 12, 2), (64, 96, 4)]
    for root, parent, ratio in scenarios:
        page.locator('#unit-root').fill(str(root))
        page.locator('#unit-parent').fill(str(parent))
        page.locator('#unit-ratio').fill(str(ratio))
        expected = browser_css(root, parent, ratio)
        for selector, key in [('#unit-font-em', 'fontEm'), ('#unit-font-rem', 'fontRem'),
                              ('#unit-padding-em', 'paddingEm'), ('#unit-padding-rem', 'paddingRem'),
                              ('#unit-px-length', 'paddingPx'), ('#unit-em-length', 'childFont')]:
            result = float(page.locator(selector).inner_text().removesuffix('px'))
            assert abs(result - expected[key]) < 0.0002, (root, parent, ratio, key, result, expected[key])
        assert page.evaluate('getComputedStyle(document.documentElement).fontSize') == site_root
    page.locator('[data-copy="unit-css"]').click()
    copied = page.evaluate('navigator.clipboard.readText()')
    assert copied == 'html { font-size: 64px; }\n.parent { font-size: 96px; }\n.child { font-size: 4em; }'

    # Invalid controls hide calculated results; resetting restores the complete example.
    for selector, value in [('#unit-root', ''), ('#unit-root', '0'), ('#unit-root', '65'),
                            ('#unit-parent', '-1'), ('#unit-parent', '97'),
                            ('#unit-ratio', '0.01'), ('#unit-ratio', '4.1')]:
        page.locator('#unit-reset').click()
        page.locator(selector).fill(value)
        expect(page.locator('#unit-error')).to_be_visible()
        expect(page.locator('#unit-results')).to_be_hidden()
        expect(page.locator('#unit-css')).to_be_empty()
    page.locator('#unit-reset').click()
    expect(page.locator('#unit-error')).to_be_hidden()
    expect(page.locator('#unit-summary')).to_contain_text('25px')

    # The complete nested snippet is executable HTML and produces the documented sizes.
    nested = page.locator('#nested-em pre code').inner_text()
    snippet = context.new_page()
    snippet.set_content(nested)
    sizes = snippet.locator('.level').evaluate_all('(els)=>els.map(e=>getComputedStyle(e).fontSize)')
    assert sizes == ['20px', '25px'], sizes
    snippet.close()
    page.locator('.guide-toc a[href="#nested-em"]').click()
    expect(page.locator('#nested-em h2')).to_be_in_viewport()
    page.locator('#guide-faq summary').nth(1).click()
    expect(page.locator('#guide-faq details').nth(1)).to_have_attribute('open', '')
    expect(page.locator('#guide-faq details').nth(1)).to_contain_text('element’s own computed font size')
    expect(page.locator('#terms dt')).to_have_count(5)

    # The guide and hub are reachable from the site, and both converters link back.
    for route in ['/px-to-rem/', '/rem-to-px/']:
        page.goto(BASE + route)
        expect(page.locator('.guide-teaser a')).to_have_attribute('href', ROUTE)
        expect(page.locator('#sidebar a[href="/guides/"]')).to_be_visible()
    page.locator('.search-trigger').click()
    page.locator('#global-search').fill('rem vs em')
    expect(page.locator('#search-list a:visible')).to_have_count(1)
    page.locator('#search-list a:visible').click()
    assert page.url == BASE + ROUTE
    page.locator('.guide-next a[href="/rem-to-px/"]').click()
    expect(page.locator('#px-output')).to_have_value('24px')

    checks = 0
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        for route in ['/guides/', ROUTE]:
            assert page.goto(BASE + route).status == 200
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, route)
            expect(page.locator('h1')).to_have_count(1)
            expect(page.locator('[data-ad-slot]')).to_have_count(0)
            if route == ROUTE:
                page.locator('#unit-root').fill('20')
                page.locator('#unit-parent').fill('24')
                page.locator('#unit-ratio').fill('1.5')
                expect(page.locator('#unit-em-length')).to_have_text('36px')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                if width == 390:
                    page.evaluate('window.scrollTo(0,0)')
                    page.screenshot(path=str(OUT / 'rem-vs-em-mobile.png'), full_page=True)
                    page.locator('#try-units').screenshot(path=str(OUT / 'unit-demo-mobile.png'), style='.skip:not(:focus){visibility:hidden}')
            checks += 1
    page.set_viewport_size({'width': 390, 'height': 640})
    page.locator('.mobile-menu').click()
    page.locator('#sidebar a[href="/guides/"]').scroll_into_view_if_needed()
    expect(page.locator('#sidebar a[href="/guides/"]')).to_be_in_viewport()
    page.locator('.sidebar-close').click()
    page.locator('.search-trigger').click()
    page.locator('#global-search').fill('rem vs em')
    assert page.locator('#search-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth')

    static = browser.new_context(java_script_enabled=False)
    static_page = static.new_page()
    static_page.goto(BASE + ROUTE)
    expect(static_page.locator('h1')).to_have_text('REM vs EM: what changes, and why')
    expect(static_page.locator('link[rel="canonical"]')).to_have_attribute('href', 'https://parsecove.com' + ROUTE)
    expect(static_page.locator('meta[property="og:type"]')).to_have_attribute('content', 'article')
    expect(static_page.locator('#unit-summary')).to_contain_text('25px')
    expect(static_page.locator('#terms')).to_contain_text('Computed font size')
    expect(static_page.locator('#guide-faq details')).to_have_count(5)
    schema = json.loads(static_page.locator('script[type="application/ld+json"]').inner_text())
    article = next(x for x in schema['@graph'] if x['@type'] == 'TechArticle')
    assert article['headline'] == static_page.locator('h1').inner_text()
    assert article['datePublished'] == article['dateModified'] == '2026-11-27'
    assert article['author']['name'] == 'ParseCove'
    assert article['url'] == 'https://parsecove.com' + ROUTE
    breadcrumbs = next(x for x in schema['@graph'] if x['@type'] == 'BreadcrumbList')
    assert len(breadcrumbs['itemListElement']) == 3
    static_page.goto(BASE + '/guides/')
    hub = json.loads(static_page.locator('script[type="application/ld+json"]').inner_text())
    assert hub['@type'] == 'CollectionPage'
    assert hub['mainEntity']['itemListElement'][0]['url'] == article['url']
    static.close()
    assert not errors, errors
    assert not external, external
    assert not mutations, mutations
    report = {'actual_browser_css_scenarios': len(scenarios), 'nested_snippet': 'passed',
              'invalid_controls_and_reset': 'passed', 'clipboard': 'passed',
              'navigation_and_context_links': 'passed', 'static_article_and_schema': 'passed',
              'responsive_checks': checks, 'page_errors': errors, 'external_requests': external,
              'input_upload_requests': mutations}
    (OUT / 'browser-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    browser.close()
