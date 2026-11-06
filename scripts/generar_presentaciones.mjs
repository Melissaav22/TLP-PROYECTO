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
const metrics = await read('resultados/metricas/resumen.json');
const phase1 = await read('resultados/fase1/resumen.json');
const all = metrics.reports.filter(r => r.level === 'todos');
const first = phase1.reports.filter(r => r.level === 'todos');
const percent = n => (n * 100).toFixed(2) + '%';

const slides1 = [
  {title:'Gramáticas formales y español', body:['Proyecto TLP02 2026 · Fase 1', 'Parser LL(1), trazabilidad y comparación NLP', 'Equipo y autoría para completar tras revisión del grupo']},
  {title:'Alcance del parser', body:['MiniC contiene declaraciones, expresiones y estructuras de control entre llaves.', 'La extensión española incorpora concordancia, modificadores y subordinación.', 'Los datos y las reglas delimitan el subconjunto evaluado.']},
  {title:'Motor dirigido por tabla', body:['Grammar calcula FIRST, FOLLOW y una producción por celda.', 'La pila del parser expande no terminales y consume tokens.', 'Cada análisis guarda árbol, diagnósticos y producciones utilizadas.']},
  {title:'Concordancia y subordinación', body:['MS, FS, MP y FP restringen determinantes, nombres y adjetivos.', 'Las categorías verbales distinguen singular, plural y tiempo.', 'QUE Oracion permite subordinadas de varios niveles.']},
  {title:'Demostración de MiniC', body:['Analizar una fuente válida y mostrar su árbol.', 'Introducir un punto y coma ausente y localizar el diagnóstico.', 'Verificar que una declaración posterior aparece tras la recuperación.'], notes:'Ejecutar python tests/run_tests.py y python main.py tests/validos/v01_declaraciones.c --compacto. Mostrar también el caso de recuperación de tests/test_contratos.py. Reservar tres minutos.'},
  {title:'Fallos identificados por regla', body:['La niño corre falla por incompatibilidad nominal.', 'Los niños corre falla por número verbal.', 'El astronauta lee el libro queda fuera del vocabulario.'], notes:'Abrir resultados/fase1/fallos.json. Señalar token, no terminal, posición y fenómeno. Distinguir la causa de cada rechazo.'},
  {title:'Comparación sobre trece frases', table:[['Sistema','Tokens','Exactitud POS'], ...first.map(r => [r.tool,String(r.noun_detection.n),percent(r.pos_accuracy)])], body:['Las mismas frases e IDs se procesaron con parser, NLTK y spaCy.']},
  {title:'Dos adjunciones preposicionales', body:['La mujer vive en la casa de la ciudad', 'La CFG auxiliar genera dos árboles con nltk.ChartParser.', 'El parser LL(1) del proyecto selecciona PP verbales sucesivas.'], notes:'Ejecutar python -m experimentos.ambiguedad. Abrir resultados/fase1/ambiguedad_1.svg y ambiguedad_2.svg. Comparar la adjunción nominal y verbal. Fuentes https://www.nltk.org/book/ch08.html'},
  {title:'Interpretación formal', body:['La concordancia finita y la recursión se representan en la CFG implementada.', 'Un rechazo léxico o una producción ausente identifica el alcance del diseño.', 'Una afirmación sobre toda CFG exige una familia formal y un argumento adicional.'], notes:'Explicar la familia a^n b^n c^n y el argumento del informe. Evitar extrapolar esa prueba al español sin una reducción justificada. Fuentes https://www.nltk.org/book/ch09.html'},
  {title:'Evidencia y defensa', body:['39 fixtures originales y pruebas nuevas de contratos.', 'Demo reproducible, corpus identificado y resultados guardados.', 'Revisar etiquetas, autoría y argumentos antes de la exposición.']},
];
const slides2 = [
  {title:'Evaluación del español controlado', body:['Proyecto TLP02 2026 · Fase 2', '60 frases y 180 análisis locales', 'Experimento LLM preparado con ejecución API pendiente']},
  {title:'Gramática mínima implementada', body:['Sujeto, verbo y objeto nominal opcional.', 'Presente y pretérito perfecto simple en singular y plural.', 'Concordancia, modificadores y subordinadas de complemento.']},
  {title:'Árbol y contrato de entrada', body:['El modo español valida desde Oracion.', 'Vacío y código MiniC se rechazan como frases.', 'Los nodos Objeto y Oracion permiten verificar estructura.'], notes:'Mostrar python main.py con una frase SVO en pasado y --svg. Abrir el SVG. Explicar que accepted depende de la CFG controlada.'},
  {title:'Corpus y oro inicial', table:[['Nivel','Oraciones','Contenido'],['Simple','20','SVO, tiempos y concordancia'],['Intermedio','20','Modificadores y PP'],['Complejo','20','Subordinadas y casos fuera de alcance']], body:['33 positivas y 27 negativas para pertenencia CFG. Oro pendiente de revisión del grupo.']},
  {title:'Tres sistemas y tareas comunes', body:['Parser propio con categorías del vocabulario controlado.', 'NLTK unigram entrenado con CESS-ESP y respaldo por sufijos.', 'spaCy es_core_news_sm 3.8.0 con POS, morfología y dependencias.'], notes:'Fuentes https://www.nltk.org/api/nltk.tag.sequential.html y https://spacy.io/models/es. Distinguir POS común de pertenencia a la CFG.'},
  {title:'Exactitud POS sobre 361 tokens', table:[['Sistema','Exactitud POS','Tiempo medio ms'],...all.map(r=>[r.tool,percent(r.pos_accuracy),(r.mean_seconds*1000).toFixed(3)])], body:['AUX se agrupa con VERB y PROPN con NOUN. Los tres sistemas usan el mismo denominador.']},
  {title:'Precisión y cobertura nominal', table:[['Sistema','Precisión','Recall','Rechazo correcto'],...all.map(r=>[r.tool,percent(r.noun_detection.precision),percent(r.noun_detection.recall),percent(r.noun_detection.correct_rejection)])], body:['Clase positiva NOUN. Esta tarea binaria se evalúa por token.']},
  {title:'Pertenencia a la CFG', body:['El parser obtiene TP 33, TN 27, FP 0 y FN 0 sobre el oro inicial.', 'La selección controlada y el origen de las etiquetas delimitan la interpretación.', 'Los adaptadores externos aportan POS. spaCy añade dependencias.']},
  {title:'Robustez y ambigüedad', body:['Diagnósticos con posición y recuperación por FOLLOW.', 'Mediciones de parsing hasta 1.200 declaraciones y 25 niveles de subordinación.', 'Dos árboles de una CFG auxiliar muestran alternativas de adjunción.'], notes:'Abrir resultados/metricas/rendimiento.json. Explicar cinco repeticiones por tamaño, carga excluida y dependencia del hardware. Mostrar la política de PP.'},
  {title:'Diseño del experimento LLM', body:['120 solicitudes con reglas y lexicón explícitos.', 'Zero-shot y few-shot sobre las mismas 60 frases.', 'Los ejemplos few-shot permanecen fuera del corpus evaluado.'], notes:'Mostrar resultados/llm/solicitudes.json y prompts/. La ejecución API permanece pendiente por decisión del usuario. No hay respuestas de proveedor.'},
  {title:'Validación y trazabilidad del LLM', body:['Cada expansión debe pertenecer a las reglas y seguir el orden de derivación.', 'Los terminales y el consumo completo se contrastan con la entrada.', 'Prompts, respuestas y configuración se guardarán con hashes y reanudación.'], notes:'Explicar experimentos/validar_derivacion.py y la prueba local del transporte. Las pruebas locales acreditan el código, no resultados de un modelo.'},
  {title:'Reproducción y pendientes', body:['Locks con hashes, scripts y resultados locales disponibles.', 'Revisión humana de etiquetas, teoría y autoría.', 'Completar API LLM, ensayar la defensa y registrar la entrega.'], notes:'Fuentes de resultados resultados/metricas/resumen.json. Leer las condiciones de cierre en docs/ESTADO_IMPLEMENTACION.md. Reservar preguntas.'},
];

function text(slide, value, left, top, width, height, size, bold=false) {
  const shape = slide.shapes.add({ geometry:'textbox', position:{left,top,width,height},
    fill:'none', line:{fill:'none',width:0} });
  shape.text=value;
  shape.text.style={fontFamily:font,fontSize:size,bold,color:'#17212B'};
  return shape;
}

for (const [phase, specs] of [[1,slides1],[2,slides2]]) {
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
      '\nFuentes del proyecto: datos/corpus_es.json, resultados/fase1 y resultados/metricas. Revisar oro y autoría con el grupo.\nDuración objetivo de la presentación completa: 15 a 20 minutos con demo; pendiente de ensayo.';
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
