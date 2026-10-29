# Sprint 4: modelo predictivo local

## Objetivo y resultado previsto

El modelo estima la posibilidad de que un equipo requiera un mantenimiento
correctivo durante los próximos **30 días**. El resultado es un índice entre 0
y 100 que se comunica mediante cuatro estados:

- **Riesgo bajo:** menos de 40 %.
- **Riesgo medio:** desde 40 % y menos de 70 %.
- **Riesgo alto:** 70 % o más.
- **Información insuficiente:** menos de cinco mediciones en los últimos 30 días.

El índice es una estimación académica entrenada localmente con cortes del
historial de PostgreSQL y escenarios simulados complementarios. No representa
una certificación industrial ni activa mantenimientos o alertas.

## Variables seleccionadas

La aplicación resume los datos existentes de cada equipo en:

1. Cantidad de mediciones durante los últimos 30 días.
2. Proporción de mediciones fuera de rango.
3. Desviación promedio respecto del rango permitido.
4. Desviación máxima respecto del rango permitido.
5. Tendencia diaria normalizada de las mediciones.
6. Mantenimientos correctivos durante los últimos 180 días.
7. Días desde el último mantenimiento completado.
8. Días desde la última medición.
9. Estado actual fuera de servicio.

Los valores ausentes, no finitos o extremos se sustituyen o acotan antes de la
inferencia. Los equipos dados de baja no se evalúan.

## Entrenamiento y selección

El conjunto combina dos fuentes:

- **Cortes históricos semanales:** para cada fecha se usan solamente las
  mediciones de los 30 días anteriores. La etiqueta es positiva cuando existe
  un correctivo no cancelado durante los 30 días posteriores al corte.
- **Escenarios simulados reproducibles:** complementan los pocos eventos de
  falla disponibles y conservan relaciones explícitas entre anomalías,
  historial correctivo y deterioro.

La mezcla completa se divide en 80 % para entrenamiento y 20 % para prueba
mediante una separación estratificada. La cantidad y procedencia de los casos
quedan guardadas junto al modelo para permitir su revisión.

Se comparan:

- Regresión logística con estandarización y balance de clases.
- Random Forest con balance de clases y profundidad limitada.

La selección prioriza F1, después recall y finalmente precision. El modelo
seleccionado debe alcanzar como mínimo:

- F1 de 0.70.
- Recall de 0.70.

La exactitud, precision, recall, F1 y matriz de confusión quedan guardadas como
metadatos junto con el modelo.

## Prioridad y costos

La pantalla convierte la probabilidad en una recomendación operativa. El
puntaje de prioridad pondera **80 % del riesgo estimado** y **20 % del impacto
relativo del costo correctivo**. Además, un riesgo alto siempre requiere
atención inmediata y uno medio, como mínimo, prioridad alta.

El costo esperado se obtiene en este orden:

1. Promedio de correctivos completados del mismo equipo.
2. Promedio de correctivos completados de su categoría.
3. Promedio general de correctivos completados.

La interfaz muestra la fuente y cantidad de registros usados. La exposición
económica se calcula como `probabilidad × costo correctivo estimado`; sirve para
comparar equipos, no como cotización ni autorización presupuestal.

## Riesgos y controles

- **Datos limitados:** los escenarios simulados complementan, pero no se
  presentan como mediciones reales; la interfaz muestra ambas cantidades.
- **Cortes temporales:** cada caso histórico excluye mediciones posteriores a
  la fecha evaluada y busca correctivos únicamente en el horizonte futuro.
- **Fuga de información:** los datos de prueba se separan antes del ajuste de
  los modelos.
- **Pocos datos por equipo:** no se inventa un porcentaje; se muestra
  "Información insuficiente".
- **Modelo incompatible:** la aplicación valida su versión y variables antes
  de utilizarlo.
- **Ejecución local:** el archivo se genera en `instance/` y no se envían datos
  a servicios externos.
- **Decisiones automáticas:** el resultado es informativo y no modifica
  mantenimientos, mediciones, costos o alertas.

## Operación

Instalar dependencias y entrenar una vez por computadora:

```bash
pip install -r requirements.txt
flask --app app entrenar-modelo-riesgo
```

El comando obtiene los cortes históricos de la base actual, genera 1,600
escenarios complementarios, entrena los dos algoritmos, compara sus resultados
y guarda el modelo aceptado en `instance/modelo_riesgo.joblib`.
