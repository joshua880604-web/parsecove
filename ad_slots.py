"""Build-time placement hooks only. This module never loads an ad network."""
import json
from pathlib import Path

PLACEMENTS = {'home_after_tools', 'tool_primary', 'tool_secondary'}

def load_config(path):
    config = json.loads(Path(path).read_text())
    if set(config) != {'slots_enabled', 'placements'}:
        raise ValueError('Ad configuration needs slots_enabled and placements only.')
    if type(config['slots_enabled']) is not bool:
        raise ValueError('slots_enabled must be a boolean.')
    if not isinstance(config['placements'], dict) or set(config['placements']) != PLACEMENTS:
        raise ValueError('Configure all three known ad placements.')
    if any(type(value) is not bool for value in config['placements'].values()):
        raise ValueError('Each placement switch must be a boolean.')
    return config

def render_slot(name, config, preview=False):
    if name not in PLACEMENTS:
        raise ValueError('Unknown ad placement.')
    if not config['placements'][name] or not (config['slots_enabled'] or preview):
        return ''
    modifier = name.replace('_', '-')
    placeholder = '<span class="ad-slot__preview">Layout preview · no ad request</span>' if preview else ''
    return (
        f'<aside class="ad-slot ad-slot--{modifier}" data-ad-slot="{name}" aria-label="Advertisement">'
        '<div class="ad-slot__label">Advertisement</div>'
        f'<div class="ad-slot__surface" data-ad-mount="{name}">{placeholder}</div></aside>'
    )
