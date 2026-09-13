from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Literal

class ConsultaContable(BaseModel):

  intencion: Literal[
      "CONSULTA_VENCIMIENTO",
      "DOCUMENTACION_REQUERIDA",
      "ESTADO_TRAMITE",
      "CONSULTA_SOSPECHOSA",
      "CONSULTA_COMPLEJA"
  ]

  cuit: str | None = None
  impuesto: str | None = None
  periodo: str | None = None
  tipo_tramite: str | None = "N/A"

  @field_validator("cuit")
  @classmethod
  def validar_cuit(cls, value):

    #  Normaliza el CUIT eliminando guiones y valida
    #  que tenga exactamente 11 dígitos.

      if value is None:
          return None

      # Sacamos guiones y espacios.
      cuit_limpio = value.replace("-", "").replace(" ", "")

      if not cuit_limpio.isdigit():
          raise ValueError("El CUIT debe contener solamente números")

      if len(cuit_limpio) != 11:
          raise ValueError("El CUIT debe contener exactamente 11 dígitos")

      return cuit_limpio
