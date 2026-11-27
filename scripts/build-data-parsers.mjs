import {build} from 'esbuild';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const vendors=[
 ['yaml',"export {parseDocument,stringify} from 'yaml';",'LICENSE'],
 ['papaparse',"import Papa from 'papaparse'; export const parse=Papa.parse,unparse=Papa.unparse;",'LICENSE'],
 ['jsonc-parser',"export {parseTree,printParseErrorCode} from 'jsonc-parser';",'LICENSE.md'],
];
const records=[];
await mkdir('dist/assets/vendor',{recursive:true});
for(const [name,contents,license] of vendors){
 const pkg=JSON.parse(await readFile(`node_modules/${name}/package.json`,'utf8'));
 const file=`dist/assets/vendor/${name}.js`;
 await build({stdin:{contents,resolveDir:process.cwd(),sourcefile:`${name}-entry.js`},outfile:file,bundle:true,minify:true,format:'esm',platform:'browser',target:'es2022',legalComments:'inline',banner:{js:`/* ${name} ${pkg.version}; see ${name}.LICENSE.txt */`}});
 await writeFile(`dist/assets/vendor/${name}.LICENSE.txt`,await readFile(`node_modules/${name}/${license}`));
 records.push({name,version:pkg.version,license:pkg.license,source:`https://www.npmjs.com/package/${name}/v/${pkg.version}`,file,sha256:createHash('sha256').update(await readFile(file)).digest('hex')});
}
await writeFile('dist/assets/vendor/manifest.json',JSON.stringify(records,null,2)+'\n');
console.log(records.map(r=>`${r.name} ${r.version}: ${r.file}`).join('\n'));
