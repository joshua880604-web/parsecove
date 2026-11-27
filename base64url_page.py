"""Static content for the URL-safe Base64 entry point."""
from faq_content import tool_faqs


def base64url_workbench(icon, segmented, copy):
    return '''<section class="workbench url-workbench"><div class="bench-toolbar">'''+segmented([('decode','Decode'),('encode','Encode')],'url-modes')+'''<span class="quiet">URL-safe · RFC 4648</span></div>
<div class="bench-body"><div class="input-panel">
<div id="url-format-wrap"><label for="url-format">Decode output</label><select id="url-format"><option value="text">UTF-8 text</option><option value="hex">Hex bytes</option></select></div>
<div class="check-field" id="url-padding-wrap" hidden><label><input type="checkbox" id="url-padding"> Add = padding when encoding</label></div>
<label for="url-input" id="url-input-label">Base64URL input</label><textarea id="url-input" class="mono" rows="8" spellcheck="false" maxlength="2000000" aria-describedby="url-hint">SGVsbG8sIHdvcmxkIQ</textarea>
<p class="hint" id="url-hint">Paste one URL-safe value using A–Z, a–z, 0–9, - and _. Valid padded or unpadded input is accepted; whitespace is ignored. Up to 2 million encoded characters.</p>
<div class="actions"><button class="button primary" id="url-convert">Decode Base64URL</button><button class="button ghost" id="url-clear">Clear</button></div>
<div class="quick-values"><span>Try an example:</span><button class="button small" data-url-example="emoji">Emoji</button><button class="button small" data-url-example="json">JSON text</button><button class="button small" data-url-example="binary">Binary bytes</button></div>
<p class="error" id="url-error" role="alert" hidden></p></div>
<div class="result-panel"><div class="result-head"><label class="mono-label" id="url-output-label" for="url-output">DECODED TEXT</label>'''+copy('url-output')+'''</div>
<textarea id="url-output" class="mono result-editor" rows="6" readonly placeholder="Your result will appear here.">Hello, world!</textarea><p class="result-sub" id="url-stats"></p><p class="hint url-note" id="url-note" role="status" hidden></p>
<div class="actions"><button class="button small" id="url-download" disabled>Download result</button><button class="button small" id="url-bytes-download" disabled>Download bytes</button></div>
<div class="url-standard"><div class="result-head"><label for="url-standard" class="mono-label">STANDARD BASE64 · SAME BYTES</label>'''+copy('url-standard','Copy')+'''</div><textarea id="url-standard" class="mono" rows="2" readonly>SGVsbG8sIHdvcmxkIQ==</textarea></div>
<a class="inline-link" href="/base64/">Have standard Base64 input? Open the Base64 decoder.</a><div class="panel-note">'''+icon('shield')+''' Calculated on your device</div></div></div></section>'''


def base64url_guide(docs, extra_section, code_example):
    intro = docs(
        'How to decode Base64URL',
        'Base64URL is the URL- and filename-safe alphabet defined in RFC 4648 section 5. It replaces the standard Base64 characters <code>+</code> and <code>/</code> with the ASCII hyphen <code>-</code> and underscore <code>_</code>. Paste one encoded value above and choose UTF-8 text or Hex bytes before decoding.',
        'Base64URL: + → - &nbsp; / → _ &nbsp; trailing = may be omitted',
        [
            ('Is Base64URL the same as Base64?', 'Both represent the same bytes with 64 printable symbols. Their last two alphabet characters differ. Base64URL is a separate alphabet, not URL percent-encoding; this tool does not automatically decode % escapes.'),
            ('Why does a valid value produce no text?', 'An encoded value can contain binary bytes that are not valid UTF-8. The tool then leaves the text result empty and explains the issue. Choose Hex bytes or download the original bytes. The standard Base64 comparison still represents the same bytes.'),
            ('Can I decode a JWT?', 'Paste only one encoded segment from a token, such as a header or payload. A complete dot-separated token is not one Base64URL value. Decoding a segment does not verify a signature, validate claims or establish authenticity.'),
            ('Are inputs uploaded or saved?', 'Conversion runs in your browser. The application does not upload inputs, store input history or put values in the URL. Clipboard and downloads are used only when you press their buttons. Normal website requests still go to the hosting provider.'),
        ] + tool_faqs('base64url-decode'),
        '<a href="https://www.rfc-editor.org/rfc/rfc4648#section-5">RFC 4648 §5: URL-safe alphabet</a> · <a href="https://www.rfc-editor.org/rfc/rfc7519">RFC 7519: JWT</a>',
    )
    reference = extra_section(
        'base64url-padding', 'Base64URL padding and validation',
        'Missing padding can be reconstructed from a valid length. Padding alone cannot repair invalid characters, truncated data or non-zero trailing bits.',
        '''<div class="table-wrap"><table><caption>Length of the value after removing whitespace and trailing =</caption><thead><tr><th>Length modulo 4</th><th>Required padding for a padded representation</th></tr></thead><tbody><tr><td>0</td><td>No padding</td></tr><tr><td>2</td><td>==</td></tr><tr><td>3</td><td>=</td></tr><tr><td>1</td><td>Invalid encoded length</td></tr></tbody></table></div>
<div class="trouble-grid"><article><h3>Padded and unpadded input</h3><p><code>Zg</code> and <code>Zg==</code> both decode to <code>f</code>. <code>Zg=</code> is rejected because its explicit padding is incomplete. Encoding above omits padding by default; enable Add = padding if the receiving system requires it.</p></article><article><h3>Strict alphabet checks</h3><p>Use the ASCII hyphen <code>-</code>, not a typographic minus sign. Standard Base64 <code>+</code> and <code>/</code>, percent escapes and data URI prefixes are rejected here. Use the <a href="/base64/">standard Base64 tool</a> or <a href="/base64-to-image/">image viewer</a> for those input types.</p></article><article><h3>Validate the final bits</h3><p><code>Zg</code> is the canonical encoding of <code>f</code>. <code>Zh</code> is rejected for non-zero unused trailing bits, even though a permissive decoder might return the same byte.</p></article><article><h3>Text and byte limits</h3><p>Decode up to 2 million encoded characters, including any whitespace. Encoding accepts up to 1 MB (1,000,000 bytes) of UTF-8 text. Bytes and text downloads are generated locally; downloading bytes does not identify or convert their file format.</p></article></div>''',
    )
    examples = extra_section(
        'base64url-examples', 'Base64URL examples: Unicode, JSON and binary',
        'These public fixtures show the distinction between an encoding alphabet and the type of data it contains. The example buttons load complete values into the tool.',
        '''<div class="table-wrap"><table><thead><tr><th>Original data</th><th>Base64URL, without padding</th><th>Standard Base64</th></tr></thead><tbody><tr><td>Hello, world!</td><td><code>SGVsbG8sIHdvcmxkIQ</code></td><td><code>SGVsbG8sIHdvcmxkIQ==</code></td></tr><tr><td>😀 (UTF-8 text)</td><td><code>8J-YgA</code></td><td><code>8J+YgA==</code></td></tr><tr><td>{&quot;message&quot;:&quot;Hello&quot;}</td><td><code>eyJtZXNzYWdlIjoiSGVsbG8ifQ</code></td><td><code>eyJtZXNzYWdlIjoiSGVsbG8ifQ==</code></td></tr><tr><td>Hex bytes fb ff ef</td><td><code>-__v</code></td><td><code>+//v</code></td></tr></tbody></table></div><p class="guide-note">JSON remains text in this tool: it is not parsed, executed or validated. Binary bytes can be inspected as hex and downloaded even when they are not valid UTF-8. For a full image preview, use <a href="/base64-to-image/">Base64 to image</a>.</p>''',
    )
    code = extra_section(
        'base64url-code', 'Decode a known Base64URL value in JavaScript or Python',
        'Both snippets decode the fixed, valid emoji example. They illustrate alphabet normalization, padding and UTF-8 decoding; the tool above also checks alphabet, length and unused trailing bits.',
        '<div class="code-grid">'+code_example(
            'JavaScript: Base64URL to UTF-8',
            "const value = '8J-YgA';\nconst standard = value.replace(/-/g, '+').replace(/_/g, '/');\nconst padded = standard + '='.repeat((4 - standard.length % 4) % 4);\nconst bytes = Uint8Array.from(atob(padded), c => c.charCodeAt(0));\nnew TextDecoder('utf-8', { fatal: true }).decode(bytes);\n// 😀",
        )+code_example(
            'Python: Base64URL to UTF-8',
            'import base64\n\nvalue = "8J-YgA"\npadded = value + "=" * (-len(value) % 4)\nbase64.urlsafe_b64decode(padded).decode("utf-8")\n# 😀',
        )+'</div><p class="guide-note">Base64URL is an encoding, so anyone with the value can decode it. It does not encrypt text or authenticate a token. Use <a href="/base64/">Base64 encode / decode</a> when you need the standard alphabet.</p>',
    )
    return intro + reference + examples + code
