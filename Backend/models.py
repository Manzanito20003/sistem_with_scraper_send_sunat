from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class Cliente(BaseModel):
    nombre: Optional[str]
    dni: Optional[str] = Field(None, max_length=8)
    ruc: Optional[str] = Field(None, max_length=11)

    @model_validator(mode="after")
    def al_menos_un_identificador(self):
        if not self.dni and not self.ruc:
            raise ValueError("Debe ingresar DNI o RUC.")
        return self


class Producto(BaseModel):
    cantidad: int = Field(..., gt=0)
    descripcion: str
    unidad_medida: Literal["KILOGRAMO", "CAJA", "UNIDAD"]
    precio_base: float
    igv: float
    igv_total: float
    precio_total: float

    @field_validator("precio_base", "igv", "precio_total", "igv_total")
    @classmethod
    def valores_no_negativos(cls, v):
        if v < 0:
            raise ValueError("Los valores monetarios deben ser positivos.")
        return v


class Resumen(BaseModel):
    serie: str
    numero: str
    sub_total: float
    igv_total: float
    total: float

    @field_validator("total")
    @classmethod
    def total_debe_ser_valido(cls, v, info):
        values = info.data
        subtotal = values.get("sub_total", 0)
        igv = values.get("igv_total", 0)
        if abs((subtotal + igv) - v) > 0.01:
            raise ValueError("El total no coincide con subtotal + IGV.")
        return v

    @field_validator("sub_total", "igv_total", "total")
    @classmethod
    def valores_no_negativos(cls, v):
        if v < 0:
            raise ValueError("Los valores totales de la boleta deben ser positivos")
        return v


class BoletaData(BaseModel):
    cliente: Cliente
    productos: List[Producto]
    resumen: Resumen
    fecha: str
    id_remitente: str
    id_cliente: str
    tipo_documento: Literal["BOLETA", "FACTURA"] = "BOLETA"

    @field_validator("fecha")
    @classmethod
    def fecha_valida(cls, v):
        try:
            datetime.strptime(v, "%d/%m/%Y")
        except ValueError:
            raise ValueError("La fecha debe tener el formato dd/mm/yyyy.")
        return v
