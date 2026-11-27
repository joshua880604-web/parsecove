"""Task-specific recommendations; complete tool discovery remains in the main directory."""
RELATED={
 'unix-timestamp-converter':['guides/unix-timestamp-seconds-vs-milliseconds','json-unescape','base64url-decode'],
 'px-to-rem':['rem-to-px','guides/rem-vs-em','hex-to-rgb','hex-to-rgba'],
 'rem-to-px':['px-to-rem','guides/rem-vs-em','hex-to-rgb','hex-to-rgba'],
 'base64':['base64url-decode','hex-to-text','base64-to-image','guides/fix-invalid-base64'],
 'base64url-decode':['base64','hex-to-text','guides/fix-invalid-base64','unix-timestamp-converter'],
 'base64-to-image':['image-to-base64','guides/save-base64-image','guides/fix-invalid-base64','base64'],
 'image-to-base64':['base64-to-image','guides/save-base64-image','base64'],
 'hex-to-rgb':['hex-to-rgba','px-to-rem','rem-to-px'],
 'hex-to-rgba':['hex-to-rgb','px-to-rem','rem-to-px'],
 'json-unescape':['guides/json-double-encoding','json-minify','json-compare','csv-to-json'],
 'json-minify':['json-compare','json-unescape','yaml-to-json','csv-to-json'],
 'json-compare':['json-minify','json-unescape','yaml-to-json','csv-to-json'],
 'hex-to-text':['base64url-decode','base64','guides/fix-invalid-base64'],
 'yaml-to-json':['guides/yaml-vs-json','csv-to-json','json-minify'],
 'csv-to-json':['yaml-to-json','json-minify','json-compare'],
}
TOOL_GROUPS=[
 ('Data formats',['yaml-to-json','csv-to-json','json-minify','json-compare','json-unescape'],'Work with configuration, records and escaped strings.'),
 ('Encoding & images',['base64','base64url-decode','hex-to-text','base64-to-image','image-to-base64'],'Inspect text, bytes and image representations.'),
 ('CSS & layout',['px-to-rem','rem-to-px','hex-to-rgb','hex-to-rgba'],'Choose units, color channels and opacity for your page.'),
 ('Time & dates',['unix-timestamp-converter'],'Check timestamp units and convert explicit dates.'),
]
