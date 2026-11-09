"""Validadores puros y determinísticos; sin I/O, logging, modelos ni persistencia.

Longitud: len(texto) sobre el original (puntos de código Unicode, no bytes ni
grafemas), igual al límite estructural de /consultar. No se recorta ni normaliza
antes de contar. Se rechazan tipos no str y sustitutos Unicode no válidos.

Inyección: se buscan combinaciones de verbos y objetivos internos; nunca palabras
aisladas. Solo para reconocer patrones se aplica NFKC, casefold, eliminación de
acentos y caracteres de formato, y colapso de espacios. No se altera la entrada.
El detector no comprueba vacío ni longitud: debe usarse junto al otro validador.

Límites: no interpreta intención ni negaciones/citas. Una cita literal de un ataque
puede rechazarse. Paráfrasis no previstas, homógrafos entre alfabetos, texto
codificado e instrucciones indirectas pueden evadirlo. No es una garantía de
seguridad. Los validadores de entrada no examinan documentos ni respuestas.
"""

import re
import unicodedata
from typing import Literal, TypedDict


Motivo = Literal["entrada_vacia", "longitud_excedida", "prompt_injection", "tipo_invalido", "unicode_invalido"]


class ResultadoValidacion(TypedDict):
    permitida: bool
    motivo: Motivo | None


def _resultado(motivo: Motivo | None = None) -> ResultadoValidacion:
    return {"permitida": motivo is None, "motivo": motivo}


def _error_texto(texto) -> Motivo | None:
    if not isinstance(texto, str):
        return "tipo_invalido"
    if any(0xD800 <= ord(char) <= 0xDFFF for char in texto):
        return "unicode_invalido"
    return None


def validar_entrada(texto: str) -> ResultadoValidacion:
    """Acepta texto no vacío de hasta 2000 puntos de código; devuelve solo motivo.

    Errores de tipo/Unicode se representan como rechazo, sin excepciones que
    incorporen la entrada. No clasifica prompt injection ni datos personales.
    """
    error = _error_texto(texto)
    if error:
        return _resultado(error)
    if not texto.strip():
        return _resultado("entrada_vacia")
    if len(texto) > 2000:
        return _resultado("longitud_excedida")
    return _resultado()


_PATRONES = tuple(re.compile(pattern) for pattern in (
    # Ignorar/olvidar reglas propias o instrucciones anteriores/internas.
    r"\b(?:ignora(?:r|s|d|n)?|ignore(?:s|n)?|olvida(?:r|s|d|n|te)?|olvide(?:s|n|se)?|omite|omiti|descarta)\s+(?:de\s+)?"
    r"(?:(?:todas?|todos?|las?|los?)\s+){0,4}"
    r"(?:(?:instrucciones|reglas|restricciones)\s+(?:anteriores|previas|internas|del\s+(?:sistema|agente))"
    r"|(?:tus|sus)\s+(?:instrucciones|reglas|restricciones))\b",
    r"\b(?:ignore|forget|disregard|override)\s+(?:about\s+)?(?:(?:all|any|the)\s+){0,3}"
    r"(?:(?:previous|prior|above|system|your)\s+){1,3}(?:instructions|rules|restrictions|constraints)\b",
    r"\b(?:ignore|forget|disregard|override)\s+all\s+(?:the\s+)?(?:instructions|rules|restrictions)\b",
    # Pedir un comportamiento sin restricciones, con destinatario agente/modelo.
    r"\b(?:actua|actuar|responde)\s+(?:como\s+si\s+no\s+tuvieras|sin)\s+(?:restricciones|reglas|limites)\b",
    r"\b(?:act|behave|respond)\s+(?:as\s+if\s+you\s+(?:had|have)\s+no|without)\s+"
    r"(?:restrictions|rules|constraints|limits)\b",
    r"\bpretend\s+(?:that\s+)?you\s+(?:have|had)\s+no\s+(?:restrictions|rules|constraints|limits)\b",
    r"\b(?:sos|eres)\s+(?:ahora\s+)?(?:un\s+)?(?:asistente|agente|modelo)\s+sin\s+(?:restricciones|reglas|limites)\b",
    r"\byou\s+are\s+(?:now\s+)?(?:an?\s+)?(?:unrestricted|unfiltered)\s+(?:assistant|agent|model)\b",
    # Extraer el prompt/instrucciones internos, no consultar instrucciones fiscales.
    r"\b(?:revela(?:me|r)?|revele(?:me)?|muestra(?:me)?|muestre(?:me)?|mostra(?:me|s|r)?|"
    r"dime|decime|imprimi|imprime|reveal|show|display|expose|print|tell\s+me|give\s+me)\s+"
    r"(?:me\s+)?(?:(?:el|la|los|las|tu|tus|sus|your|the)\s+){0,4}"
    r"(?:prompt\s+(?:del\s+)?(?:sistema|interno)|(?:instrucciones|reglas)\s+(?:internas|del\s+(?:sistema|agente))"
    r"|system\s+(?:prompt|instructions)|(?:internal|hidden)\s+(?:instructions|rules))\b",
    # Desactivar/bypassear controles explícitos; 'seguridad' sola no alcanza.
    r"\b(?:desactiva(?:r)?|deshabilita(?:r)?|anula|elimina|disable|deactivate|bypass|turn\s+off|remove)\s+"
    r"(?:(?:el|la|los|las|tu|tus|sus|the|your|all)\s+){0,4}"
    r"(?:(?:controles|filtros)\s+de\s+seguridad|restricciones\s+(?:del\s+)?(?:agente|sistema)"
    r"|(?:safety|security)\s+(?:checks|controls|filters|rules)|guardrails|safeguards)\b",
))


def detectar_prompt_injection(texto: str) -> ResultadoValidacion:
    """Rechaza patrones explícitos de manipulación en español/inglés.

    Devuelve aceptación si no encuentra patrones, no una certificación de que la
    entrada sea segura. No devuelve texto, fragmentos coincidentes ni errores crudos.
    """
    error = _error_texto(texto)
    if error:
        return _resultado(error)
    normalizado = unicodedata.normalize("NFKC", texto).casefold()
    normalizado = "".join(char for char in unicodedata.normalize("NFD", normalizado)
                          if unicodedata.category(char) not in {"Mn", "Cf"})
    normalizado = " ".join(normalizado.split())
    if any(pattern.search(normalizado) for pattern in _PATRONES):
        return _resultado("prompt_injection")
    return _resultado()


# Enmascaramiento de salida: los prefijos del CUIT compacto evitan tratar cualquier
# entero de once cifras como identidad. El formato 2-8-1 se oculta incluso si el
# prefijo/DV están mal escritos. No se exige checksum: un error no vuelve público
# el resto del identificador. No se consulta padrón ni se certifica identidad.
_H = r"[^\S\r\n]"  # Espacio horizontal Unicode; no une líneas distintas.
_GUION = r"[-\u2010\u2011]"
_SEP = rf"(?:{_H}+|{_GUION})"
_GSEP = rf"(?:{_H}+|{_GUION})?"
_EMAIL = (
    r"(?<![\w\u0300-\u036f.+%-])[\w](?:[\w\u0300-\u036f.+%'-]*[\w\u0300-\u036f])?@"
    r"(?:[\w](?:[\w\u0300-\u036f-]*[\w\u0300-\u036f])?\.)+"
    r"[^\W\d_](?:[^\W\d_]|[\u0300-\u036f]){1,62}(?![\w\u0300-\u036f-])"
)
_CUIT = (rf"(?<![\w\-])(?:[0-9]{{2}}{_GUION}[0-9]{{8}}{_GUION}[0-9]"
         r"|(?:20|23|24|27|29|30|33|34|50|51|55)[0-9]{9})(?![\w\-])")
_NACIONAL = (
    rf"(?:11{_SEP}[0-9]{{4}}{_GSEP}[0-9]{{4}}"
    rf"|[23][0-9]{{2}}{_SEP}[0-9]{{3}}{_GSEP}[0-9]{{4}}"
    rf"|[23][0-9]{{3}}{_SEP}[0-9]{{2}}{_GSEP}[0-9]{{4}})"
)
_PREFIJO = rf"(?:\+54{_H}*(?:9{_H}*)?|0)"
_TELEFONO = (
    rf"(?<![\w+\-])(?:{_PREFIJO}?{_NACIONAL}"
    rf"|{_PREFIJO}(?:11[0-9]{{8}}|[23][0-9]{{9}}))(?![\w\-])"
)
_PII = re.compile(rf"(?P<email>{_EMAIL})|(?P<cuit>{_CUIT})|(?P<telefono>{_TELEFONO})", re.IGNORECASE)
_MONEDA_ANTES = re.compile(r"(?:[$€]|\b(?:ARS|USD|EUR|pesos))\s*$", re.IGNORECASE)
_IDENTIDAD_ANTES = re.compile(
    r"\b(?:CUIT|CUIL)\s*(?:nro\.?|n[°º]|número)?\s*[:=#]?\s*"
    r"(?:(?:[$€]|ARS|USD|EUR)\s*)?$", re.IGNORECASE)
_REFERENCIA_ANTES = re.compile(r"\b(?:factura|comprobante|asiento|movimiento)\s*(?:nro\.?|n[°º]|número)?\s*[:#]?\s*$", re.IGNORECASE)
_MONEDA_DESPUES = re.compile(r"^\s*(?:%|[$€]|(?:ARS|USD|EUR|pesos)\b)", re.IGNORECASE)


def enmascarar_pii(texto: str) -> str:
    """Reemplaza emails, teléfonos argentinos y CUIT/CUIL sin registrar entradas.

    Emails primero (incluidos locales numéricos), CUIT antes que teléfonos. Los
    spans se reemplazan completos, sin alterar texto fuera de ellos. Los números
    compactos con moneda, porcentaje o parte decimal, y las referencias contables
    explícitas, se conservan salvo rótulo inmediato CUIT/CUIL; un CUIT con guiones
    siempre se oculta. Vacío devuelve
    vacío; tipos incorrectos generan TypeError genérico
    y Unicode no válido ValueError genérico, sin incluir el contenido recibido.

    Es heurístico: un entero sin contexto con prefijo/formato CUIT puede ser un
    falso positivo; un CUIT rotulado como importe/referencia puede no ocultarse.
    No cubre todo RFC de email, teléfonos extranjeros, extensiones, caracteres
    numéricos no ASCII ni ofuscaciones. No modifica normalización o espacios.
    No certifica ausencia de PII y no enmascara otros tipos de datos personales.
    """
    error = _error_texto(texto)
    if error == "tipo_invalido":
        raise TypeError("El texto debe ser una cadena.")
    if error:
        raise ValueError("El texto contiene Unicode no válido.")

    fin_ultimo_enmascarado = 0

    def reemplazar(match):
        nonlocal fin_ultimo_enmascarado
        tipo = match.lastgroup
        if tipo == "email":
            fin_ultimo_enmascarado = match.end()
            return "[EMAIL_OCULTO]"
        valor = match.group()
        # La forma 2-8-1 no es un importe: prevalece aun junto a $ o %.
        if tipo == "cuit" and not valor.isdigit():
            fin_ultimo_enmascarado = match.end()
            return "[CUIT_OCULTO]"
        antes, despues = texto[fin_ultimo_enmascarado:match.start()], texto[match.end():]
        if tipo == "cuit":
            if _IDENTIDAD_ANTES.search(antes):
                fin_ultimo_enmascarado = match.end()
                return "[CUIT_OCULTO]"
            # Solo los enteros compactos son ambiguos con importes/referencias.
            # Un teléfono formateado no deja de ser PII por tener un precio al lado.
            if (_MONEDA_ANTES.search(antes) or _MONEDA_DESPUES.search(despues)
                    or _REFERENCIA_ANTES.search(antes)
                    or re.search(r"[0-9][.,]$", antes) or re.match(r"[.,][0-9]", despues)):
                return valor
            fin_ultimo_enmascarado = match.end()
            return "[CUIT_OCULTO]"
        # Evita sustituir el final de una secuencia numérica mayor separada por espacios.
        if re.search(r"[0-9][^\S\r\n\-]*$", antes):
            return valor
        fin_ultimo_enmascarado = match.end()
        return "[TELEFONO_OCULTO]"

    return _PII.sub(reemplazar, texto)
