# Configuración final predeterminada del avanzado

Se ejecutó la consulta compuesta por la CLI sin --selected: máximo resuelto 4.
La respuesta y los IDs de fuentes coinciden exactamente con la ejecución
validada anterior que suministraba --selected 4. Se conserva toda la cobertura
validada: comprobantes IVA, presentación y pago, aportes/contribuciones,
altas/bajas antes de liquidar, intereses y bloqueo del certificado por pago tardío.

Configuración: chunking 500/100; hasta ocho candidatos; sin corte duro previo
por distancia en reranking; score mínimo 0.5; hasta cuatro seleccionados de
forma predeterminada, configurable entre 1 y 4, con posibilidad de seleccionar cero.
Básico y chunks conservan máximo predeterminado 3 y su umbral 0.28.
No se cambiaron reglas de recuperación, juicio o generación.

## Pregunta

Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?

## Respuesta real completa

> Para liquidar el IVA, el estudio necesita que el cliente proporcione: facturas de venta emitidas, facturas de compra recibidas, notas de crédito y débito (emitidas y recibidas), comprobantes de retenciones y percepciones sufridas, y tickets de controlador fiscal si utiliza ese medio [DOC-007].
>
> Respecto a la declaración y pago del IVA:
> *   Es un impuesto mensual donde se presenta la declaración jurada y se paga el saldo en el mes siguiente al que se liquida [DOC-001].
> *   La fecha exacta depende de la terminación del CUIT, escalonándose de menor a mayor [DOC-001].
> *   Si el vencimiento cae en sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente [DOC-001].
> *   La presentación y el pago son actos distintos [DOC-001].
>
> Sobre las cargas sociales:
> *   El empleador debe presentar mensualmente una declaración jurada que informa la nómina del período y liquida aportes y contribuciones [DOC-008].
> *   Los aportes son retenidos del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador [DOC-008].
> *   El vencimiento de la presentación y el pago ocurre en la segunda semana del mes siguiente al período liquidado, escalonado por terminación de CUIT [DOC-008].
> *   Es obligatorio tener la nómina actualizada, registrando altas y bajas de empleados antes de liquidar [DOC-008].
> *   El pago fuera de término genera intereses y bloquea la obtención del certificado de libre deuda previsional [DOC-008].

## Fuentes en orden

1. DOC-008::chunk-000-989bdb5081187467 — padre DOC-008, score 1.0.
2. DOC-001::chunk-000-5d1a5023e0007962 — padre DOC-001, score 1.0.
3. DOC-007::chunk-000-bfbf474549da33fb — padre DOC-007, score 0.9.
4. DOC-008::chunk-001-92e73e8b1d8ef4e4 — padre DOC-008, score 0.7.

## Validación y pendiente

Once pruebas locales aprobadas. No se repitieron los otros cuatro casos con API,
porque solo se cambió la resolución del valor predeterminado y se añadió una
prueba de defaults por variante. Se preservan las evidencias anteriores.
LangSmith sigue pendiente: falta configurar credenciales y verificar una traza
real con recuperación, reranking, generación, tiempos, tokens y candidatos frente
a seleccionados. No se declara B.4 completo ni se generó evidencia ficticia.
No se ejecutaron RAGAS ni nuevos ajustes de recuperación. Sin merge, push ni PR.
