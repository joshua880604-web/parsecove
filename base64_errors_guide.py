"""A staged Base64 diagnosis walkthrough using complete public examples."""
import html
import json

CASES = [
    {'id': 'bad-padding', 'title': 'Incomplete padding: Zg=', 'value': 'Zg=', 'alphabet': 'standard',
     'explanation': 'The explicit padded value has three characters, so its padding is incomplete. This checker accepts Zg or Zg==, but it does not treat Zg= as either form.',
     'href': '/base64/?example=bad-padding', 'link': 'See the same padding error in the text decoder'},
    {'id': 'padded', 'title': 'Valid padded value: Zg==', 'value': 'Zg==', 'alphabet': 'standard',
     'explanation': 'The standard alphabet, length, padding and unused bits are valid. The decoded byte 0x66 is the UTF-8 character f.',
     'href': '/base64/?example=one-byte', 'link': 'Open this valid text example'},
    {'id': 'unpadded', 'title': 'Valid unpadded value: Zg', 'value': 'Zg', 'alphabet': 'standard',
     'explanation': 'This checker accepts a valid unpadded representation. Missing = signs alone do not prove the value is damaged; the receiving protocol may still require them.',
     'href': '/base64/?example=unpadded', 'link': 'Open the unpadded text example'},
    {'id': 'bad-character', 'title': 'Unexpected character: a$bc', 'value': 'a$bc', 'alphabet': 'standard',
     'explanation': 'The dollar sign is outside the standard Base64 alphabet. Get the original value or parse its surrounding format; do not delete arbitrary characters until decoding succeeds.',
     'href': '/base64/?example=bad-character', 'link': 'See the character check in the text decoder'},
    {'id': 'url-wrong', 'title': 'URL-safe value in a standard decoder', 'value': '8J-YgA', 'alphabet': 'standard',
     'explanation': 'The hyphen belongs to the URL-safe alphabet. The same value decodes as an emoji when the URL-safe alphabet is selected.',
     'href': '/base64/?example=url-safe', 'link': 'Open this value with URL-safe selected'},
    {'id': 'url-right', 'title': 'URL-safe value with the matching alphabet', 'value': '8J-YgA', 'alphabet': 'url',
     'explanation': 'With the matching alphabet, the bytes are f0 9f 98 80 and strict UTF-8 decoding produces the emoji. Alphabet selection and text interpretation are separate checks.',
     'href': '/base64/?example=url-safe', 'link': 'Open the matching-alphabet example'},
    {'id': 'trailing-bits', 'title': 'Non-zero unused trailing bits: Zh==', 'value': 'Zh==', 'alphabet': 'standard',
     'explanation': 'A permissive decoder may return f, but this checker rejects the non-zero unused bits. The canonical padded encoding of that known byte is Zg==. This comparison does not justify guessing a replacement for unknown data.',
     'href': '/base64/?example=trailing-bits', 'link': 'See canonical validation in the text decoder'},
    {'id': 'binary', 'title': 'Valid bytes that are not UTF-8 text', 'value': '+//v', 'alphabet': 'standard',
     'explanation': 'The bytes fb ff ef pass Base64 validation, but they are not valid UTF-8 text. They are not automatically an image either. Inspect the bytes and determine the original data format.',
     'href': '/base64url-decode/?example=binary', 'link': 'Inspect these same bytes as Base64URL hex'},
    {'id': 'data-url', 'title': 'A complete data URL pasted as raw Base64', 'value': 'data:text/plain;base64,Zg==', 'alphabet': 'standard',
     'explanation': 'This is a wrapper containing a Base64 payload, not one raw Base64 string. For this known text/plain example, the payload after the comma is Zg==, which decodes to f.',
     'href': '/base64/?example=one-byte', 'link': 'Open the extracted payload from this example'},
]

JAVASCRIPT = r'''function readStandardBase64(value) {
  const clean = value.replace(/\s/g, '');
  if (clean.length > 4096) throw new Error('Small-example limit.');
  if (!/^[A-Za-z0-9+/]*={0,2}$/.test(clean)) throw new Error('Alphabet.');
  const bare = clean.replace(/=+$/, '');
  if (bare.length % 4 === 1 || (clean.includes('=') && clean.length % 4 !== 0)) {
    throw new Error('Length or padding.');
  }
  const binary = atob(bare + '='.repeat((4 - bare.length % 4) % 4));
  if (btoa(binary).replace(/=+$/, '') !== bare) throw new Error('Trailing bits.');
  return Uint8Array.from(binary, char => char.charCodeAt(0));
}
for (const sample of ['Zg==', 'Zg', 'Zg=', 'a$bc', 'Zh==', '+//v', '8J-YgA']) {
  try {
    const bytes = readStandardBase64(sample);
    let result;
    try { result = new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
    catch { result = 'valid bytes; not UTF-8 text'; }
    console.log(sample + ': ' + result);
  } catch { console.log(sample + ': rejected'); }
}'''

PYTHON = r'''import base64
import re

def read_standard_base64(value):
    clean = "".join(value.split())
    if len(clean) > 4096:
        raise ValueError("Small-example limit.")
    if not re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", clean):
        raise ValueError("Alphabet.")
    bare = clean.rstrip("=")
    if len(bare) % 4 == 1 or ("=" in clean and len(clean) % 4 != 0):
        raise ValueError("Length or padding.")
    data = base64.b64decode(bare + "=" * (-len(bare) % 4), validate=True)
    if base64.b64encode(data).decode("ascii").rstrip("=") != bare:
        raise ValueError("Trailing bits.")
    return data

for sample in ["Zg==", "Zg", "Zg=", "a$bc", "Zh==", "+//v", "8J-YgA"]:
    try:
        data = read_standard_base64(sample)
        try:
            result = data.decode("utf-8")
        except UnicodeDecodeError:
            result = "valid bytes; not UTF-8 text"
        print(sample + ": " + result)
    except ValueError:
        print(sample + ": rejected")'''


def base64_errors_guide(code_example, faq, copy):
    first = CASES[0]
    options = ''.join(f'<option value="{c["id"]}">{html.escape(c["title"])}</option>' for c in CASES)
    fixtures = json.dumps(CASES).replace('<', '\\u003c')
    intro = '''<article class="guide-article"><header class="guide-header"><nav class="guide-breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span aria-current="page">Base64 errors</span></nav><span class="eyebrow">ENCODING · WORKED GUIDE</span><h1>Invalid Base64: why decoding fails</h1><p class="guide-deck">First identify the input format, then validate the encoding, then interpret the decoded bytes. A padding error, an alphabet mismatch and a UTF-8 failure happen at different stages and need different checks.</p><p class="guide-byline">By <a href="/about/">ParseCove</a> · Published <time datetime="2026-11-27">27 November 2026</time></p></header>
<nav class="guide-toc" aria-label="On this page"><strong>On this page</strong><a href="#base64-check-order">Where to start</a><a href="#base64-error-examples">Try complete examples</a><a href="#base64-padding">Padding and trailing bits</a><a href="#base64-check-code">JavaScript & Python</a><a href="#base64-byte-type">Interpret the bytes</a><a href="#base64-error-terms">Terms & FAQ</a></nav>
<section class="guide-section" id="base64-check-order"><h2>Check the wrapper, alphabet and output type</h2><ol class="guide-steps"><li><strong>Identify what you copied.</strong> A raw Base64 value, a data URL, a JSON field and a complete dot-separated token are different input forms. Parse the surrounding format before passing its encoded value to a decoder.</li><li><strong>Choose the expected alphabet.</strong> Standard Base64 uses <code>+</code> and <code>/</code>; Base64URL uses the ASCII hyphen <code>-</code> and underscore <code>_</code>. Use the field’s documented format.</li><li><strong>Validate before interpreting bytes.</strong> Check the characters, length, explicit padding and canonical trailing bits. Only then ask whether the decoded bytes are UTF-8 text, an image or another format.</li></ol><p>The tools and snippets here intentionally ignore whitespace and reject other unexpected characters. Decoders in other environments may apply different policies. A successful format check also does not prove that a value is complete, authentic or the data type you expected.</p></section>'''
    demo = f'''<section class="base64-diagnostic" id="base64-error-examples" aria-labelledby="base64-diagnostic-heading"><span class="eyebrow">FIXED EXAMPLES · REAL DECODER RESULTS</span><h2 id="base64-diagnostic-heading">See which stage rejects the value</h2><p>Choose a complete public example. These cases isolate one issue at a time; the linked tools handle your own input.</p><label for="b64-case-select">Example to inspect</label><select id="b64-case-select">{options}</select><div class="b64-case-source"><div class="result-head"><label class="mono-label" for="b64-case-input">COMPLETE EXAMPLE INPUT</label>{copy('b64-case-input','Copy input')}</div><textarea id="b64-case-input" class="mono" rows="2" readonly>{first['value']}</textarea><p class="hint">Selected alphabet: <strong id="b64-case-alphabet">Standard (+ /)</strong></p></div><div class="b64-stage-grid"><div><h3>1. Base64 encoding check</h3><span class="b64-stage-status" id="b64-case-encoding" data-state="fail">Rejected</span><p id="b64-case-parser-message">Invalid Base64 length or padding.</p></div><div><h3>2. UTF-8 text check</h3><span class="b64-stage-status" id="b64-case-utf8" data-state="skipped">Not attempted</span><p id="b64-case-text-message">The encoding must be accepted before text decoding.</p></div></div><p class="b64-case-summary" id="b64-case-summary" role="status">Encoding rejected; UTF-8 decoding was not attempted.</p><div id="b64-case-bytes-wrap" hidden><span class="mono-label">DECODED BYTES · HEX</span><code id="b64-case-hex"></code></div><div id="b64-case-text-wrap" hidden><div class="result-head"><label class="mono-label" for="b64-case-text">DECODED UTF-8 TEXT</label>{copy('b64-case-text','Copy text')}</div><textarea id="b64-case-text" class="mono" rows="2" readonly></textarea></div><p id="b64-case-explanation">{html.escape(first['explanation'])}</p><a class="button" id="b64-case-next" href="{first['href']}">{html.escape(first['link'])}</a><noscript><p class="hint">JavaScript switches the examples. The initial padding case and the written checks remain readable without it.</p></noscript></section><script type="application/json" id="base64-diagnostic-cases">{fixtures}</script>'''
    padding = '''<section class="guide-section" id="base64-padding"><h2>Missing padding and incorrect padding are different</h2><p><code>Zg==</code> is a padded encoding of the UTF-8 character <code>f</code>. This checker also accepts the unpadded <code>Zg</code>. It rejects <code>Zg=</code>, because the explicitly padded value has an invalid length. Whether unpadded values are permitted is part of the receiving format’s contract.</p><div class="table-wrap"><table><thead><tr><th>Check</th><th>What it tells you</th></tr></thead><tbody><tr><td>Payload length modulo 4 is 1</td><td>The value cannot represent a complete final Base64 group.</td></tr><tr><td>Padding appears in the middle</td><td>The supplied representation is malformed.</td></tr><tr><td>Unused final bits are non-zero</td><td>A strict canonical check can reject a value that a permissive decoder accepts.</td></tr><tr><td>All format checks pass</td><td>You have a valid representation of some bytes, not proof that the original data was complete or correct.</td></tr></tbody></table></div><p>For a concrete trailing-bit example, a permissive decoder may turn <code>Zh==</code> into <code>f</code>. Re-encoding that byte gives <code>Zg==</code>, revealing the non-canonical spelling. This site rejects it. For unknown input, check the source rather than guessing replacement characters.</p><p class="guide-source">Reference: <a href="https://www.rfc-editor.org/rfc/rfc4648">RFC 4648, sections 3.2–3.5: padding, alphabets and canonical encoding</a>.</p></section>'''
    code = '''<section class="guide-section" id="base64-check-code"><h2>Separate byte validation from UTF-8 decoding in code</h2><p>These complete examples use the standard alphabet and accept valid unpadded values. They deliberately cap small examples at 4,096 encoded characters after whitespace removal. The two tools have their own documented size limits.</p><div id="base64-error-js">'''+code_example('JavaScript: validate bytes, then decode UTF-8', JAVASCRIPT)+'''</div><p>The browser’s <code>atob()</code> returns a binary string. The byte check above re-encodes that result to check canonical trailing bits; <code>TextDecoder</code> with <code>fatal: true</code> then reports malformed UTF-8 instead of silently inserting replacement characters.</p><div id="base64-error-python">'''+code_example('Python 3: the same checks and complete sample loop', PYTHON)+'''</div><p>Python’s <code>validate=True</code> rejects non-alphabet characters. The explicit length and re-encoding checks keep this example’s policy consistent for padded and unpadded values. Decode to text only when UTF-8 is the expected content encoding.</p><p class="guide-source">References: <a href="https://developer.mozilla.org/en-US/docs/Web/API/Window/atob">MDN: atob</a> · <a href="https://developer.mozilla.org/en-US/docs/Web/API/TextDecoder/fatal">MDN: fatal UTF-8 decoding</a> · <a href="https://docs.python.org/3/library/base64.html#base64.b64decode">Python: b64decode</a>.</p></section>'''
    kinds = '''<section class="guide-section" id="base64-byte-type"><h2>Valid bytes may need a different tool</h2><div class="table-wrap"><table><thead><tr><th>Expected content</th><th>Next step</th></tr></thead><tbody><tr><td>UTF-8 text in standard Base64</td><td>Use <a href="/base64/">Base64 encode / decode</a>.</td></tr><tr><td>URL-safe encoded text or binary bytes</td><td>Select the matching alphabet or inspect hex in the <a href="/base64url-decode/">Base64URL tool</a>.</td></tr><tr><td>A PNG, JPEG, GIF or WebP image</td><td>Use <a href="/base64-to-image/">Base64 to image</a> to check the signature, preview and original-byte download.</td></tr><tr><td>A full image data URL</td><td>Use the image viewer’s data URL input. The <a href="/guides/save-base64-image/">image-saving guide</a> explains its prefix and payload.</td></tr><tr><td>A dot-separated token</td><td>Identify the encoded segment and its documented alphabet. Decoding a segment does not verify a token’s signature or claims.</td></tr></tbody></table></div><p>The binary example in the walkthrough contains <code>fb ff ef</code>. It is valid Base64 data, but invalid UTF-8 and not a supported image signature. Binary data can also represent compressed files or text in a different character encoding. Identify the original format instead of forcing it through a text decoder.</p></section>'''
    terms = '''<section class="guide-section" id="base64-error-terms"><h2>Terms used in this guide</h2><dl class="guide-terms"><div><dt>Alphabet</dt><dd>The permitted encoding symbols. Standard and URL-safe Base64 differ in their last two symbols.</dd></div><div><dt>Padding</dt><dd>Trailing = characters used by padded Base64 representations to complete their final group.</dd></div><div><dt>Canonical encoding</dt><dd>A normalized encoding of the bytes, including zero values in the unused trailing bits.</dd></div><div><dt>UTF-8 validation</dt><dd>A separate check that a byte sequence represents valid UTF-8 text. Passing Base64 validation does not establish that.</dd></div></dl></section>'''
    questions = [
        ('Is a value without = always invalid?', 'No. Some formats allow unpadded Base64 or Base64URL. Check the length, trailing bits and receiving protocol rather than treating missing padding as proof of corruption.'),
        ('Should I strip every non-alphanumeric character?', 'No. Characters such as +, /, -, _ and = may be meaningful. Parse wrappers deliberately, select the correct alphabet and get the original value if unexpected characters remain.'),
        ('Does unreadable decoded text mean Base64 is broken?', 'Not necessarily. The encoded bytes may be binary data or text in another character encoding. Check the expected content type and inspect bytes before choosing a text decoder.'),
        ('Can I repair a truncated value by adding padding?', 'Padding cannot recover missing data. It can complete a valid unpadded representation, but a truncated payload may remain wrong even if a decoder accepts its syntax.'),
    ]
    ending = '''<section class="guide-section guide-faq" id="base64-error-faq"><h2>Common questions</h2>'''+''.join(faq(*q) for q in questions)+'''</section><section class="guide-next"><span class="eyebrow">CHECK THE RIGHT STAGE</span><h2>Choose the tool for the data you expect</h2><div class="actions"><a class="button primary" href="/base64/">Base64 text</a><a class="button" href="/base64url-decode/">Base64URL & hex</a><a class="button" href="/base64-to-image/">Base64 images</a></div></section></article>'''
    return intro + demo + padding + code + kinds + terms + ending
