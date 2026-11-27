import {hexColor} from './conversion-core.js';
export function rgbaFromHex(value,opacity='1'){
 const color=hexColor(value);let alpha=color.alpha;
 if(!color.hasAlpha){const raw=String(opacity).trim();alpha=raw===''?1:Number(raw);if(raw!==''&&!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(raw)||!Number.isFinite(alpha)||alpha<0||alpha>1)throw Error('Opacity must be a decimal from 0 to 1. Leave it empty for an opaque color.');}
 const alphaByte=Math.round(alpha*255),hex=color.hex.slice(0,7)+alphaByte.toString(16).padStart(2,'0').toUpperCase();
 const displayedAlpha=color.hasAlpha?Number(alpha.toFixed(6)):alpha;
 return {...color,alpha,alphaByte,hex,rgba:`rgba(${color.r}, ${color.g}, ${color.b}, ${displayedAlpha})`,embeddedAlpha:color.hasAlpha,hexAlpha:alphaByte/255,quantized:Math.abs(alpha-alphaByte/255)>1e-12};
}
