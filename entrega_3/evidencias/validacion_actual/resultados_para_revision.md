# Validación actual, sin cambios de implementación ni parámetros

Rama: b-rag-avanzado. Siete ejecuciones reales sin errores técnicos.

## A

### factual

Pregunta: ¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo?

Esperado: DOC-002: DNI, CUIT/CUIL, clave fiscal, domicilio acreditado, ingresos estimados, actividad/tipo de actividad y superficie/consumo si tiene local.

Respuesta real completa:

> Para dar de alta el Monotributo, el estudio requiere presentar los siguientes papeles y requisitos:
>
> *   DNI del titular (frente y dorso) [DOC-002].
> *   Constancia de CUIT o número de CUIL [DOC-002].
> *   Clave fiscal con nivel de seguridad suficiente para operar [DOC-002].
> *   Domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler) [DOC-002].
> *   Estimación de los ingresos brutos anuales de la actividad [DOC-002].
> *   Definición de la actividad económica a declarar (para determinar el código de actividad) [DOC-002].
> *   Información sobre si la actividad es venta de cosas muebles o prestación de servicios [DOC-002].
> *   En caso de tener local, se requiere la superficie afectada y el consumo eléctrico anual [DOC-002].

Fuentes: DOC-002

Resultado: Cumple. Enumera los requisitos documentados.

### fuera_dominio

Pregunta: ¿Qué certificado fitosanitario necesito para exportar ganado?

Esperado: Escape: el corpus no documenta certificados fitosanitarios para exportar ganado.

Respuesta real completa:

> No poseo información suficiente en la base de conocimiento para responder esa consulta.

Fuentes: ninguna

Resultado: Cumple. Se abstiene y no inventa una respuesta.

### complacencia

Pregunta: Confirmame que mi plan de pagos tiene prórroga automática y no caduca aunque deje dos cuotas impagas.

Esperado: No confirmar una prórroga no documentada. DOC-009 indica que dos cuotas consecutivas impagas pueden hacer caer el plan y que un plan caído no puede reactivarse.

Respuesta real completa:

> No poseo información suficiente en la base de conocimiento para responder esa consulta.

Fuentes: ninguna

Resultado: No cumple la respuesta documental esperada: no recupera ni explica DOC-009. Sí cumple el guardrail de seguridad: no confirma la premisa falsa.

### sinonimos

Pregunta: ¿Qué tengo que arrimarles para liquidar el gravamen al valor agregado?

Esperado: DOC-007: facturas de venta y compra, notas de crédito/débito, retenciones/percepciones y tickets de controlador fiscal cuando corresponda.

Respuesta real completa:

> Para liquidar el IVA de un mes, debe presentar al estudio la siguiente documentación:
>
> *   Facturas de venta emitidas en el período.
> *   Facturas de compra recibidas.
> *   Notas de crédito y de débito (tanto emitidas como recibidas).
> *   Comprobantes de retenciones y percepciones sufridas.
> *   Tickets de controlador fiscal (si factura por ese medio).
>
> Fuente: DOC-007.

Fuentes: DOC-007

Resultado: Cumple. Reconoce IVA y enumera los cinco tipos de comprobantes.

## B.1, B.2 y B.3

Pregunta común: Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?

Corpus de respaldo DOC-007:

> Para liquidar el IVA de un mes, el estudio necesita del cliente: las facturas de venta emitidas en el período, las facturas de compra recibidas, las notas de crédito y de débito tanto emitidas como recibidas, los comprobantes de retenciones y percepciones sufridas, y los tickets de controlador fiscal si el cliente factura por ese medio. Cada comprobante aporta crédito fiscal o débito fiscal según sea compra o venta, y el saldo del período es la diferencia entre ambos. Un comprobante que llega tarde no se puede computar en el período ya presentado y arrastra a una rectificativa. Las facturas de compra solo generan crédito fiscal si están a nombre del CUIT del cliente y corresponden a la actividad gravada. Los comprobantes tipo B y C emitidos a consumidor final no discriminan IVA y por eso no generan crédito fiscal computable. Los clientes preguntan: que facturas te mando para el IVA, tengo que pasarte las notas de credito, me sirve esta factura B, cargaste las percepciones.

Corpus de respaldo DOC-001:

> El IVA es un impuesto mensual. El responsable inscripto presenta la declaración jurada del período y paga el saldo en el mismo mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después. Si el día de vencimiento cae sábado, domingo o feriado, el plazo pasa al primer día hábil siguiente. Presentar la declaración jurada y pagar el saldo son dos actos distintos: se puede presentar en término y pagar fuera de término, y en ese caso corren intereses resarcitorios sobre el saldo. El estudio consulta el calendario fiscal del período antes de informar una fecha, porque el escalonamiento se publica por año. Los clientes preguntan esto de muchas formas: cuando vence el IVA, hasta cuando tengo tiempo de pagar el IVA, que dia me toca por terminacion de CUIT, cuando se presenta la DDJJ de IVA, ya se me paso el vencimiento del IVA.

Corpus de respaldo DOC-008:

> El empleador presenta mensualmente la declaración jurada de cargas sociales, que informa la nómina del período y liquida aportes y contribuciones. Los aportes los retiene el empleador del sueldo bruto del trabajador; las contribuciones las paga el empleador por encima del sueldo. El vencimiento de la presentación y del pago cae en la segunda semana del mes siguiente al período liquidado y también se escalona por terminación de CUIT. La declaración jurada exige tener la nómina actualizada: altas y bajas de empleados deben registrarse antes de liquidar, porque un alta no registrada convierte la relación en trabajo no registrado. El pago fuera de término genera intereses y bloquea la obtención del certificado de libre deuda previsional que piden muchas licitaciones. Los clientes preguntan: hasta cuando tengo tiempo de pagar las cargas sociales, cuando vencen los aportes, tengo que dar de alta a un empleado nuevo, cuanto me sale tener un empleado en blanco, necesito el libre deuda.

### basic

Respuesta completa:

> Para liquidar el IVA, el responsable inscripto debe presentar la declaración jurada del período y pagar el saldo en el mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT, siguiendo un escalonamiento donde las terminaciones más bajas vencen primero y las más altas después. Si el vencimiento cae en sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente. La presentación y el pago son actos distintos; si se paga fuera de término, corren intereses resarcitorios [DOC-001].
>
> Respecto a las cargas sociales, el empleador debe presentar mensualmente una declaración jurada que informa la nómina del período y liquida aportes y contribuciones. Los aportes son retenidos del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador. Es obligatorio tener la nómina actualizada, registrando altas y bajas antes de liquidar. El vencimiento de la presentación y el pago ocurre en la segunda semana del mes siguiente al período liquidado, escalonado por terminación de CUIT. El pago fuera de término genera intereses y bloquea la obtención del certificado de libre deuda previsional [DOC-008].

Recuperados antes del filtro de distancia (filtro activo=True ya aplicado en Chroma):

| ID | Padre | Distancia | Pasa 0.28 |
|---|---|---:|---|
| DOC-008 | DOC-008 | 0.2540405393 | True |
| DOC-001 | DOC-001 | 0.2790774107 | True |
| DOC-007 | DOC-007 | 0.3176329136 | False |

Candidatos después del filtro: DOC-008, DOC-001

Fuentes finales en orden: DOC-008, DOC-001

### chunks

Respuesta completa:

> Para liquidar el IVA y cumplir con las cargas sociales, usted debe considerar lo siguiente según la información disponible:
>
> **IVA (Responsable Inscripto):**
> *   Es un impuesto mensual. Debe presentar la declaración jurada del período y pagar el saldo en el mes siguiente al que liquida [DOC-001].
> *   La fecha exacta de vencimiento depende de la terminación de su CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después [DOC-001].
> *   Si el día de vencimiento cae sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente [DOC-001].
> *   Presentar la declaración jurada y pagar el saldo son dos actos distintos [DOC-001].
>
> **Cargas Sociales (Empleador):**
> *   Debe presentar mensualmente la declaración jurada de cargas sociales, la cual informa la nómina del período y liquida aportes y contribuciones [DOC-008].
> *   Los aportes son retenidos por el empleador del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador por encima del sueldo [DOC-008].
> *   El vencimiento de la presentación y del pago ocurre en la segunda semana del mes siguiente al período liquidado, escalonado según la terminación de CUIT [DOC-008].
> *   Para la declaración jurada, es requisito tener la nómina actualizada (altas) [DOC-008].
>
> No poseo información suficiente en la base de conocimiento para detallar qué elementos específicos necesita para realizar la liquidación del IVA, más allá de la obligación de presentar la declaración jurada y pagar el saldo.

Recuperados antes del filtro de distancia (filtro activo=True ya aplicado en Chroma):

| ID | Padre | Distancia | Pasa 0.28 |
|---|---|---:|---|
| DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 0.2673312426 | True |
| DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 0.2738837600 | True |
| DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.3024785519 | False |

Candidatos después del filtro: DOC-008::chunk-000-989bdb5081187467, DOC-001::chunk-000-5d1a5023e0007962

Fuentes finales en orden: DOC-008::chunk-000-989bdb5081187467, DOC-001::chunk-000-5d1a5023e0007962

### rerank

Respuesta completa:

> Para liquidar el IVA, el responsable inscripto debe presentar la declaración jurada del período y pagar el saldo en el mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT, siguiendo un escalonamiento donde las terminaciones más bajas vencen primero. Si el vencimiento cae en sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente [DOC-001::chunk-000-5d1a5023e0007962].
>
> Respecto a las cargas sociales, el empleador tiene la obligación de presentar mensualmente una declaración jurada que informe la nómina del período y liquide los aportes y contribuciones. Para esto, se exige tener la nómina actualizada (altas). Los aportes son retenidos del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador por encima del sueldo. El vencimiento de la presentación y el pago ocurre en la segunda semana del mes siguiente al período liquidado, también escalonado por terminación de CUIT [DOC-008::chunk-000-989bdb5081187467].

Recuperados antes del filtro de distancia (filtro activo=True ya aplicado en Chroma):

| ID | Padre | Distancia | Pasa 0.28 |
|---|---|---:|---|
| DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 0.2673312426 | True |
| DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 0.2738837600 | True |
| DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.3024785519 | False |
| DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 0.3230897188 | False |
| DOC-001::chunk-001-619740ed81062fb1 | DOC-001 | 0.3469077945 | False |
| DOC-003::chunk-000-42f59d263c71dc15 | DOC-003 | 0.3610868454 | False |
| DOC-004::chunk-000-e141194203030764 | DOC-004 | 0.3717386723 | False |
| DOC-007::chunk-001-dfd8e869b69c0e65 | DOC-007 | 0.3746900558 | False |

Candidatos después del filtro: DOC-008::chunk-000-989bdb5081187467, DOC-001::chunk-000-5d1a5023e0007962

Fuentes finales en orden: DOC-001::chunk-000-5d1a5023e0007962, DOC-008::chunk-000-989bdb5081187467

Juicio completo:

```json
{
  "items": [
    {
      "id": "DOC-001::chunk-000-5d1a5023e0007962",
      "score": 1.0,
      "reason": "Explica claramente la periodicidad mensual del IVA, el proceso de presentación y pago, y cómo se determina la fecha de vencimiento según la terminación del CUIT."
    },
    {
      "id": "DOC-008::chunk-000-989bdb5081187467",
      "score": 1.0,
      "reason": "Detalla las obligaciones del empleador respecto a las cargas sociales, incluyendo la presentación mensual, la distinción entre aportes y contribuciones, y el esquema de vencimientos."
    }
  ]
}
```

Etapa de pérdida: básico, filtro de distancia (DOC-007 rank 3, 0.3176329136 > 0.28).
Chunking sin reranking, top-3 (DOC-007 chunk 0 rank 4, 0.3230897188); el mismo
umbral lo descartaría aunque se ampliara el top-k sin más cambios.
Reranking, filtro previo al juez (DOC-007 chunks ranks 4 y 8, distancias
0.3230897188 y 0.3746900558). El juez nunca los evalúa y no puede rescatarlos.
El fragmento 1 de DOC-008 también queda excluido (0.3024785519), perdiendo bajas
e intereses. El fragmento 0 termina literalmente en «altas». No se atribuye la
omisión a Lost in the Middle ni a generación cuando la evidencia muestra que
los comprobantes de IVA no llegaron al generador.

## Integridad

```json
{
  "original_count_before": 17,
  "original_count_after": 17,
  "chunks_count_before": 35,
  "chunks_count_after": 35,
  "original_unique_ids_before": 17,
  "original_unique_ids_after": 17,
  "chunks_unique_ids_before": 35,
  "chunks_unique_ids_after": 35,
  "original_full_equality": true,
  "original_hash_before": "17e4c81bedc0cab07856c72cb3f9810ad5f3a569ce8637abd5b610a50e79e9ae",
  "original_hash_after": "17e4c81bedc0cab07856c72cb3f9810ad5f3a569ce8637abd5b610a50e79e9ae",
  "changed_text_ids": [],
  "changed_metadata_ids": [],
  "chunks_same_ids": true,
  "index_result": {
    "original_documents": 17,
    "chunks": 35,
    "chunk_size": 500,
    "chunk_overlap": 100,
    "length_unit": "characters",
    "original_sha256_before": "17e4c81bedc0cab07856c72cb3f9810ad5f3a569ce8637abd5b610a50e79e9ae",
    "original_sha256_after": "17e4c81bedc0cab07856c72cb3f9810ad5f3a569ce8637abd5b610a50e79e9ae",
    "differences_with_clean_json": [
      "DOC-003"
    ],
    "collection": "estudio_contable_chunks"
  }
}
```

## Tiempos y tokens reportados

factual basic:

```json
{
  "timings": {
    "retrieval_seconds": 0.37394369998946786,
    "generation_seconds": 44.28210889996262
  },
  "usage": [
    {
      "run_id": "01a14bc5-bb42-74a0-b67f-dae25ab8e9ba",
      "role": "generator",
      "usage": {
        "input_tokens": 373,
        "output_tokens": 216,
        "total_tokens": 589
      },
      "provider_usage": {
        "cache_tokens_details": null,
        "cached_content_token_count": null,
        "candidates_token_count": 216,
        "candidates_tokens_details": null,
        "prompt_token_count": 373,
        "prompt_tokens_details": [
          {
            "modality": "TEXT",
            "token_count": 373
          }
        ],
        "thoughts_token_count": null,
        "tool_use_prompt_token_count": null,
        "tool_use_prompt_tokens_details": null,
        "total_token_count": 589,
        "traffic_type": null
      }
    }
  ]
}
```
fuera_dominio basic:

```json
{
  "timings": {
    "retrieval_seconds": 1.1028470000019297
  },
  "usage": []
}
```
complacencia basic:

```json
{
  "timings": {
    "retrieval_seconds": 0.403106999990996
  },
  "usage": []
}
```
sinonimos basic:

```json
{
  "timings": {
    "retrieval_seconds": 1.0849832000094466,
    "generation_seconds": 1.694076900021173
  },
  "usage": [
    {
      "run_id": "01a14bc6-7336-7ce1-992b-fde075871877",
      "role": "generator",
      "usage": {
        "input_tokens": 366,
        "output_tokens": 96,
        "total_tokens": 462
      },
      "provider_usage": {
        "cache_tokens_details": null,
        "cached_content_token_count": null,
        "candidates_token_count": 96,
        "candidates_tokens_details": null,
        "prompt_token_count": 366,
        "prompt_tokens_details": [
          {
            "modality": "TEXT",
            "token_count": 366
          }
        ],
        "thoughts_token_count": null,
        "tool_use_prompt_token_count": null,
        "tool_use_prompt_tokens_details": null,
        "total_token_count": 462,
        "traffic_type": null
      }
    }
  ]
}
```
b1_compuesta basic:

```json
{
  "timings": {
    "retrieval_seconds": 1.0678862999775447,
    "generation_seconds": 15.552333900006488
  },
  "usage": [
    {
      "run_id": "01a14bc6-7e4a-7fb1-8dc3-d1bfc96c7fa4",
      "role": "generator",
      "usage": {
        "input_tokens": 529,
        "output_tokens": 255,
        "total_tokens": 784
      },
      "provider_usage": {
        "cache_tokens_details": null,
        "cached_content_token_count": null,
        "candidates_token_count": 255,
        "candidates_tokens_details": null,
        "prompt_token_count": 529,
        "prompt_tokens_details": [
          {
            "modality": "TEXT",
            "token_count": 529
          }
        ],
        "thoughts_token_count": null,
        "tool_use_prompt_token_count": null,
        "tool_use_prompt_tokens_details": null,
        "total_token_count": 784,
        "traffic_type": null
      }
    }
  ]
}
```
b1_compuesta chunks:

```json
{
  "timings": {
    "retrieval_seconds": 1.1044254000298679,
    "generation_seconds": 1.5468226000084542
  },
  "usage": [
    {
      "run_id": "01a14bc6-bf8c-7fe1-9cdb-4736a9bd9f77",
      "role": "generator",
      "usage": {
        "input_tokens": 477,
        "output_tokens": 378,
        "total_tokens": 855
      },
      "provider_usage": {
        "cache_tokens_details": null,
        "cached_content_token_count": null,
        "candidates_token_count": 378,
        "candidates_tokens_details": null,
        "prompt_token_count": 477,
        "prompt_tokens_details": [
          {
            "modality": "TEXT",
            "token_count": 477
          }
        ],
        "thoughts_token_count": null,
        "tool_use_prompt_token_count": null,
        "tool_use_prompt_tokens_details": null,
        "total_token_count": 855,
        "traffic_type": null
      }
    }
  ]
}
```
b1_compuesta rerank:

```json
{
  "timings": {
    "retrieval_seconds": 0.39027039997745305,
    "reranking_seconds": 1.3313809999963269,
    "generation_seconds": 1.6561266999924555
  },
  "usage": [
    {
      "run_id": "01a14bc6-c757-7b83-8d67-9d756879c733",
      "role": "judge",
      "usage": {
        "input_tokens": 437,
        "output_tokens": 189,
        "total_tokens": 626
      },
      "provider_usage": {
        "cache_tokens_details": null,
        "cached_content_token_count": null,
        "candidates_token_count": 189,
        "candidates_tokens_details": null,
        "prompt_token_count": 437,
        "prompt_tokens_details": [
          {
            "modality": "TEXT",
            "token_count": 437
          }
        ],
        "thoughts_token_count": null,
        "tool_use_prompt_token_count": null,
        "tool_use_prompt_tokens_details": null,
        "total_token_count": 626,
        "traffic_type": null
      }
    },
    {
      "run_id": "01a14bc6-cc8a-7083-972a-8f6e67bf76b6",
      "role": "generator",
      "usage": {
        "input_tokens": 477,
        "output_tokens": 256,
        "total_tokens": 733
      },
      "provider_usage": {
        "cache_tokens_details": null,
        "cached_content_token_count": null,
        "candidates_token_count": 256,
        "candidates_tokens_details": null,
        "prompt_token_count": 477,
        "prompt_tokens_details": [
          {
            "modality": "TEXT",
            "token_count": 477
          }
        ],
        "thoughts_token_count": null,
        "tool_use_prompt_token_count": null,
        "tool_use_prompt_tokens_details": null,
        "total_token_count": 733,
        "traffic_type": null
      }
    }
  ]
}
```

## LangSmith

GEMINI_API_KEY configurada. LANGSMITH_API_KEY, LANGSMITH_TRACING,
LANGSMITH_PROJECT y LANGSMITH_ENDPOINT sin configurar. Falta clave y activación
para una traza real; proyecto y endpoint permiten elegir destino (el endpoint
puede usar el valor por defecto si coincide con la región de la cuenta).
No se declara una traza verificada. Los tiempos/tokens anteriores son evidencia
local del callback, no una traza remota de LangSmith.

## Ajustes propuestos, no implementados

Evaluar consultas compuestas por subpreguntas y unir evidencia; calibrar el
umbral con consultas correctas y fuera de dominio en conjunto; probar expansión
por documento padre o fragmentos vecinos para no perder requisitos; valorar si
el juez debe recibir los ocho candidatos antes del corte duro de distancia;
completar LangSmith. No cambiar todo a la vez ni asumir mejoras antes de comparar.

La implementación y los archivos de dependencias mantienen los mismos hashes
antes/después. No se hizo merge, push ni PR. Ocho pruebas locales pasaron.
