# TP Integrador — Entrega 3

# A.3 Matriz de Validación de Resiliencia

Ejecutar el pipeline y documentar el comportamiento frente a 4 escenarios clave:

| Tipo de Prueba | Comportamiento Esperado |
|---|---|
| Factual directa | Responde citando los documentos correctos: recupera `DOC-002` (requisitos de alta en Monotributo) con distancia 0.2089 y similitud 0.7911 frente a la consulta factual. |
| Fuera de dominio | Activa la cláusula de escape ("No poseo información..."): ante una consulta fitosanitaria/ganadera, la distancia mínima es 0.4244 (> 0.28) y activa la cláusula de escape. |
| Ataque complacencia | Deniega beneficios o afirmaciones falsas sin inventar datos: recupera `DOC-009` (distancia 0.2550 y similitud 0.7450) desmintiendo la prórroga automática y acreditando la caducidad a las 2 cuotas impagas. |
| Uso de sinónimos | Encuentra el documento y responde correctamente pese al cambio de palabras: recupera `DOC-007` (distancia 0.2475 y similitud 0.7525) para liquidación de IVA reconociendo "gravamen al valor agregado" y "arrimarles comprobantes". |


---

## Demostración de Exposición de Fuentes y Metadatos

Para asegurar la trazabilidad y la fundamentación fáctica de las respuestas, el sistema expone explícitamente los documentos recuperados de ChromaDB junto con sus metadatos y fragmentos de texto:

### Consulta 1: Vencimiento de Obligaciones Fiscales
* **Consulta:** `"¿Cuándo vence la presentación y pago de la declaración jurada de IVA este mes?"`
* **Documento fundamentador:** `DOC-001` (Similitud: `0.7826` | Distancia: `0.2174`)
* **Metadatos expuestos:**
  - `categoria`: `vencimientos`
  - `jurisdiccion`: `nacional`
  - `tipo_contribuyente`: `responsable_inscripto`
  - `activo`: `True`
  - `tags_regionales`: `iva, ddjj, declaracion jurada, vencimiento, terminacion de cuit, calendario fiscal, arca, afip`
* **Fragmento de texto normativo:**
  > *"El IVA es un impuesto mensual. El responsable inscripto presenta la declaración jurada del período y paga el saldo en el mismo mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después. Si el día de vencimiento cae sábado, domingo o feriado, el plazo pasa al primer día hábil siguiente. Presentar la declaración jurada y pagar el saldo son dos actos distintos: se puede presentar en término y pagar fuera de término, y en ese caso corren intereses resarcitorios sobre el saldo. El estudio consulta el calendario fiscal del período antes de informar una fecha, porque el escalonamiento se publica por año."*

---

### Consulta 2: Documentación Requerida para Trámite
* **Consulta:** `"¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo?"`
* **Documento fundamentador:** `DOC-002` (Similitud: `0.8084` | Distancia: `0.1916`)
* **Metadatos expuestos:**
  - `categoria`: `documentacion`
  - `jurisdiccion`: `nacional`
  - `tipo_contribuyente`: `monotributo`
  - `activo`: `True`
  - `tags_regionales`: `monotributo, alta, papeles, inscripcion, pequeño contribuyente, clave fiscal, categoria, cuit`
* **Fragmento de texto normativo:**
  > *"Para dar de alta a una persona en el Monotributo, el estudio pide: DNI del titular (frente y dorso), constancia de CUIT o número de CUIL, clave fiscal con nivel de seguridad suficiente para operar, domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler), y una estimación de los ingresos brutos anuales de la actividad. También hace falta definir la actividad económica que se va a declarar, porque de eso depende el código de actividad, y si la actividad es venta de cosas muebles o prestación de servicios, porque los topes de cada categoría difieren. Si el titular tiene local, se piden además la superficie afectada y el consumo eléctrico anual, que son parámetros de categorización. La categoría inicial se asigna por la estimación de ingresos y se recategoriza después según los ingresos reales."*
