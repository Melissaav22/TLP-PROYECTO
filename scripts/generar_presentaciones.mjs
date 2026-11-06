import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const deps = path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies');
process.env.RUNTIME_NODE_MODULES = path.join(deps, 'node/node_modules');
const skill = process.env.CODEX_PRESENTATIONS_SKILL;
if (!skill) throw new Error('Configura CODEX_PRESENTATIONS_SKILL con la habilidad de presentaciones instalada');
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(deps, 'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')));
const { finalizePresentation, resolvePresentationFont } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')));
const font = resolvePresentationFont({ fontFamily: 'Arial' });
const read = async p => JSON.parse(await fs.readFile(path.join(root, p), 'utf8'));
const phase1 = await read('resultados/fase1/resumen.json');
const first = phase1.reports.filter(r => r.level === 'todos');
const percent = n => (n * 100).toFixed(2) + '%';

const slides1 = [
  {title:'Gramáticas formales y español', body:['Proyecto TLP02 2026 · Fase 1', 'Parser LL(1), trazabilidad y comparación NLP', 'Equipo y autoría para completar tras revisión del grupo']},
  {title:'Alcance del parser', body:['MiniC contiene declaraciones, expresiones y estructuras de control entre llaves.', 'La extensión española incorpora concordancia, modificadores y subordinación.', 'Los datos y las reglas delimitan el subconjunto evaluado.']},
  {title:'Motor dirigido por tabla', body:['Grammar calcula FIRST, FOLLOW y una producción por celda.', 'La pila del parser expande no terminales y consume tokens.', 'Cada análisis guarda árbol, diagnósticos y producciones utilizadas.']},
  {title:'Concordancia y subordinación', body:['MS, FS, MP y FP restringen determinantes, nombres y adjetivos.', 'Las categorías verbales distinguen singular y plural en presente.', 'QUE Oracion permite subordinadas de varios niveles.']},
  {title:'Demostración de MiniC', body:['Analizar una fuente válida y mostrar su árbol.', 'Introducir un punto y coma ausente y localizar el diagnóstico.', 'Verificar que una declaración posterior aparece tras la recuperación.'], notes:'Ejecutar python tests/run_tests.py y python main.py tests/validos/v01_declaraciones.c --compacto. Mostrar también el caso de recuperación de tests/test_contratos.py. Reservar tres minutos.'},
  {title:'Fallos identificados por regla', body:['La niño corre falla por incompatibilidad nominal.', 'Los niños corre falla por número verbal.', 'El astronauta lee el libro queda fuera del vocabulario.'], notes:'Abrir resultados/fase1/fallos.json. Señalar token, no terminal, posición y fenómeno. Distinguir la causa de cada rechazo.'},
  {title:'Comparación sobre trece frases', table:[['Sistema','Tokens','Exactitud POS'], ...first.map(r => [r.tool,String(r.noun_detection.n),percent(r.pos_accuracy)])], body:['Las mismas frases e IDs se procesaron con parser, NLTK y spaCy.']},
  {title:'Dos adjunciones preposicionales', body:['La mujer vive en la casa de la ciudad', 'La CFG auxiliar genera dos árboles con nltk.ChartParser.', 'El parser LL(1) del proyecto selecciona PP verbales sucesivas.'], notes:'Ejecutar python -m experimentos.ambiguedad. Abrir resultados/fase1/ambiguedad_1.svg y ambiguedad_2.svg. Comparar la adjunción nominal y verbal. Fuentes https://www.nltk.org/book/ch08.html'},
  {title:'Interpretación formal', body:['La concordancia finita y la recursión se representan en la CFG implementada.', 'Un rechazo léxico o una producción ausente identifica el alcance del diseño.', 'Una afirmación sobre toda CFG exige una familia formal y un argumento adicional.'], notes:'Explicar la familia a^n b^n c^n y el argumento del informe. Evitar extrapolar esa prueba al español sin una reducción justificada. Fuentes https://www.nltk.org/book/ch09.html'},
  {title:'Evidencia y defensa', body:['39 fixtures originales y pruebas nuevas de contratos.', 'Demo reproducible, corpus identificado y resultados guardados.', 'Revisar etiquetas, autoría y argumentos antes de la exposición.']},
];
function text(slide, value, left, top, width, height, size, bold=false) {
  const shape = slide.shapes.add({ geometry:'textbox', position:{left,top,width,height},
    fill:'none', line:{fill:'none',width:0} });
  shape.text=value;
  shape.text.style={fontFamily:font,fontSize:size,bold,color:'#17212B'};
  return shape;
}

for (const [phase, specs] of [[1,slides1]]) {
  const deck = Presentation.create({slideSize:{width:1280,height:720}});
  const tableOwners=[];
  for (const [index,spec] of specs.entries()) {
    const slide = deck.slides.add();
    slide.background.fill='#FFFFFF';
    text(slide,spec.title,72,60,1136,index===0?140:100,index===0?60:44,true);
    if (spec.table) {
      tableOwners.push(index+1);
      const table=slide.tables.add({rows:spec.table.length,columns:spec.table[0].length,
        left:72,top:190,width:1136,height:Math.min(325,spec.table.length*62),values:spec.table});
      table.borders.assign({fill:'#D9D9D9',width:1,style:'solid'});
      for(let row=0;row<spec.table.length;row++) {
        for(let col=0;col<spec.table[0].length;col++) {
          const cell=table.getCell(row,col);
          cell.fill=row===0?'#DCE6F0':row%2?'#FFFFFF':'#F4F6F8';
          cell.text.style={fontFamily:font,fontSize:25,bold:row===0,color:'#17212B'};
        }
      }
      text(slide,spec.body.join('\n'),72,540,1136,115,26);
    } else {
      spec.body.forEach((paragraph,i)=>text(slide,paragraph,72,220+i*125,1136,110,29));
    }
    text(slide,String(index+1),1140,668,70,40,16);
    slide.speakerNotes.text=(spec.notes??'Explicar el contenido con las producciones y resultados del repositorio. Tiempo orientativo de 90 segundos.')+
      '\nFuentes del proyecto: datos/fase1.json y resultados/fase1. Revisar oro y autoría con el grupo.\nDuración objetivo de la presentación completa: 15 a 20 minutos con demo; pendiente de ensayo.';
  }
  const build=path.join(root,'.build/presentaciones','fase'+phase);
  await fs.mkdir(build,{recursive:true});
  await fs.mkdir(path.join(root,'docs'),{recursive:true});
  for(const [index,slide] of deck.slides.items.entries()) {
    const png=await deck.export({slide,format:'png',scale:1});
    await fs.writeFile(path.join(build,'slide-'+String(index+1).padStart(2,'0')+'.png'),new Uint8Array(await png.arrayBuffer()));
  }
  const candidate=path.join(build,'candidate.pptx');
  await (await PresentationFile.exportPptx(deck)).save(candidate);
  const result=await finalizePresentation({
    workspaceDir:root,candidatePath:candidate,finalPath:path.join(root,'docs','presentacion_fase'+phase+'.pptx'),
    pythonExecutable:path.join(deps,'python/python.exe'),
    integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',
                ...tableOwners.flatMap(number=>['--require-native-table-slide',String(number)])],
    requiredNativeTableOwnerSlides:tableOwners,
    explicitTotalSlideCount:specs.length,
    fontPolicy:{basis:'design',families:[font]},
    verifyArtifactToolImport:true,
    receiptPath:path.join(build,'validation-'+Date.now()+'.json'),
  });
  console.log('Fase',phase,'validada:',result.finalPath,'diapositivas:',specs.length);
}
