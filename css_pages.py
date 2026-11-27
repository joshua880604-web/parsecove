"""Shared static UI for the two CSS length converter entry points."""
import html
import json

COMMON_PX = [4, 5, 8, 10, 12, 14, 16, 20, 24, 32, 40, 48, 64, 72, 80, 96, 100, 120, 144, 150]
COMMON_REM = [0.25, 0.5, 0.75, 0.875, 1, 1.125, 1.25, 1.5, 1.75, 2, 2.5, 3, 3.5, 4, 5, 6, 8, 10, 12, 16]


def css_workbench(direction, icon, copy):
    rem = direction == 'rem'
    source = 'REM values' if rem else 'Pixels'
    sample, result = ('1.5', '24px') if rem else ('24', '1.5rem')
    number, unit = ('24', 'px') if rem else ('1.5', 'rem')
    equation = '1.5rem × 16 = 24px' if rem else '24px ÷ 16 = 1.5rem'
    modes = ''.join(
        f'<button type="button" data-mode="{value}" aria-pressed="{str(value == direction).lower()}"'
        f' class="{"selected" if value == direction else ""}">{label}</button>'
        for value, label in [('px', 'PX to REM'), ('rem', 'REM to PX')]
    )
    quick = [1, 1.5, 1.25, 0.75, 0.875] if rem else [14, 24, 72, 80, 150]
    quick_buttons = ''.join(
        f'<button class="button small" type="button" data-{direction}-quick="{value}">{value}{"rem" if rem else "px"}</button>'
        for value in quick
    )
    return f'''<section class="workbench">
<div class="bench-toolbar"><div class="segmented" id="px-modes" role="group" aria-label="Conversion mode">{modes}</div><span class="quiet">Instant conversion</span></div>
<div class="bench-body"><div class="input-panel">
<div class="field-row"><div><label for="px-base">Root font size (px)</label><input id="px-base" type="number" min="0.01" max="10000" step="any" value="16"></div>
<div><label for="px-precision">Decimal places</label><select id="px-precision"><option>2</option><option selected>4</option><option>6</option><option>8</option><option>0</option></select></div></div>
<label id="px-input-label" for="px-input">{source}</label><textarea id="px-input" class="mono large-text" rows="5" spellcheck="false" aria-describedby="px-input-hint">{sample}</textarea>
<p class="hint" id="px-input-hint">Enter numbers without units. Separate a list with spaces, commas or new lines. Up to 1,000 values.</p>
<div class="actions"><button class="button" id="px-sample">Try a spacing scale</button><button class="button ghost" id="px-clear">Clear</button></div>
<div class="quick-values"><span>Try a {'REM' if rem else 'PX'} value:</span>{quick_buttons}</div>
<p class="error" id="px-error" role="alert" hidden></p></div>
<div class="result-panel"><div class="result-head"><span class="mono-label">YOUR RESULT</span>{copy('px-output')}</div>
<div class="result-big px-value" id="px-value">{number}<span>{unit}</span></div><p class="result-sub" id="px-equation">{equation}</p>
<label for="px-output">Copyable values</label><textarea class="mono" id="px-output" rows="4" readonly>{result}</textarea>
<div class="actions"><button class="button small" id="px-download" disabled>Download CSV</button></div>
<div class="type-preview"><span class="mono-label">TYPE PREVIEW · FIRST VALUE</span><span id="px-preview">Aa — in proportion.</span><small>Preview is limited to 8–72px for readability.</small></div>
<div class="panel-note">{icon('shield')} Calculated on your device</div></div></div></section>'''


def css_reference_table(direction):
    rem = direction == 'rem'
    values = COMMON_REM if rem else COMMON_PX
    half = len(values) // 2
    source, target = ('REM', 'Pixels') if rem else ('Pixels', 'REM')
    rows = ''
    for index in range(half):
        cells = ''
        for number in (values[index], values[index + half]):
            converted = number * 16 if rem else number / 16
            cells += f'<td>{number:g}{"rem" if rem else "px"}</td><td>{converted:g}{"px" if rem else "rem"}</td>'
        rows += f'<tr>{cells}</tr>'
    encoded = html.escape(json.dumps(values), quote=True)
    return f'''<section class="reference-table"><div class="section-heading"><h2>{'Common REM values in pixels' if rem else 'Everyday spacing, translated.'}</h2><span id="px-table-base">At a 16px root size</span></div>
<div class="table-wrap"><table><caption class="sr-only">{source} to {target}; results use the root font size shown above.</caption><thead><tr><th>{source}</th><th>{target}</th><th>{source}</th><th>{target}</th></tr></thead>
<tbody id="px-table" data-source-unit="{direction}" data-values="{encoded}">{rows}</tbody></table></div></section>'''
