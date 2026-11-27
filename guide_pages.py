"""Guide registry, metadata and original worked CSS examples."""
import html

GUIDES = [{
    'slug': 'guides/rem-vs-em',
    'title': 'REM vs EM: CSS Units, Examples & When to Use Each',
    'heading': 'REM vs EM: what changes, and why',
    'description': 'Compare rem, em and px in CSS. Explore root and inherited font sizes, nested em scaling, practical examples and when each unit is useful.',
    'published': '2026-11-27',
    'category': 'CSS & layout',
    'label': 'REM vs EM',
}, {
    'slug': 'guides/save-base64-image',
    'title': 'How to Save a Base64 Image to a File — Data URL Guide',
    'heading': 'How to save a Base64 image to a file',
    'description': 'Save a Base64 image or data URL as its original file. Follow a complete PNG example, run JavaScript or Python code and troubleshoot common decoding errors.',
    'published': '2026-11-27',
    'category': 'Images & files',
    'label': 'Save a Base64 image',
}, {
    'slug': 'guides/unix-timestamp-seconds-vs-milliseconds',
    'title': 'Unix Timestamp: Seconds vs Milliseconds — Examples',
    'heading': 'Unix timestamps: seconds vs milliseconds',
    'description': 'Compare Unix timestamp seconds and milliseconds, troubleshoot 1970 dates, preserve millisecond precision and run complete JavaScript and Python examples.',
    'published': '2026-11-27',
    'category': 'Time & dates',
    'label': 'Unix timestamp units',
}]


def guide_schema(slug, origin):
    if slug == 'guides':
        return {
            '@context': 'https://schema.org', '@type': 'CollectionPage',
            'name': 'Developer guides | ParseCove', 'url': origin + '/guides/',
            'description': 'Worked CSS, image and timestamp examples connected to the ParseCove tools.',
            'inLanguage': 'en',
            'mainEntity': {'@type': 'ItemList', 'itemListElement': [
                {'@type': 'ListItem', 'position': i + 1, 'name': g['title'],
                 'url': origin + '/' + g['slug'] + '/'} for i, g in enumerate(GUIDES)
            ]},
        }
    guide = next((g for g in GUIDES if g['slug'] == slug), None)
    if not guide:
        return None
    canonical = origin + '/' + slug + '/'
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'TechArticle', '@id': canonical + '#article',
         'headline': guide['heading'], 'description': guide['description'],
         'url': canonical, 'mainEntityOfPage': canonical, 'inLanguage': 'en',
         'datePublished': guide['published'], 'dateModified': guide['published'],
         'author': {'@type': 'Organization', 'name': 'ParseCove', 'url': origin + '/about/'},
         'publisher': {'@type': 'Organization', 'name': 'ParseCove', 'url': origin + '/'},
         'articleSection': guide['category'], 'isAccessibleForFree': True},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': origin + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Guides', 'item': origin + '/guides/'},
            {'@type': 'ListItem', 'position': 3, 'name': guide['label'], 'item': canonical},
        ]},
    ]}


def guide_teaser(slug='guides/rem-vs-em'):
    guide = next(g for g in GUIDES if g['slug'] == slug)
    return f'<aside class="guide-teaser"><span class="eyebrow">WORKED GUIDE</span><h2>{html.escape(guide["heading"])}</h2><p>{html.escape(guide["description"])}</p><a class="inline-link" href="/{slug}/">Read the guide →</a></aside>'


def guide_cards():
    return ''.join(
        f'<a class="guide-card" href="/{g["slug"]}/"><span class="eyebrow">{html.escape(g["category"])}</span>'
        f'<h2>{html.escape(g["title"])}</h2><p>{html.escape(g["description"])}</p>'
        '<span class="guide-card-link">Read the guide →</span></a>' for g in GUIDES
    )


def guides_preview():
    return '<section class="guides-preview"><span class="eyebrow">UNDERSTAND THE RESULT</span><div class="section-heading"><h2>Practical guides</h2><a class="inline-link" href="/guides/">Browse all guides →</a></div><div class="guide-directory">'+guide_cards()+'</div></section>'


def guides_index():
    return '''<div class="page-heading"><span class="eyebrow">UNDERSTAND THE RESULT</span><h1>Developer guides</h1><p>Worked examples, clear assumptions and small experiments you can try. Understand CSS units, encoded images and timestamp units, then use the tools to check your own values.</p></div><div class="guide-directory">'''+guide_cards()+'''</div><section class="guide-hub-tools"><h2>Put the examples to work</h2><p>Check CSS lengths, inspect an encoded image, or convert a timestamp with an explicit unit.</p><div class="actions"><a class="button" href="/px-to-rem/">PX to REM converter</a><a class="button" href="/rem-to-px/">REM to PX converter</a><a class="button" href="/base64-to-image/">Base64 to image</a><a class="button" href="/unix-timestamp-converter/">Unix timestamp converter</a></div></section>'''


def rem_em_guide(code_example, faq, copy):
    intro = '''<article class="guide-article"><header class="guide-header"><nav class="guide-breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span aria-current="page">REM vs EM</span></nav><span class="eyebrow">CSS & LAYOUT · WORKED GUIDE</span><h1>REM vs EM: what changes, and why</h1><p class="guide-deck">Rem follows the root font size. Em follows an element’s font size, with a different reference when you set font-size itself. That distinction explains most surprising conversions.</p><p class="guide-byline">By <a href="/about/">ParseCove</a> · Published <time datetime="2026-11-27">27 November 2026</time></p></header>
<nav class="guide-toc" aria-label="On this page"><strong>On this page</strong><a href="#comparison">The difference</a><a href="#try-units">Try the numbers</a><a href="#nested-em">Nested em values</a><a href="#choose-units">Choose a unit</a><a href="#terms">Terms</a><a href="#guide-faq">FAQ</a></nav>
<section class="guide-section" id="comparison"><h2>REM vs EM vs PX: the reference is the difference</h2><p>For a regular element’s <code>font-size</code>, an em value multiplies the inherited font size. For <code>padding</code>, it multiplies that element’s own computed font size. A rem value on these properties uses the root font size, normally that of <code>&lt;html&gt;</code>. A px value is a CSS pixel length.</p><div class="table-wrap"><table><caption>Reference used by ordinary element declarations</caption><thead><tr><th>Declaration</th><th>What 1 unit refers to</th><th>At root 16px, parent 20px, child 25px</th></tr></thead><tbody><tr><td><code>font-size: 1em</code></td><td>Inherited font size</td><td>20px</td></tr><tr><td><code>padding: 1em</code></td><td>The element’s own font size</td><td>25px</td></tr><tr><td><code>padding: 1rem</code></td><td>Root font size</td><td>16px</td></tr><tr><td><code>padding: 16px</code></td><td>16 CSS pixels</td><td>16px</td></tr></tbody></table></div><p class="guide-source">Reference: <a href="https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/length">MDN: CSS lengths</a>. Root font-size and media-query contexts have additional rules; see the FAQ below.</p></section>'''
    demo = '''<section class="unit-demo" id="try-units" aria-labelledby="unit-demo-heading"><div class="unit-demo-head"><div><span class="eyebrow">CHANGE ONE REFERENCE</span><h2 id="unit-demo-heading">Try root, parent and child sizes</h2></div><button class="button small" id="unit-reset">Reset example</button></div><p>The child uses an em font size inside a parent with an explicit px font size. Edit the three values to see which declarations change.</p>
<div class="unit-controls"><div><label for="unit-root">Root font size (px)</label><input id="unit-root" type="number" min="1" max="64" step="any" value="16"></div><div><label for="unit-parent">Parent font size (px)</label><input id="unit-parent" type="number" min="1" max="96" step="any" value="20"></div><div><label for="unit-ratio">Child font size (em)</label><input id="unit-ratio" type="number" min="0.1" max="4" step="any" value="1.25"></div></div><p class="error" id="unit-error" role="alert" hidden></p>
<div id="unit-results"><p class="unit-computed" id="unit-summary" role="status">Child font size: 20px × 1.25 = 25px.</p><div class="unit-bars"><div><code>padding: 16px</code><strong id="unit-px-length">16px</strong><span class="unit-track" aria-hidden="true"><span id="unit-px-bar" style="width:64%"></span></span><small>Fixed CSS pixel value</small></div><div><code>padding: 1rem</code><strong id="unit-rem-length">16px</strong><span class="unit-track" aria-hidden="true"><span id="unit-rem-bar" style="width:64%"></span></span><small>Uses the root size</small></div><div><code>padding: 1em</code><strong id="unit-em-length">25px</strong><span class="unit-track" aria-hidden="true"><span id="unit-em-bar" style="width:100%"></span></span><small>Uses the child’s font size</small></div></div>
<div class="table-wrap"><table><caption>Independent declarations using the selected references</caption><thead><tr><th>Declaration</th><th>Computed length</th><th>Reference</th></tr></thead><tbody><tr><td><code>font-size: 1em</code></td><td id="unit-font-em">20px</td><td>Inherited parent size</td></tr><tr><td><code>font-size: 1rem</code></td><td id="unit-font-rem">16px</td><td>Root size</td></tr><tr><td><code>padding: 1em</code></td><td id="unit-padding-em">25px</td><td>Child size, using the em multiplier above</td></tr><tr><td><code>padding: 1rem</code></td><td id="unit-padding-rem">16px</td><td>Root size</td></tr></tbody></table></div>
<div class="unit-code"><div class="result-head"><span class="mono-label">CSS USED BY THE EXAMPLE</span>'''+copy('unit-css','Copy CSS')+'''</div><pre><code id="unit-css">html { font-size: 16px; }
.parent { font-size: 20px; }
.child { font-size: 1.25em; }</code></pre></div></div>
<p class="hint">The controls model a separate page. The parent’s px size stays independent of the root. Bars compare lengths on the same relative scale. Outputs are rounded to four decimal places.</p><noscript><p class="hint">JavaScript enables the controls. The default worked example above remains readable without it.</p></noscript></section>'''
    nested = '''<section class="guide-section" id="nested-em"><h2>Why nested em font sizes compound</h2><p>Suppose a container has a 16px font and two nested elements each declare <code>font-size: 1.25em</code>. The first becomes 20px. The second uses that inherited 20px and becomes 25px. A third level would be 31.25px. Each declaration introduces another multiplication.</p>'''+code_example('A complete nested example', '''<style>
  .base { font-size: 16px; }
  .level { font-size: 1.25em; }
</style>
<div class="base">
  <div class="level">20px
    <div class="level">25px</div>
  </div>
</div>''')+'''<p>With <code>font-size: 1.25rem</code> instead, both nested elements resolve to 20px when the root is 16px. Changing the parent’s font size does not add another rem multiplication. Merely nesting elements does not compound font size: the repeated relative declaration causes it.</p><p class="guide-source">Reference: <a href="https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-size#ems">MDN: font-size and nested em values</a>.</p></section>'''
    choices = '''<section class="guide-section" id="choose-units"><h2>When should you use rem, em or px?</h2><p>Choose the reference that matches the relationship you want. A component can reasonably use all three units.</p><div class="table-wrap"><table><thead><tr><th>Goal</th><th>A useful starting point</th><th>Reason</th></tr></thead><tbody><tr><td>A page-wide typography or spacing scale</td><td>rem</td><td>One root reference keeps unrelated components on the same scale.</td></tr><tr><td>A button’s padding that follows its text</td><td>em</td><td>The padding can grow when that button’s own font grows.</td></tr><tr><td>A border with a fixed CSS pixel width</td><td>px</td><td>The width stays independent of the font-size reference.</td></tr><tr><td>Line height that follows inherited text sizes</td><td>A unitless number</td><td>A multiplier such as 1.5 inherits as a number rather than a computed length.</td></tr></tbody></table></div>'''+code_example('A component using the three relationships', '''html { font-size: 100%; }
.card {
  font-size: 1.125rem;
  padding: 1em;
  border: 1px solid #d9e1ef;
  line-height: 1.5;
}
.card__title { font-size: 1.25em; }''')+'''<p>At a computed 16px root, this card has an 18px font and 18px padding. Its title is 22.5px. At a 20px root those values become 22.5px, 22.5px and 28.125px. The border stays 1 CSS pixel. <code>100%</code> does not guarantee 16px; the browser’s initial font size and the user’s settings still matter.</p><p>Test the component with larger default text, page zoom and narrow viewports. Using rem or em alone does not guarantee accessible text or a layout that reflows well. CSS pixels can also scale with page zoom; a CSS pixel is not necessarily one physical display pixel.</p><p class="guide-source">References: <a href="https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/line-height#number">MDN: unitless line-height</a> · <a href="https://www.w3.org/TR/css-values-4/#absolute-lengths">W3C CSS Values: absolute lengths</a>.</p></section>'''
    terms = '''<section class="guide-section" id="terms"><h2>Terms used in this guide</h2><dl class="guide-terms"><div><dt>Root element</dt><dd>The top element of an HTML document, normally <code>&lt;html&gt;</code>. Its font size supplies the rem reference for ordinary element declarations.</dd></div><div><dt>Computed font size</dt><dd>The font size after CSS rules and relative references have been resolved. Browser developer tools expose the computed value in CSS pixels.</dd></div><div><dt>Inherited font size</dt><dd>The font size passed down from an element’s parent. An em value on the element’s own font-size uses this starting size.</dd></div><div><dt>CSS pixel</dt><dd>A reference length used by CSS. Its relationship to physical display pixels depends on the display and browser settings.</dd></div><div><dt>Compounding</dt><dd>Repeated multiplication when nested elements each set a relative font size. In the worked example, 16 × 1.25 × 1.25 produces 25px.</dd></div></dl></section>'''
    questions = [
        ('Is 1rem always 16px?', 'No. For the ordinary element declarations shown here, 1rem equals the computed root font size. Check your page rather than assuming the browser default. Use the REM to PX converter with that root size for a numeric result.'),
        ('Does em always use the parent’s font size?', 'No. On font-size it uses the inherited font size; on properties such as padding it uses the element’s own computed font size. That is why the live example has different em results for font-size and padding.'),
        ('What happens on the root’s own font-size?', 'A rem value on the root’s own font-size refers to the initial font size, so it does not depend circularly on the root size being calculated. The live comparison models declarations on regular child elements.'),
        ('Do media queries use the same font references?', 'Font-relative units used outside an element context, such as media queries, use initial font metrics. Do not calculate a media-query breakpoint from a component’s current font size. Check the W3C font-relative length rules for this separate context.'),
        ('Should I replace every px value with rem?', 'No blanket replacement is needed. Decide whether the value should follow root text, local text or a fixed CSS pixel length. Then test the result with zoom, larger text and the layouts you support.'),
    ]
    ending = '''<section class="guide-section guide-faq" id="guide-faq"><h2>Common questions</h2>'''+''.join(faq(*q) for q in questions)+'''<p class="guide-source">Reference for root and media-query contexts: <a href="https://www.w3.org/TR/css-values-4/#font-relative-lengths">W3C CSS Values and Units Level 4, font-relative lengths (Working Draft)</a>.</p></section>
<section class="guide-next"><span class="eyebrow">CHECK YOUR OWN VALUES</span><h2>Convert with the root size your page uses</h2><p>Inspect the computed font-size of your page’s <code>&lt;html&gt;</code> element, then enter it in either converter. An em calculation also needs the relevant inherited or local font size.</p><div class="actions"><a class="button primary" href="/px-to-rem/">PX to REM</a><a class="button" href="/rem-to-px/">REM to PX</a></div></section></article>'''
    return intro + demo + nested + choices + terms + ending
