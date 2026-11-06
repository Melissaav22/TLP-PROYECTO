"""Genera informes PDF y fuentes Markdown desde la evidencia experimental."""
from html import escape
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def pct(value):
    return 'N/A' if value is None else f'{value * 100:.2f}%'


def make_pdf(phase, pages):
    font_dir = Path('C:/Windows/Fonts')
    regular, bold = 'Helvetica', 'Helvetica-Bold'
    if (font_dir / 'arial.ttf').exists() and (font_dir / 'arialbd.ttf').exists():
        pdfmetrics.registerFont(TTFont('ReportArial', str(font_dir / 'arial.ttf')))
        pdfmetrics.registerFont(TTFont('ReportArialBold', str(font_dir / 'arialbd.ttf')))
        regular, bold = 'ReportArial', 'ReportArialBold'
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Body', fontName=regular, fontSize=10.8,
                              leading=15.5, spaceAfter=11, textColor=colors.black))
    styles.add(ParagraphStyle(name='SmallBody', parent=styles['Body'], fontSize=8.4, leading=11.5))
    for name in ['Title', 'Heading1', 'Heading2']:
        styles[name].textColor = colors.black
        styles[name].fontName = bold
    styles['Title'].fontSize = 23
    styles['Title'].leading = 28
    styles['Heading1'].fontSize = 17
    styles['Heading1'].leading = 22
    styles['Heading1'].spaceAfter = 15
    story, md = [], []
    for index, page in enumerate(pages):
        if index:
            story.append(PageBreak())
        story.append(Paragraph(escape(page['title']), styles['Title' if index == 0 else 'Heading1']))
        md.append('# ' + page['title'])
        for block in page['blocks']:
            if isinstance(block, str):
                story.append(Paragraph(escape(block), styles['Body']))
                md.append(block)
            elif 'heading' in block:
                story.append(Paragraph(escape(block['heading']), styles['Heading2']))
                md.append('## ' + block['heading'])
            elif 'code' in block:
                story.append(Preformatted(block['code'], ParagraphStyle(
                    name='Code', fontName='Courier', fontSize=8.3, leading=11, spaceAfter=12)))
                md.append('```text\n' + block['code'] + '\n```')
            elif 'table' in block:
                values = block['table']
                widths = block.get('widths', [487 / len(values[0])] * len(values[0]))
                cells = [[Paragraph(escape(str(cell)), styles['SmallBody']) for cell in row] for row in values]
                table = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), .5, colors.HexColor('#D9D9D9')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DCE6F0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F6F8FA')]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ]))
                story.extend([table, Spacer(1, 14)])
                md.extend([' | '.join(map(str, row)) for row in values])
            elif 'image' in block:
                story.append(Image(str(ROOT / block['image']), width=455, height=250, kind='proportional'))
                story.append(Spacer(1, 10))
                md.append('![' + block['image'] + '](' + block['image'] + ')')
        md.append('\n---\n')
    def footer(canvas, doc):
        canvas.setFont(regular, 8)
        canvas.setFillColor(colors.HexColor('#4B5563'))
        canvas.drawString(54, 29, f'TLP02 2026   Fase {phase}   Revisión del grupo pendiente')
        canvas.drawRightString(A4[0] - 54, 29, str(doc.page))
    OUT.mkdir(exist_ok=True)
    doc = SimpleDocTemplate(str(OUT / f'informe_fase{phase}.pdf'), pagesize=A4,
                            leftMargin=54, rightMargin=54, topMargin=48, bottomMargin=48)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    (OUT / f'informe_fase{phase}.md').write_text('\n\n'.join(md).rstrip() + '\n', encoding='utf-8')


def main():
    f1 = load('resultados/fase1/resumen.json')
    f2 = load('resultados/metricas/resumen.json')
    tools = load('resultados/nlp/comparacion.json')['tools']
    perf = load('resultados/metricas/rendimiento.json')['measurements']
    phase1_rows = [r for r in f1['reports'] if r['level'] == 'todos']
    phase2_rows = [r for r in f2['reports'] if r['level'] == 'todos']
    pos_table = lambda rows: [['Sistema', 'Tokens POS', 'Exactitud POS', 'Tiempo ms']] + [
        [r['tool'], r['noun_detection']['n'], pct(r['pos_accuracy']), f'{r["mean_seconds"] * 1000:.3f}'] for r in rows]
    f1_pages = [
      dict(title='Gramáticas formales y análisis del español', blocks=[
        'Informe técnico de la Fase 1 del Proyecto TLP02 2026. Versión del 6 de noviembre de 2026 preparada para revisión de etiquetas, autoría y defensa por el grupo.',
        'El trabajo implementa un parser LL(1) dirigido por tabla para fragmentos MiniC y extiende la misma gramática a un español controlado. El motor produce árboles concretos y diagnósticos con posición. La comparación ejecutada utiliza el parser propio, un etiquetador estadístico NLTK y un pipeline español de spaCy sobre las mismas trece oraciones de demostración.',
        'Los casos demuestran concordancia local, subordinación recursiva y modificadores. También permiten rastrear rechazos hasta tokens o no terminales. Una CFG auxiliar genera dos análisis de una frase preposicional, mientras el subconjunto LL(1) adopta una adjunción determinada. Las conclusiones diferencian una decisión del diseño y una afirmación sobre la capacidad expresiva de todas las CFG.',
        dict(heading='Método y evidencia'),
        'Se conservaron los veinte fixtures MiniC y los diecinueve del español. Las nuevas pruebas verifican posiciones, recuperación, FIRST/FOLLOW, estructuras de árboles y ejecución CLI. Los resultados de demo y sus trazas están en resultados/fase1. Los hashes de código, gramática y datos permiten identificar la revisión ejecutada aunque existan cambios locales sobre el commit base.',
        dict(table=[['Componente', 'Implementación'], ['Motor', 'Pila predictiva y tabla calculada desde producciones'], ['Léxico', 'PLY y diccionario español con rasgos'], ['Árbol', 'nltk.Tree, corchetes iterativos y SVG'], ['Comparación', 'NLTK CESS-ESP y spaCy es_core_news_sm']], widths=[110,377]),
        'La anotación es una referencia inicial preparada antes de las predicciones. El grupo debe revisarla y completar la autoría antes de entregar el informe. Los resultados corresponden al conjunto controlado y las tareas descritas en estas páginas.',
      ]),
      dict(title='Motor formal y gramática de MiniC', blocks=[
        'La clase Grammar carga alternativas, valida símbolos, comprueba productividad y calcula FIRST mediante punto fijo. FOLLOW incorpora FIRST del sufijo y propaga FOLLOW del padre cuando el sufijo es anulable. La tabla selecciona una producción por no terminal y token de anticipación. Una colisión genera GrammarError con la celda implicada.',
        'El parser mantiene símbolos y nodos pendientes en una pila explícita. Una coincidencia terminal consume un token y conserva su lexema como hoja. Una expansión no terminal construye los hijos de la producción. Las alternativas vacías producen la hoja eps. Este procedimiento separa las reglas declaradas del mecanismo que las ejecuta.',
        dict(code='Decl -> INT ID DeclTail SEMI\nDeclTail -> ASSIGN Expr | eps\nExpr -> Term ExprP\nExprP -> PLUS Term ExprP | MINUS Term ExprP | eps\nTerm -> Factor TermP\nTermP -> TIMES Factor TermP | DIVIDE Factor TermP | eps'),
        'Los niveles Expr, Term y Factor establecen la precedencia aritmética. La forma del árbol conserva las continuaciones derechas introducidas al eliminar recursión izquierda. Un evaluador futuro necesitaría acumular resta y división de izquierda a derecha. En esta entrega se analiza sintaxis y se construye el árbol.',
        'Ante un terminal ausente se registra la posición esperada. Ante un no terminal sin entrada de tabla se descartan tokens hasta FOLLOW o fin de archivo. Los diagnósticos incluyen etapa, código, línea, columna y desplazamiento; su presentación respeta el orden del fuente. Las producciones utilizadas se registran para examinar el recorrido.',
        'MiniC representa fragmentos de sentencias con declaraciones int y estructuras entre llaves. Los literales admitidos son decimales ASCII sin ceros iniciales, conservando la escritura original. La comprobación de declaración previa, tipos y comportamiento de ejecución corresponde a análisis semántico y queda declarada fuera del alcance.',
      ]),
      dict(title='Extensión controlada al español', blocks=[
        'La rama española utiliza Oracion como entrada efectiva. Esta selección impide que una declaración MiniC o la cadena vacía se interpreten como una oración. El lexer consulta un vocabulario finito y asocia las palabras a categorías que codifican género y número. La consulta normaliza NFC y mayúsculas sin modificar las posiciones del texto original.',
        dict(table=[['Fenómeno', 'Codificación de la gramática'], ['Concordancia nominal', 'SN_MS, SN_FS, SN_MP y SN_FP combinan determinante, nombre y adjetivo compatibles'], ['Sujeto y verbo', 'VerboSG y VerboPL restringen tercera persona'], ['Subordinación', 'QUE Oracion permite inclusión recursiva'], ['Modificadores', 'Adjetivos pospuestos, ADV y PREP SN'], ['Tiempos y objeto', 'Presente, pretérito perfecto simple y SN objeto opcional']], widths=[125,362]),
        'La duplicación de categorías por un número finito de rasgos permite expresar la concordancia elegida dentro de una CFG. El crecimiento de reglas es un costo de mantenimiento observable. La subordinación también usa recursión de producciones y admite más de un nivel. La prueba de dos niveles comprueba tres nodos Oracion en el árbol.',
        'Las frases preposicionales sucesivas se adjuntan al sintagma verbal. El fixture denominado históricamente pp_anidada contiene dos PP hermanas. Se conserva como regresión y se añade una aserción estructural para hacer explícita esa interpretación. La gramática auxiliar de ambigüedad permite además una adjunción nominal.',
        'El vocabulario excluye pronombres, coordinación, relativas e imperfecto. El punto final también está fuera de esta versión. Todos los verbos plenos comparten los complementos permitidos y la gramática no comprueba valencia semántica. Esas decisiones se registran para interpretar las etiquetas del corpus y las diferencias con un analizador general.',
      ]),
      dict(title='Fallos trazables y jerarquía de Chomsky', blocks=[
        'El registro de cada caso conserva texto, etiqueta esperada, fenómeno, tokens, producciones y diagnósticos. El primer punto de fallo identifica un símbolo inesperado o una palabra ausente del vocabulario. Esta trazabilidad permite explicar por qué se acepta o rechaza una entrada concreta y revisar la regla responsable.',
        dict(table=[['Caso', 'Resultado y clase de limitación'], ['La niño corre', 'Rechazo por incompatibilidad DET_FS y SUST_MS'], ['Los niños corre', 'Rechazo de verbo singular tras sujeto plural'], ['El astronauta lee el libro', 'Rechazo léxico por nombre fuera del vocabulario'], ['El niño y la niña corren', 'Rechazo por coordinación fuera de la CFG definida']], widths=[190,297]),
        'Una CFG de tipo 2 expande un único no terminal en cada producción. Su reconocimiento se relaciona con autómatas de pila. Los patrones regulares forman el nivel tipo 3, y las gramáticas sensibles al contexto forman el tipo 1. La clasificación se refiere a familias de cadenas y al mecanismo necesario para reconocerlas, con las convenciones usuales sobre la cadena vacía.',
        'La familia abstracta a^n b^n c^n ofrece un contraste formal. En un argumento de bombeo con longitud p, la ventana de hasta p símbolos dentro de a^p b^p c^p no puede abarcar simultáneamente un a y un c. Bombear modifica como máximo dos bloques o rompe el orden, dejando sin mantener la igualdad de los tres conteos. Esa familia queda fuera de las CFG.',
        'El contraste anterior ilustra una prueba sobre una familia formal. Para trasladarla a una construcción del español se necesitaría definir esa familia lingüística y justificar una reducción o un argumento equivalente. Los ejemplos finitos de esta entrega acreditan límites del subconjunto implementado. La concordancia finita y la subordinación observadas sí están codificadas mediante CFG [1, 2].',
      ]),
      dict(title='Comparación ejecutada y ambigüedad', blocks=[
        'La demo ejecutó trece frases idénticas en los tres sistemas, con identificadores compartidos y sin errores de ejecución. NLTK entrena unigramas con respaldo por sufijos sobre CESS-ESP. spaCy utiliza es_core_news_sm 3.8.0. La tarea común utiliza etiquetas POS gruesas, agrupando AUX con VERB y PROPN con NOUN.',
        dict(table=pos_table(phase1_rows), widths=[95,105,130,157]),
        'El parser coincidió con las trece etiquetas de pertenencia al subconjunto de la demo. Los adaptadores externos aportan POS y, en spaCy, dependencias y morfología. accepted permanece sin valor en esos adaptadores porque su tarea no emite una decisión de pertenencia a esta CFG. El informe identifica por separado procesamiento, etiquetado y aceptación.',
        'La oración La mujer vive en la casa de la ciudad se procesó además mediante nltk.ChartParser con una CFG auxiliar que permite NP con PP y VP con PP. La ejecución produjo exactamente dos derivaciones. En una, de la ciudad modifica el nombre casa. En la otra, aparece como otra PP del predicado. Ambas derivaciones y sus SVG quedaron guardados.',
        'La existencia de esos dos árboles muestra ambigüedad estructural dentro de una CFG [2]. La gramática LL(1) del proyecto elige PP verbales sucesivas. Las dos decisiones tienen consecuencias en el árbol aunque acepten la misma cadena. La demo permite examinar esta diferencia con resultados obtenidos por ejecución.',
      ]),
      dict(title='Conclusiones y reproducción de la Fase 1', blocks=[
        'El motor formal y su extensión española producen resultados trazables y conservan los ejemplos originales. Las categorías morfológicas permiten verificar concordancia local, y la producción recursiva permite subordinación. Los rechazos por coordinación, palabras nuevas o puntuación identifican el alcance actual de la implementación.',
        'La comparación proporciona evidencia de diferencias de etiquetado y de interpretación estructural. La CFG auxiliar representa dos adjunciones, mientras el parser predictivo sigue una política explícita. El análisis formal distingue esas decisiones de diseño de una demostración general sobre el lenguaje español. El grupo debe revisar esta interpretación y defender los argumentos con las producciones y árboles disponibles.',
        dict(heading='Comandos de demostración'),
        dict(code='python tests/run_tests.py\npython tests/run_tests.py --es\npython -m experimentos.registro_fallos\npython -m experimentos.demo_fase1\npython -m experimentos.ambiguedad'),
        'Las instalaciones y modelos se describen en README.md y los archivos requirements con hashes. Los datos de demo están en datos/fase1.json. Los resultados y las dos derivaciones auxiliares están en resultados/fase1. Las pruebas de contrato y de experimentos usan unittest y se verificaron en Python 3.10 y 3.12.',
        dict(heading='Referencias y revisión'),
        '[1] NLTK Book, capítulo 9, Building Feature Based Grammars. https://www.nltk.org/book/ch09.html',
        '[2] NLTK Book, capítulo 8, Analyzing Sentence Structure. https://www.nltk.org/book/ch08.html',
        '[3] spaCy, pipelines entrenados para español. https://spacy.io/models/es',
        '[4] Especificación docente TLP02-2026, Fase 1, archivo suministrado por el solicitante. Autoría, etiquetas y exposición requieren revisión final del grupo.',
      ]),
    ]
    f2_pages = [
      dict(title='Parser de español y evaluación experimental', blocks=[
        'Informe de la Fase 2 del Proyecto TLP02 2026. Versión del 6 de noviembre de 2026 para revisión del grupo. La sección de ejecución LLM permanece pendiente por decisión del usuario.',
        'La implementación incorpora SVO, presente y pretérito perfecto simple a la gramática controlada. El corpus contiene sesenta oraciones distribuidas en tres niveles. Se ejecutaron el parser propio, un etiquetador estadístico NLTK y spaCy sobre todas las entradas, obteniendo ciento ochenta análisis sin errores de ejecución.',
        'El parser coincide con las treinta y tres etiquetas positivas y veintisiete negativas iniciales de pertenencia CFG. La exactitud POS en los 361 tokens de referencia fue de ' + ', '.join(r['tool'] + ' ' + pct(r['pos_accuracy']) for r in phase2_rows) + '. Estas cifras corresponden a una anotación preparada para revisión y al vocabulario y fenómenos de este conjunto.',
        dict(table=[['Dimensión', 'Evidencia guardada'], ['Corpus', '60 frases, 20 por nivel, ejemplos few-shot separados'], ['Comparación', '180 resultados, versiones y tiempos'], ['Métricas', 'Matriz de confusión CFG y POS común'], ['LLM', '120 solicitudes preparadas, cero respuestas de proveedor']], widths=[115,372]),
        'Las tareas se evalúan con contratos separados. El parser decide pertenencia al subconjunto. NLTK y spaCy aportan etiquetas y dependencias; su éxito técnico no define aceptación bajo la CFG. La comparación común utiliza POS grueso y detección de NOUN, con denominadores idénticos. Los errores de ejecución se contabilizan aparte.',
        'El paquete conserva datos, código, configuración y resultados para regenerar tablas y figuras. El cierre académico requiere revisión de etiquetas, autoría y exposición, además de completar el experimento API cuando el responsable lo autorice.',
      ]),
      dict(title='Diseño de la gramática y contratos', blocks=[
        'La entrada española es Oracion y la raíz efectiva determina FOLLOW y la tabla predictiva. Esto evita aceptar vacío o fragmentos MiniC como frases. La clase Grammar valida producciones, epsilon, símbolos y productividad. FIRST y FOLLOW se obtienen por punto fijo y los conflictos de tabla se reportan con la celda correspondiente.',
        dict(code='Oracion -> OracionSG | OracionPL\nSV_MS -> VerboSG Cpl_MS | CopulaSG PredCpl_MS\nVerboSG -> VERB_3S | VERB_PAST_3S\nCpl_MS -> QUE Oracion | Objeto ModsS\nObjeto -> SN | eps\nPP -> PREP SN'),
        'Las variantes femeninas y plurales completan la concordancia nominal y verbal. Las formas de pasado tienen tipos de token propios, por lo que el tiempo permanece identificable en los resultados. El objeto se representa como un nodo Objeto que contiene SN cuando aparece. Se verifican positivos y negativos en ambos tiempos.',
        'El análisis es sintáctico. Los verbos plenos comparten las opciones de complemento y el modelo no verifica plausibilidad ni valencia semántica. Las PP se adjuntan al sintagma verbal. La coordinación, relativas, pronombres, imperfecto y puntuación final están fuera del subconjunto elegido.',
        'La API parse conserva árbol y lista de mensajes. parse_detailed añade diagnósticos con posición, tokens y traza de producciones. La serialización en corchetes usa una pila y tolera profundidad grande. La salida SVG permite inspeccionar las relaciones; su límite de nodos se informa mediante un error controlado.',
        dict(table=[['Caso', 'Evidencia estructural'], ['El niño lee el libro', 'Objeto contiene un SN después del verbo'], ['Los niños leyeron los libros', 'Token VERB_PAST_3P y sujeto plural'], ['La casa fue blanca', 'Cópula de pasado y atributo femenino singular']], widths=[210,277]),
      ]),
      dict(title='Corpus y anotación de referencia', blocks=[
        'Las sesenta oraciones se prepararon antes de las predicciones de los adaptadores. Cada entrada guarda ID, texto, nivel, fenómeno, esperado_cfg, corrección general, tokens y POS de referencia. La versión de gramática y el hash del corpus identifican el conjunto evaluado. El estado de revisión humana permanece pendiente del grupo.',
        dict(table=[['Nivel', 'Cantidad', 'Fenómenos'], ['Simple', '20', 'Sujeto, verbo, SVO, concordancia y pasado'], ['Intermedio', '20', 'Adjetivos, adverbios, PP y variaciones'], ['Complejo', '20', 'Subordinadas, errores distantes y construcciones fuera del subconjunto']], widths=[85,70,332]),
        'Hay treinta y tres etiquetas positivas y veintisiete negativas para pertenencia CFG. Una frase correcta del español puede tener etiqueta negativa si utiliza un pronombre, una relativa, un tiempo o una palabra fuera del vocabulario. Por ejemplo, El astronauta lee el libro es correcta en español general y queda fuera del lexicón controlado.',
        'La anotación POS usa categorías amplias y una tabla léxica explícita, independiente de las predicciones de NLTK y spaCy. Este procedimiento favorece al lexer propio en las palabras que comparte con esa tabla; se declara como característica del conjunto y justifica ampliar y revisar el oro antes de generalizar las cifras.',
        'Los tres ejemplos few-shot tienen IDs y textos distintos del conjunto evaluado. El validador comprueba tamaño mínimo, niveles, duplicados, etiquetas y versión de gramática. Los cambios manuales deben conservarse en Git. Volver a ejecutar el constructor de datos restablece deliberadamente la anotación inicial y exige revisar los resultados asociados.',
      ]),
      dict(title='Herramientas y metodología de comparación', blocks=[
        f'NLTK {tools["nltk"]["version"]} entrena un UnigramTagger sobre {tools["nltk"]["training_sentences"]} oraciones y {tools["nltk"]["training_tokens"]} tokens de CESS-ESP. Utiliza un AffixTagger de sufijos de tres caracteres y NOUN como respaldo final. El archivo descargado queda identificado por SHA-256. El corpus experimental no se usa para entrenar el etiquetador.',
        f'spaCy {tools["spacy"]["version"]} carga es_core_news_sm {tools["spacy"]["model_version"]}, que aporta POS, dependencias, lemas y morfología. Se guarda la salida original necesaria para revisar diferencias. Los modelos y su ámbito de entrenamiento difieren del vocabulario reducido del proyecto [1, 2].',
        'Los tres sistemas procesan los mismos IDs. Las etiquetas se normalizan agrupando AUX con VERB y PROPN con NOUN. La detección nominal es una tarea binaria por token, donde NOUN es la clase positiva. Sobre ella se calculan precisión, recall y tasa de rechazo correcto. También se calcula exactitud POS global.',
        'Para pertenencia CFG se calculan TP, FP, TN y FN sobre frases. Esa tarea se aplica al parser y se aplicará al LLM cuando existan respuestas. Los adaptadores externos mantienen accepted sin valor. La salida diferencia una decisión lingüística, un desalineamiento de tokens y un fallo técnico.',
        'Los tiempos por oración usan perf_counter con modelos ya cargados y entrenamiento excluido. La inicialización se registra por separado. Son mediciones locales de una ejecución; la carga del sistema y el hardware afectan su valor. Los datos incluyen plataforma, versiones, hashes y parámetros para describir el contexto.',
        dict(table=[['Sistema', 'Precisión NOUN', 'Recall NOUN', 'Rechazo NOUN']] + [
            [r['tool'], pct(r['noun_detection']['precision']), pct(r['noun_detection']['recall']),
             pct(r['noun_detection']['correct_rejection'])] for r in phase2_rows], widths=[110,125,125,127]),
      ]),
      dict(title='Resultados cuantitativos obtenidos', blocks=[
        'La evaluación POS utiliza 361 tokens de referencia en todos los sistemas. El parser conserva una X para símbolos fuera de su léxico en esta tarea, incluida la puntuación no admitida, para mantener un denominador común. Los errores de tokenización se registran y el conjunto actual no presenta desalineamientos.',
        dict(table=pos_table(phase2_rows), widths=[95,105,130,157]),
        dict(image='resultados/metricas/exactitud_pos.png'),
        'En pertenencia CFG el parser obtuvo TP=33, TN=27, FP=0 y FN=0 en la anotación inicial. Precisión, recall y rechazo correcto son 1,00 en ese conjunto. La selección controlada y la revisión humana pendiente limitan la interpretación externa de este resultado.',
        'La comparación de POS incluye una regla léxica controlada, un baseline estadístico entrenado y un pipeline general. Las diferencias deben interpretarse junto con el tipo de tarea y el origen de las etiquetas. La tabla completa por nivel y la clasificación de errores se conservan en resultados/metricas.',
      ]),
      dict(title='Errores y comportamiento experimental', blocks=[
        'El resumen clasifica falsos positivos, falsos negativos, errores POS, desalineamientos y errores de ejecución. La pertenencia CFG no produjo FP/FN sobre la referencia inicial. Los errores POS permiten revisar palabras desconocidas y diferencias de clase. La anotación debe revisarse antes de concluir qué decisión es lingüísticamente preferible.',
        dict(table=[['Lenguaje', 'Tamaño', 'Tiempo medio ms']] + [[r['language'], r['size'], f'{r["mean_seconds"] * 1000:.3f}'] for r in perf], widths=[170,110,207]),
        'Se midieron cinco repeticiones por tamaño con gramática cargada. MiniC se evaluó hasta 1.200 declaraciones y español hasta 25 niveles de subordinación. Todos esos análisis se aceptaron. La desviación temporal de cada grupo está guardada en rendimiento.json. Las medidas describen parsing y no incluyen dibujar árboles.',
        'En robustez se verifican caracteres ilegales, palabras nuevas, formatos numéricos, concordancia y selección de lenguaje. La ambigüedad preposicional se examina con dos derivaciones de una CFG auxiliar sobre la misma frase. El parser propio sigue su política de PP verbales. El número de categorías crece al codificar rasgos finitos, un costo de mantenimiento visible al extender el subconjunto.',
      ]),
      dict(title='Experimento LLM preparado', blocks=[
        'El usuario indicó preparar la integración y mantener pendiente la ejecución API. Se generaron ciento veinte solicitudes, sesenta zero-shot y sesenta few-shot. El directorio LLM conserva el estado prepared y cero respuestas reales. La comparación de precisión entre variantes sigue pendiente.',
        'Cada prompt proporciona el símbolo Oracion, las producciones españolas y el lexicón. La respuesta solicitada es un objeto JSON con accepted y una lista ordenada de expansiones izquierdas. Few-shot añade tres ejemplos de un archivo separado; los ejemplos positivos contienen derivaciones completas verificadas por el parser.',
        'El validador comprueba que cada no terminal se expanda en el orden correspondiente, que la alternativa exista y que los terminales coincidan con la entrada. Incluye epsilon y comprueba consumo completo. Un rechazo se contrasta con el reconocimiento formal. Se conserva el razonamiento de validación junto con el acierto o fallo de decisión.',
        'El cliente usa un endpoint HTTPS Chat Completions compatible, con modelo, clave y configuración definidos en el entorno. Registra el prompt, la respuesta original, tokens y costo estimado si el responsable suministra tarifas. La huella de solicitud permite reanudar llamadas completadas. Los secretos quedan excluidos de los archivos.',
        'La prueba automatizada del transporte ejecuta un servidor HTTP local y comprueba reanudación y ausencia de claves en logs. Es evidencia de integración de software. Los resultados del LLM requieren llamadas reales al proveedor y se incorporarán mediante experimentos.resumir_llm cuando se ejecute el experimento.',
        dict(code='python -m experimentos.llm\n# Tras configurar proveedor, modelo y clave local\npython -m experimentos.llm --execute --max-new-calls 2\npython -m experimentos.resumir_llm'),
      ]),
      dict(title='Conclusiones y condiciones de cierre', blocks=[
        'El desarrollo incorpora los mínimos sintácticos SVO y dos tiempos, además de concordancia, modificadores y subordinación. El conjunto experimental tiene sesenta frases y permite reproducir ciento ochenta análisis con datos por sistema y nivel. Las métricas separan la pertenencia al subconjunto de las tareas POS comparables.',
        'Las cifras obtenidas respaldan el comportamiento del modelo controlado sobre la anotación inicial. El grupo debe revisar oro, adjunción, valencia y casos fuera del vocabulario antes de ampliar las conclusiones. La comparación LLM y su efecto zero-shot/few-shot permanecen pendientes y no se les asignan cifras.',
        'El cierre requiere completar esa ejecución cuando el responsable lo decida, regenerar sus métricas, actualizar la discusión de costo y robustez, registrar integrantes y ensayar la presentación. El repositorio contiene instrucciones, locks con hashes y resultados reales locales. Se verificaron pruebas del núcleo en Python 3.10 y 3.12 y un entorno experimental limpio de Python 3.12.',
        dict(heading='Reproducción y referencias'),
        dict(code='python -m experimentos.validar_corpus\npython -m experimentos.comparar_nlp\npython -m experimentos.metricas\npython -m experimentos.graficas\npython -m experimentos.rendimiento'),
        '[1] NLTK, etiquetadores secuenciales y lectores de corpus. https://www.nltk.org/api/nltk.tag.sequential.html',
        '[2] spaCy, modelos españoles. https://spacy.io/models/es',
        '[3] NLTK Book, capítulos 8 y 9, estructura, ambigüedad y rasgos. https://www.nltk.org/book/',
        '[4] OpenAI, contrato Chat Completions. https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create',
        '[5] Especificación docente TLP02-2026, Fase 2, archivo suministrado por el solicitante. El grupo revisará autoría, etiquetas y defensa antes de entrega.',
      ]),
    ]
    make_pdf(1, f1_pages)
    make_pdf(2, f2_pages)
    from pypdf import PdfReader
    for phase, expected in [(1, 6), (2, 8)]:
        path = OUT / f'informe_fase{phase}.pdf'
        count = len(PdfReader(str(path)).pages)
        print(path.name, count, 'paginas')
        if count != expected:
            raise ValueError(f'Revisar paginacion de fase {phase}: {count}')


if __name__ == '__main__':
    main()
