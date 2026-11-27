"""Shared image workbench and task-specific encoder documentation."""


def image_workbench(initial_mode, icon, segmented):
    if initial_mode not in ('decode', 'encode'):
        raise ValueError('Unknown image mode')
    encoding = initial_mode == 'encode'
    modes = [('encode', 'Image to Base64'), ('decode', 'Base64 to image')]
    if not encoding:
        modes.reverse()
    image_icon = icon('image')

    def samples(attribute, verb):
        buttons = []
        for key, label, ext in [('png', 'PNG', 'png'), ('jpeg', 'JPEG', 'jpg'), ('webp', 'WebP', 'webp')]:
            buttons.append(f'''<button type="button" class="sample-image" {attribute}="{key}" aria-label="{verb} {label} example">
<img src="/assets/examples/sample.{ext}" width="96" height="54" loading="lazy" alt="Blue sample card with a green circle">
<span>{label} · 320 × 180</span></button>''')
        return '<div class="sample-gallery" aria-label="Image examples"><span class="sample-caption">Try a real image</span><div class="sample-buttons">' + ''.join(buttons) + '</div></div>'

    text_output = f'''<div id="image-text-wrap"{'' if encoding else ' hidden'}>
<div class="result-head"><label for="image-text">Encoded output</label></div>
<textarea id="image-text" class="mono" rows="7" readonly spellcheck="false" placeholder="Choose an image to generate its complete Base64 output."></textarea>
<div class="actions image-text-actions">
<button type="button" class="button" id="image-text-copy" data-copy="image-text" disabled>{icon('copy')} Copy output</button>
<button type="button" class="button primary" id="image-text-download" disabled>Download output</button>
</div></div>'''
    preview = f'''<div class="image-preview" id="image-preview"><div id="image-empty">{image_icon}
<strong>{'Start with an image.' if encoding else 'A little less mystery.'}</strong>
<span>{'Choose a file or load an example to create Base64.' if encoding else 'Your decoded image will appear here.'}</span></div>
<img id="image-output" alt="Preview of your converted image" hidden></div>'''
    result = (text_output + preview) if encoding else (preview + text_output)
    other_link = ('<a class="inline-link" href="/base64-to-image/">Open the Base64 to image converter</a>' if encoding else
                  '<a class="inline-link" href="/image-to-base64/">Open the dedicated image to Base64 converter</a>')
    return f'''<section class="workbench">
<div class="bench-toolbar">{segmented(modes, 'image-modes')}<span class="quiet">PNG · JPEG · GIF · WebP</span></div>
<div class="bench-body"><div class="input-panel">
<div id="image-decode-input"{' hidden' if encoding else ''}>
<label for="image-input">Base64 image or data URI</label>
<textarea id="image-input" class="mono" rows="9" placeholder="data:image/png;base64,iVBORw0KGgo…" spellcheck="false"></textarea>
<p class="hint">Paste raw Base64 or a full data URI. Maximum decoded file size: 10 MB. SVG is not supported in this version.</p>
<div class="actions"><button class="button primary" id="image-convert">Preview image</button><button class="button" id="image-sample">Load example</button></div>
{samples('data-image-example', 'Load')}
</div>
<div id="image-encode-input"{'' if encoding else ' hidden'}>
<label class="dropzone" id="image-drop" for="image-file">{image_icon}<strong>Drop an image here</strong>
<span>or choose a file from your device</span><input type="file" id="image-file" accept="image/png,image/jpeg,image/gif,image/webp">
<small>PNG, JPEG, GIF or WebP · up to 10 MB</small></label>
<p class="hint" id="image-file-name" aria-live="polite">No image selected.</p>
<label for="image-format">Output format</label><select id="image-format">
<option value="uri">Data URL (data URI)</option><option value="raw">Raw Base64</option>
<option value="html">HTML image tag</option><option value="css">CSS background-image</option></select>
{samples('data-image-encode-example', 'Encode')}
</div>
<button class="button ghost" id="image-clear">Clear all</button>
<p class="error" id="image-error" role="alert" hidden></p>
<div class="error-help" id="image-error-help" hidden><strong id="image-error-title">{'Check the file' if encoding else 'Check the source'}</strong>
<p id="image-error-detail">{'Choose a valid PNG, JPEG, GIF or WebP image within the size and preview limits.' if encoding else 'Paste the Base64 value or a data URI, not a complete HTML tag or JSON response. The decoded bytes must be a supported image.'}</p>
<a id="image-error-link" href="{'#encoding-help' if encoding else '#image-troubleshooting'}">View the image troubleshooting guide</a></div>
<p class="notice" id="image-warning" role="status" hidden></p>
<p class="hint image-direction-link">{other_link}</p>
</div><div class="result-panel">
<div class="result-head"><span class="mono-label" id="image-result-title">{'IMAGE TO BASE64' if encoding else 'IMAGE PREVIEW'}</span><span class="pill" id="image-status">{'Waiting for an image' if encoding else 'Waiting for input'}</span></div>
{result}
<dl class="image-meta" id="image-meta" hidden><div><dt>Detected format</dt><dd id="image-mime"></dd></div>
<div><dt>Dimensions</dt><dd id="image-dimensions"></dd></div><div><dt>Original bytes</dt><dd id="image-size"></dd></div></dl>
<a id="image-download" class="button{' primary' if not encoding else ''}" hidden>Download original image</a>
<p class="hint" id="image-preservation" hidden>Original bytes, original format. Downloading does not compress or convert this image.</p>
<div class="panel-note">{icon('shield')} Files stay on your device</div>
</div></div></section>'''


def image_encoder_guide(docs, extra_section, code_example):
    context = docs(
        'How to convert an image to Base64',
        'Choose a PNG, JPEG, GIF or WebP file, then select the output you need: a complete data URL, raw Base64, an HTML image tag or a CSS background declaration. Copy the result or download it as text. The conversion runs in your browser and keeps the original image bytes.',
        'Base64 length = 4 × ceil(original byte count ÷ 3)',
        [
            ('What is the difference between raw Base64 and a data URL?',
             'Raw Base64 contains only the encoded bytes. A data URL adds a media type and the ;base64, prefix, for example data:image/png;base64,. HTML and CSS image references need that complete URL, not just the raw payload.'),
            ('Does Base64 compress or convert the image?',
             'No. Base64 represents the original bytes as text. For larger files it adds roughly one third to the byte count, plus the data URL prefix. A JPEG remains JPEG; changing an extension does not convert its format.'),
            ('Which images can I encode?',
             'PNG, JPEG, GIF and WebP are supported. The file limit is 10,485,760 bytes and the preview limit is 40 megapixels. The byte signature and the browser image decoder must both accept the image. SVG is not supported.'),
            ('Can I convert an image URL directly?',
             'This tool reads local files you select or drop. It does not fetch remote image URLs. Save the image to your device, then choose that file here.'),
            ('Does my image get uploaded?',
             'The image bytes are read and encoded on your device. Tool inputs are not sent to a conversion API. The website itself still makes normal requests to load its pages, scripts and local examples.'),
        ],
        '<a href="https://www.rfc-editor.org/rfc/rfc4648">RFC 4648: Base64</a> · <a href="https://www.rfc-editor.org/rfc/rfc2397">RFC 2397: Data URLs</a>',
    )
    steps = ('<ol class="encoding-steps"><li>Choose an image or try one of the complete PNG, JPEG or WebP examples above.</li>'
             '<li>Keep Data URL selected for an HTML/CSS image reference, or choose Raw Base64 when an API expects only the payload.</li>'
             '<li>Copy the full output or select Download output. The preview reports the detected format, dimensions and original byte count.</li></ol>')
    formats = ('<div class="table-wrap"><table><caption>Choose the output for your task</caption>'
               '<thead><tr><th>Output</th><th>Use it for</th></tr></thead><tbody>'
               '<tr><td>Data URL</td><td>A complete image URL with a media type and Base64 prefix.</td></tr>'
               '<tr><td>Raw Base64</td><td>An API field that expects only encoded bytes.</td></tr>'
               '<tr><td>HTML image tag</td><td>An image element. Add alt text that describes the actual image.</td></tr>'
               '<tr><td>CSS background-image</td><td>A CSS declaration. Set the element size and other presentation rules yourself.</td></tr>'
               '</tbody></table></div>')
    examples = ('<div class="code-grid">' +
                code_example('Use a complete data URL in HTML', '<img src="PASTE_YOUR_DATA_URL_HERE" alt="Describe the image">') +
                code_example('Use it as a CSS background', '.icon {\n  width: 32px;\n  height: 32px;\n  background-image: url("PASTE_YOUR_DATA_URL_HERE");\n  background-size: contain;\n  background-repeat: no-repeat;\n}') +
                '</div><p class="guide-note">Replace the placeholder with the complete Data URL output, including its data:image/...;base64, prefix. The sample buttons above produce complete, working values. Copying the HTML output starts with an empty alt attribute; add an appropriate description when you use the image.</p>')
    reference = extra_section('image-encoding-reference', 'Use image Base64 in HTML, CSS and API fields',
                              'A Base64 payload and a complete image URL serve different purposes. Choose the format expected by the destination.', steps + formats + examples)
    help_body = ('<div class="trouble-grid"><article><h3>The file cannot be encoded</h3><p>Check that it is a valid PNG, JPEG, GIF or WebP within the size and preview limits. A renamed file can have a different byte format; output uses the detected format rather than trusting its extension.</p></article>'
                 '<article><h3>My copied image does not display</h3><p>Use the complete Data URL in an image src or CSS url(). Raw Base64 needs the media-type prefix before a browser can use it as an image URL. The destination may also restrict data: images through its content security policy.</p></article>'
                 '<article><h3>Why did the output get larger?</h3><p>Base64 maps each three input bytes to four text characters, with padding when needed. An original 3,000-byte image produces 4,000 Base64 characters before its data URL prefix. Use a normal image file URL when inline text is unsuitable.</p></article>'
                 '<article><h3>I need to decode an image instead</h3><p>Open the <a class="inline-link" href="/base64-to-image/">Base64 to image converter</a> to paste an existing value, preview its bytes and download the original image. For UTF-8 text, use the <a class="inline-link" href="/base64/">Base64 decoder and encoder</a>.</p></article></div>')
    help_section = extra_section('encoding-help', 'Image to Base64 troubleshooting',
                                 'Encoding changes how bytes are represented. It does not repair corrupt images, convert formats or make a large payload smaller.', help_body)
    return context + reference + help_section
