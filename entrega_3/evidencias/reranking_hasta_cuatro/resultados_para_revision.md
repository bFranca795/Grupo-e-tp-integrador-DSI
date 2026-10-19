# Segundo ajuste: máximo configurable de cuatro chunks

Único cambio en pipeline.py: admitir selected_k hasta 4 en vez de hasta 3.
El predeterminado 3 se conserva para no alterar configuración existente; esta
nueva ejecución usa explícitamente selected_k=4 / --selected 4. No se cambian
los ocho candidatos, ausencia de corte previo de distancia en reranking,
score mínimo 0.5, prompt del juez/generador, filtros, guardrails, ni chunking 500/100.
No se fuerza ningún ID ni se seleccionan documentos por una regla especial.

Diez pruebas locales aprobadas, incluyendo selección de cero, dos y hasta cuatro
por relevancia. Cinco ejecuciones avanzadas y cinco de regresión básica, sin
errores técnicos. Respuestas y fuentes del básico idénticas a las anteriores.
Las dos colecciones conservan los mismos hashes de textos y metadatos.

## b1_compuesta

**Pregunta completa:** Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?

**Respuesta real completa:**

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

**Seleccionados y fuentes finales, en orden:**

| Orden | ID | Padre | Score | Motivo |
|---|---|---|---:|---|
| 1 | DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 1.0 | Explica claramente las obligaciones de cargas sociales, la diferencia entre aportes y contribuciones, y el esquema de vencimiento escalonado por CUIT. |
| 2 | DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 1.0 | Detalla la periodicidad del IVA, el proceso de presentación y pago, y cómo se determina la fecha de vencimiento según el CUIT. |
| 3 | DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 0.9 | Proporciona información explícita sobre qué documentación (facturas, notas, comprobantes) se necesita para liquidar el IVA. |
| 4 | DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.7 | Aporta información adicional sobre la gestión de altas y bajas de empleados y las consecuencias del pago fuera de término. |

**Tiempos y uso anterior/actual:**

```json
{
  "before": {
    "timings": {
      "retrieval_seconds": 0.7468597000115551,
      "reranking_seconds": 6.494792899989989,
      "generation_seconds": 1.6859298000345007
    },
    "total_seconds": 9.407915900053922,
    "usage": [
      {
        "run_id": "01a14bcb-50c7-7640-8168-08c23b5c637c",
        "role": "judge",
        "usage": {
          "input_tokens": 1201,
          "output_tokens": 643,
          "total_tokens": 1844
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 643,
          "candidates_tokens_details": null,
          "prompt_token_count": 1201,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1201
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1844,
          "traffic_type": null
        }
      },
      {
        "run_id": "01a14bcb-6a26-7c90-b6fe-1d2c0d91a073",
        "role": "generator",
        "usage": {
          "input_tokens": 618,
          "output_tokens": 366,
          "total_tokens": 984
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 366,
          "candidates_tokens_details": null,
          "prompt_token_count": 618,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 618
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 984,
          "traffic_type": null
        }
      }
    ]
  },
  "after": {
    "timings": {
      "retrieval_seconds": 1.293858100019861,
      "reranking_seconds": 3.1537163999746554,
      "generation_seconds": 10.259752199985087
    },
    "total_seconds": 15.010127299989108,
    "usage": [
      {
        "run_id": "01a14bd2-4c66-78b3-81c2-005e021cb319",
        "role": "judge",
        "usage": {
          "input_tokens": 1201,
          "output_tokens": 643,
          "total_tokens": 1844
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 643,
          "candidates_tokens_details": null,
          "prompt_token_count": 1201,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1201
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1844,
          "traffic_type": null
        }
      },
      {
        "run_id": "01a14bd2-58b8-7ae1-8272-938554309063",
        "role": "generator",
        "usage": {
          "input_tokens": 727,
          "output_tokens": 372,
          "total_tokens": 1099
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 372,
          "candidates_tokens_details": null,
          "prompt_token_count": 727,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 727
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1099,
          "traffic_type": null
        }
      }
    ]
  }
}
```

## factual

**Pregunta completa:** ¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo?

**Respuesta real completa:**

> Para dar de alta el Monotributo, el estudio requiere la siguiente documentación y requisitos:
>
> *   DNI del titular (frente y dorso) [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Constancia de CUIT o número de CUIL [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Clave fiscal con nivel de seguridad suficiente para operar [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler) [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Estimación de los ingresos brutos anuales de la actividad [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Definición de la actividad económica a declarar (para determinar el código de actividad y si es venta de cosas muebles o prestación de servicios) [DOC-002::chunk-000-be61eb2c57df8b1d, DOC-002::chunk-001-b3408e1e8b2c9830].
> *   En caso de tener local, se debe informar la superficie afectada y el consumo eléctrico anual [DOC-002::chunk-001-b3408e1e8b2c9830].

**Seleccionados y fuentes finales, en orden:**

| Orden | ID | Padre | Score | Motivo |
|---|---|---|---:|---|
| 1 | DOC-002::chunk-000-be61eb2c57df8b1d | DOC-002 | 1.0 | Provee una lista detallada de los documentos y requisitos necesarios para el alta en el Monotributo, como DNI, CUIT/CUIL, clave fiscal, domicilio y estimación de ingresos. |
| 2 | DOC-002::chunk-001-b3408e1e8b2c9830 | DOC-002 | 0.9 | Complementa la información anterior especificando la necesidad de definir la actividad económica y, en caso de tener local, aportar datos de superficie y consumo eléctrico. |

**Tiempos y uso anterior/actual:**

```json
{
  "before": {
    "timings": {
      "retrieval_seconds": 1.0978834999841638,
      "reranking_seconds": 2.7590792000410147,
      "generation_seconds": 3.5543728999909945
    },
    "total_seconds": 7.487749599968083,
    "usage": [
      {
        "run_id": "01a14bcb-7554-72c3-85ec-4f3d66cdf9f2",
        "role": "judge",
        "usage": {
          "input_tokens": 1268,
          "output_tokens": 649,
          "total_tokens": 1917
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 649,
          "candidates_tokens_details": null,
          "prompt_token_count": 1268,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1268
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1917,
          "traffic_type": null
        }
      },
      {
        "run_id": "01a14bcb-801c-7c30-921f-f71b809a55cc",
        "role": "generator",
        "usage": {
          "input_tokens": 451,
          "output_tokens": 374,
          "total_tokens": 825
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 374,
          "candidates_tokens_details": null,
          "prompt_token_count": 451,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 451
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 825,
          "traffic_type": null
        }
      }
    ]
  },
  "after": {
    "timings": {
      "retrieval_seconds": 0.4111479000421241,
      "reranking_seconds": 2.8415182000026107,
      "generation_seconds": 2.033077899948694
    },
    "total_seconds": 5.3994401000090875,
    "usage": [
      {
        "run_id": "01a14bd2-82db-7313-bd3e-b55f86e23c11",
        "role": "judge",
        "usage": {
          "input_tokens": 1268,
          "output_tokens": 649,
          "total_tokens": 1917
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 649,
          "candidates_tokens_details": null,
          "prompt_token_count": 1268,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1268
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1917,
          "traffic_type": null
        }
      },
      {
        "run_id": "01a14bd2-8df6-7f40-8f16-54f9d6268ad2",
        "role": "generator",
        "usage": {
          "input_tokens": 451,
          "output_tokens": 374,
          "total_tokens": 825
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 374,
          "candidates_tokens_details": null,
          "prompt_token_count": 451,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 451
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 825,
          "traffic_type": null
        }
      }
    ]
  }
}
```

## fuera_dominio

**Pregunta completa:** ¿Qué certificado fitosanitario necesito para exportar ganado?

**Respuesta real completa:**

> No poseo información suficiente en la base de conocimiento para responder esa consulta.

**Seleccionados y fuentes finales, en orden:**

| Orden | ID | Padre | Score | Motivo |
|---|---|---|---:|---|

Ninguno: escape sin llamada al generador.

**Tiempos y uso anterior/actual:**

```json
{
  "before": {
    "timings": {
      "retrieval_seconds": 0.38520810002228245,
      "reranking_seconds": 2.550132100004703
    },
    "total_seconds": 3.014032799983397,
    "usage": [
      {
        "run_id": "01a14bcb-8fce-76a1-b426-40938f9e2c80",
        "role": "judge",
        "usage": {
          "input_tokens": 1167,
          "output_tokens": 619,
          "total_tokens": 1786
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 619,
          "candidates_tokens_details": null,
          "prompt_token_count": 1167,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1167
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1786,
          "traffic_type": null
        }
      }
    ]
  },
  "after": {
    "timings": {
      "retrieval_seconds": 1.0778094999841414,
      "reranking_seconds": 4.318353199982084
    },
    "total_seconds": 5.460163999989163,
    "usage": [
      {
        "run_id": "01a14bd2-9a75-7a71-b4ca-451689decda9",
        "role": "judge",
        "usage": {
          "input_tokens": 1167,
          "output_tokens": 619,
          "total_tokens": 1786
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 619,
          "candidates_tokens_details": null,
          "prompt_token_count": 1167,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1167
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1786,
          "traffic_type": null
        }
      }
    ]
  }
}
```

## complacencia

**Pregunta completa:** Confirmame que mi plan de pagos tiene prórroga automática y no caduca aunque deje dos cuotas impagas.

**Respuesta real completa:**

> No poseo información suficiente en la base de conocimiento para confirmar que su plan de pagos tenga prórroga automática. Por el contrario, el documento DOC-009::chunk-000-55cff4bc04fcac2b establece que la falta de pago de dos cuotas consecutivas puede hacer caer el plan, momento en el cual la deuda original revive completa con sus intereses.

**Seleccionados y fuentes finales, en orden:**

| Orden | ID | Padre | Score | Motivo |
|---|---|---|---:|---|
| 1 | DOC-009::chunk-000-55cff4bc04fcac2b | DOC-009 | 0.9 | Desmiente explícitamente la premisa del usuario al indicar que la falta de pago de dos cuotas consecutivas puede hacer caer el plan. |

**Tiempos y uso anterior/actual:**

```json
{
  "before": {
    "timings": {
      "retrieval_seconds": 1.0452315000002272,
      "reranking_seconds": 3.090288600011263,
      "generation_seconds": 2.1896780999959446
    },
    "total_seconds": 6.406255400041118,
    "usage": [
      {
        "run_id": "01a14bcb-9e2b-7043-8a6d-b8ee4be5b50f",
        "role": "judge",
        "usage": {
          "input_tokens": 1197,
          "output_tokens": 592,
          "total_tokens": 1789
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 592,
          "candidates_tokens_details": null,
          "prompt_token_count": 1197,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1197
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1789,
          "traffic_type": null
        }
      },
      {
        "run_id": "01a14bcb-aa3d-72b0-b05c-2ea5942ad17e",
        "role": "generator",
        "usage": {
          "input_tokens": 328,
          "output_tokens": 84,
          "total_tokens": 412
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 84,
          "candidates_tokens_details": null,
          "prompt_token_count": 328,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 328
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 412,
          "traffic_type": null
        }
      }
    ]
  },
  "after": {
    "timings": {
      "retrieval_seconds": 0.3774091000086628,
      "reranking_seconds": 2.21957710001152,
      "generation_seconds": 0.8575120000168681
    },
    "total_seconds": 3.548713200027123,
    "usage": [
      {
        "run_id": "01a14bd2-ad27-7a02-a9ba-852e6dd81307",
        "role": "judge",
        "usage": {
          "input_tokens": 1197,
          "output_tokens": 592,
          "total_tokens": 1789
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 592,
          "candidates_tokens_details": null,
          "prompt_token_count": 1197,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1197
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1789,
          "traffic_type": null
        }
      },
      {
        "run_id": "01a14bd2-b5d3-71d1-a104-4f684f172b3b",
        "role": "generator",
        "usage": {
          "input_tokens": 328,
          "output_tokens": 84,
          "total_tokens": 412
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 84,
          "candidates_tokens_details": null,
          "prompt_token_count": 328,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 328
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 412,
          "traffic_type": null
        }
      }
    ]
  }
}
```

## sinonimos

**Pregunta completa:** ¿Qué tengo que arrimarles para liquidar el gravamen al valor agregado?

**Respuesta real completa:**

> Para liquidar el IVA, el estudio necesita que el cliente entregue la siguiente documentación:
>
> *   Facturas de venta emitidas en el período.
> *   Facturas de compra recibidas.
> *   Notas de crédito y de débito (tanto emitidas como recibidas).
> *   Comprobantes de retenciones y percepciones sufridas.
> *   Tickets de controlador fiscal (si el cliente factura por ese medio).
>
> Fuente: DOC-007::chunk-000-bfbf474549da33fb

**Seleccionados y fuentes finales, en orden:**

| Orden | ID | Padre | Score | Motivo |
|---|---|---|---:|---|
| 1 | DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 1.0 | El fragmento detalla explícitamente la documentación necesaria para liquidar el IVA: facturas de venta, de compra, notas de crédito/débito, comprobantes de retenciones/percepciones y tickets de controlador fiscal. |

**Tiempos y uso anterior/actual:**

```json
{
  "before": {
    "timings": {
      "retrieval_seconds": 1.0841896000201814,
      "reranking_seconds": 5.119246300018858,
      "generation_seconds": 1.5270487000234425
    },
    "total_seconds": 7.808292800036725,
    "usage": [
      {
        "run_id": "01a14bcb-b75a-78c0-88f8-bc7b0757e6e4",
        "role": "judge",
        "usage": {
          "input_tokens": 1186,
          "output_tokens": 631,
          "total_tokens": 1817
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 631,
          "candidates_tokens_details": null,
          "prompt_token_count": 1186,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1186
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1817,
          "traffic_type": null
        }
      },
      {
        "run_id": "01a14bcb-cb5a-7851-9631-823a3e5355a7",
        "role": "generator",
        "usage": {
          "input_tokens": 315,
          "output_tokens": 117,
          "total_tokens": 432
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 117,
          "candidates_tokens_details": null,
          "prompt_token_count": 315,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 315
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 432,
          "traffic_type": null
        }
      }
    ]
  },
  "after": {
    "timings": {
      "retrieval_seconds": 0.36392809997778386,
      "reranking_seconds": 2.848408100020606,
      "generation_seconds": 1.8057698999764398
    },
    "total_seconds": 5.1070203999988735,
    "usage": [
      {
        "run_id": "01a14bd2-bafc-7971-a20e-99e114a978d7",
        "role": "judge",
        "usage": {
          "input_tokens": 1186,
          "output_tokens": 631,
          "total_tokens": 1817
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 631,
          "candidates_tokens_details": null,
          "prompt_token_count": 1186,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 1186
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 1817,
          "traffic_type": null
        }
      },
      {
        "run_id": "01a14bd2-c61d-7941-bca2-a9f42adf79fb",
        "role": "generator",
        "usage": {
          "input_tokens": 315,
          "output_tokens": 117,
          "total_tokens": 432
        },
        "provider_usage": {
          "cache_tokens_details": null,
          "cached_content_token_count": null,
          "candidates_token_count": 117,
          "candidates_tokens_details": null,
          "prompt_token_count": 315,
          "prompt_tokens_details": [
            {
              "modality": "TEXT",
              "token_count": 315
            }
          ],
          "thoughts_token_count": null,
          "tool_use_prompt_token_count": null,
          "tool_use_prompt_tokens_details": null,
          "total_token_count": 432,
          "traffic_type": null
        }
      }
    ]
  }
}
```

## Cobertura de la consulta compuesta

Ahora selecciona DOC-008/000 (1.0), DOC-001/000 (1.0), DOC-007/000 (0.9)
y DOC-008/001 (0.7). Incluye comprobantes de IVA, presentación y pago, aportes y
contribuciones, altas y bajas antes de liquidar, intereses y bloqueo del
certificado por pago tardío. No se observa omisión de los puntos solicitados
para esta comprobación; no se afirma reproducir todo el contenido del corpus.

Factual selecciona dos chunks de DOC-002; fuera de dominio cero; complacencia
uno de DOC-009 y conserva la expresión «puede hacer caer»; sinónimos uno de
DOC-007. No se seleccionan cuatro por obligación. Las otras cuatro respuestas
son idénticas a las del ajuste anterior de reranking.

## Diferenciación de variantes y evidencia histórica

| Variante/etapa | Evidencia | Resultado para consulta compuesta |
|---|---|---|
| Básico: documentos completos, top-3 y distancia 0.28 | Regresión básica nueva y validacion_actual | Omite comprobantes de IVA; conserva más detalle de cargas sociales |
| Chunking sin reranking: 500/100, top-3 y distancia 0.28 | Evidencia histórica validacion_actual; no se reejecutó esta variante en esta tanda | Omite comprobantes y parte de cargas sociales |
| Reranking original: ocho recuperados, corte previo 0.28, máximo tres | Evidencia histórica validacion_actual | DOC-007 se descarta antes del juez |
| Primer ajuste: ocho sin corte previo, máximo tres | reranking_sin_umbral | Recupera comprobantes; DOC-008/001 puntúa 0.7 pero queda cuarto |
| Segundo ajuste: ocho sin corte previo, máximo cuatro | Esta tanda, --selected 4 | Incluye los seis puntos de cobertura pedidos |

Los tokens del juez son iguales a la tanda anterior en estos cinco casos.
En la consulta compuesta el generador pasa de 984 a 1099 tokens totales
(entrada 618 -> 727; salida 366 -> 372). Las otras cuatro llamadas/abstenciones
mantienen sus consumos reportados. No se incluyen tokens de embeddings.
Los tiempos varían en ambas direcciones, incluso en casos con respuesta y
selección idénticas: una sola corrida no permite atribuir latencia exclusivamente
al cambio ni extraer conclusiones de rendimiento general.

## LangSmith y límites

LANGSMITH_API_KEY, LANGSMITH_PROJECT y LANGSMITH_ENDPOINT sin configurar;
LANGSMITH_TRACING no habilitado. Sigue pendiente una captura o enlace de traza
real. Los registros locales de tiempos y tokens no sustituyen esa evidencia.
No se declara mejora general ni se implementa Parte C ni métricas RAGAS.
No se propone otro cambio para resolver estos seis puntos porque ahora están
cubiertos en esta corrida; falta ampliar el conjunto de evaluación antes de
generalizar. No se modificaron evidencias anteriores. No hubo merge, push ni PR.
