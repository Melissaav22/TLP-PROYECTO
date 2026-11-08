# Estado de implementación de la fase 1

Rama: `feat/fase-uno`, creada desde `ExtensionEspañol` el 6 de noviembre de 2026.

## Alcance

Parser LL(1) MiniC y español en presente; concordancia, modificadores y subordinación. Incluye validación de gramáticas, raíz española independiente, diagnósticos con posición, recuperación, árboles profundos y SVG. SVO y pasado se incorporan en `feat/fase-dos`, que deriva de esta rama.

## Evidencia de esta rama

- 39 fixtures originales y 11 pruebas de contratos/experimentos.
- Demo de 13 frases y 39 análisis reales con parser, NLTK CESS-ESP y spaCy.
- Datos y trazas bajo datos/fase1.json y resultados/fase1.
- Ambigüedad contrastada mediante dos derivaciones de una CFG auxiliar.
- Informe de seis páginas y presentación de diez diapositivas con notas.
- Dependencias bloqueadas y huellas de código, gramática y datos.

Las etiquetas son una referencia inicial. Dos frases con objeto nominal tienen esperado_cfg=false porque esa construcción todavía queda fuera de esta gramática. En fase 2 cambia la gramática y se actualizan esas etiquetas.

## Documentación histórica y pendientes

AUDITORIA_TECNICA.md, AUDITORIA_ESTADO_ACTUAL.md, auditoria/ y PLAN_IMPLEMENTACION.md conservan el diagnóstico y plan previos, que cubren ambas fases. Su contenido no representa el alcance implementado de esta rama.

Faltan revisión de etiquetas y argumento formal por el grupo, completar autoría, ensayar 15–20 minutos y confirmar entrega/defensa. Los límites del subconjunto no demuestran por sí mismos que el español quede fuera de todas las CFG.

Los informes y diapositivas se revisan mediante render. El generador PPTX presenta en este host un código de salida 1 al cerrar, incluso después de emitir recibos satisfactorios; se verifican por separado paquete, geometría, fuentes, reimportación y renders. Sigue pendiente corregir esa anomalía de automatización. No se ha validado mediante una sesión nativa de PowerPoint.
