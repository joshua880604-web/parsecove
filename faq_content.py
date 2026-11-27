"""Task-specific tool questions and stable links to their complete answers."""

TOOL_FAQS = {
    'unix-timestamp-converter': [
        ('Can I convert a date without a timezone?',
         'This converter requires a complete ISO date and time with <code>Z</code> or a numeric offset. '
         'For example, <code>2023-11-14T22:13:20Z</code> and <code>2023-11-14T17:13:20-05:00</code> '
         'represent the same instant. A date such as <code>2023-11-14</code> needs a time and an intended '
         'timezone before you can identify an instant. The display-timezone selector does not supply a '
         'missing input timezone. See the <a href="/guides/unix-timestamp-seconds-vs-milliseconds/#timestamp-zone">'
         'worked UTC and offset example</a>.',
         'faq-date-needs-timezone'),
    ],
    'px-to-rem': [
        ('What is 14px in rem?',
         '<code>14px ÷ 16px = 0.875rem</code> at a 16px root. At a 20px root, '
         '<code>14px ÷ 20px = 0.7rem</code>. Enter 14 above and set Root font size to the computed '
         'root size on your page. The <a href="/guides/rem-vs-em/#comparison">REM, EM and PX comparison</a> '
         'explains which font size each unit uses.',
         'faq-14px-in-rem'),
    ],
    'rem-to-px': [
        ('When should I use rem instead of px?',
         'Use rem when a length should follow the root font size, such as a page-wide type or spacing '
         'scale. A px length expresses a CSS pixel value independently of that root size. One component '
         'can use both. Test larger text, zoom and narrow layouts; a unit choice alone does not guarantee '
         'accessibility. See <a href="/guides/rem-vs-em/#choose-units">worked choices for rem, em and px</a>.',
         'faq-rem-or-px'),
    ],
    'base64': [
        ('How do I decode a Base64 string?',
         'Paste the complete encoded value, select Standard or URL-safe to match its source, keep '
         'Decode selected, then choose Decode text. For example, <code>SGVsbG8=</code> produces '
         '<code>Hello</code>. This text decoder expects UTF-8 bytes. For a rejected value, follow the '
         '<a href="/guides/fix-invalid-base64/#base64-error-examples">step-by-step error examples</a>; '
         'for URL-safe binary values, inspect hex in the <a href="/base64url-decode/">Base64URL tool</a>. '
         'Use the <a href="/base64-to-image/">image viewer</a> for supported image bytes.',
         'faq-decode-base64-string'),
    ],
    'base64url-decode': [
        ('Do I need to add = padding before decoding Base64URL?',
         'This tool accepts valid padded and unpadded input: <code>8J-YgA==</code> and '
         '<code>8J-YgA</code> both decode to 😀. It still rejects malformed padding, impossible lengths '
         'and non-zero unused trailing bits. Padding cannot restore missing payload data. Follow the '
         'receiving format’s rules when encoding; see the <a href="/guides/fix-invalid-base64/#base64-padding">'
         'padding and trailing-bit explanation</a>.',
         'faq-base64url-padding'),
    ],
    'base64-to-image': [
        ('Can I view a Base64 image without a data URL prefix?',
         'Yes. Paste either the complete raw Base64 payload or a complete Base64 data URL, then choose '
         'Preview image. The viewer checks the decoded byte signature and browser image decoding. '
         'Changing a prefix cannot turn arbitrary bytes into an image. PNG, JPEG, GIF and WebP are '
         'supported; a copied fragment or an entire HTML tag is not the expected input. See '
         '<a href="/guides/save-base64-image/#data-url-parts">a complete data URL and its raw payload</a>.',
         'faq-raw-base64-image'),
    ],
    'image-to-base64': [
        ('How do I embed a Base64 image in HTML?',
         'Choose your image, select HTML image tag, and copy the complete output into your HTML. '
         'Alternatively, put the full Data URL output in the <code>src</code> attribute of an '
         '<code>&lt;img&gt;</code> element. Raw Base64 alone is not an image URL. Add suitable '
         '<code>alt</code> text for the image’s purpose. The '
         '<a href="/guides/save-base64-image/#embed-image">complete HTML example</a> shows a working '
         'image rather than a shortened payload.',
         'faq-base64-image-html'),
    ],
}


def tool_faqs(slug):
    return TOOL_FAQS.get(slug, [])
