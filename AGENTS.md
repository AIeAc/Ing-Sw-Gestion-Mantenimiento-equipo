# Proyecto 3: Sistema Inteligente para Gestión de Mantenimiento Predictivo de Equipos

## Contexto del proyecto

Este repositorio corresponde al desarrollo de un sistema inteligente para gestionar el mantenimiento predictivo de equipos.

El proyecto se desarrollará con Scrum en **5 sprints de 2 semanas cada uno**.

La visión completa del sistema contempla:

- Administración de usuarios y roles.
- Inventario de equipos.
- Clasificación y búsqueda de equipos.
- Historial de mantenimiento.
- Registro o importación de variables operativas.
- Predicción de posibles fallas.
- Alertas de mantenimiento.
- Calendario de actividades.
- Indicadores y reportes.

## Sprint actual

El sprint actual es el **Sprint 4**. Los Sprints 1, 2 y 3 ya entregaron las
bases técnicas, usuarios, roles, inventario, mantenimiento, variables
operativas, mediciones, alertas por rango e indicadores básicos.

El alcance autorizado para el Sprint 4 se limita a:

- Recopilación y limpieza de los datos disponibles para entrenamiento.
- Selección documentada de variables y del resultado que se predecirá.
- División reproducible de los datos en entrenamiento y prueba.
- Entrenamiento local de uno o dos algoritmos predictivos sencillos.
- Evaluación y selección del modelo con mejores resultados.
- Integración del modelo local con la aplicación existente.
- Visualización del nivel estimado de riesgo por equipo.
- Pruebas del entrenamiento, integración y presentación de riesgos.

## Restricción obligatoria de alcance

No agregar, adelantar ni implementar funciones que estén fuera del alcance del sprint actual, aunque formen parte de la visión completa del sistema.

En particular, durante el Sprint 4 no se deben implementar programación
automática de mantenimientos, alertas predictivas automáticas, sensores o
integraciones IoT, reentrenamiento automático ni reportes ejecutivos.

Antes de realizar cualquier cambio, comprobar que pertenece directamente al
alcance del Sprint 4. Si una solicitud resulta ambigua o parece corresponder a
un sprint posterior, detenerse y pedir confirmación antes de implementarla.

No crear infraestructura, modelos, endpoints, pantallas ni lógica especulativa para funcionalidades futuras. Solo se permiten decisiones técnicas y componentes estrictamente necesarios para entregar el alcance actual.

## Estado del desarrollo

Los Sprints 1, 2 y 3 están implementados. El trabajo actual debe extenderlos
de forma incremental, conservando los datos existentes y sin adelantar
módulos de sprints posteriores.
