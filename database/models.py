"""
Modelos SQLAlchemy - Sistema Área de Alimentos Fighiera
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Rubro(Base):
    __tablename__ = "rubros"

    id_rubro    = Column(Integer, primary_key=True)
    nombre      = Column(String(255), nullable=False)
    valor       = Column(Float, default=0.0)

    establecimientos = relationship("Establecimiento", back_populates="rubro_rel",
                                    foreign_keys="Establecimiento.rubro_id")

    def __repr__(self):
        return f"<Rubro {self.id_rubro}: {self.nombre}>"


class Anexo1(Base):
    __tablename__ = "anexo1"
    id_rubro = Column(Integer, primary_key=True)
    nombre   = Column(String(255))
    valor    = Column(Float, default=0.0)


class Anexo2(Base):
    __tablename__ = "anexo2"
    id_rubro = Column(Integer, primary_key=True)
    nombre   = Column(String(255))
    valor    = Column(Float, default=0.0)


class Anexo3(Base):
    __tablename__ = "anexo3"
    id_rubro = Column(Integer, primary_key=True)
    nombre   = Column(String(255))
    valor    = Column(Float, default=0.0)


class Inscripto(Base):
    __tablename__ = "inscriptos"

    codigo_inscripcion         = Column(Integer, primary_key=True)
    apellido_razonsocial       = Column(String(200))
    nombres                    = Column(String(255))
    tipo_documento             = Column(String(6))
    numero_documento           = Column(String(8))
    tipo_identificacion        = Column(String(5))
    numero_identificacion      = Column(String(11))
    domicilio                  = Column(String(255))
    numero_domicilio           = Column(String(50))
    localidad                  = Column(String(255))
    codigo_postal              = Column(String(4))
    provincia                  = Column(String(255))
    telefono                   = Column(String(14))
    telefono_movil             = Column(String(18))
    correo                     = Column(String(255))
    observaciones              = Column(Text)
    monto_sellado              = Column(Float, default=0.0)
    fecha_inicio_tramite       = Column(DateTime, nullable=True)

    establecimientos = relationship("Establecimiento", back_populates="inscripto")

    @property
    def nombre_completo(self):
        apellido = (self.apellido_razonsocial or "").strip().title()
        nombres  = (self.nombres or "").strip().title()
        if nombres:
            return f"{apellido}, {nombres}"
        return apellido


class Establecimiento(Base):
    __tablename__ = "establecimientos"

    codigo_establecimiento     = Column(String(6), primary_key=True)
    codigo_inscripcion         = Column(Integer, ForeignKey("inscriptos.codigo_inscripcion"), nullable=True)
    nombre_establecimiento     = Column(String(255))
    domicilio_establecimiento  = Column(String(150))
    numero_establecimiento     = Column(String(50))
    localidad_establecimiento  = Column(String(50))
    codigo_postal              = Column(Integer, nullable=True)
    provincia_establecimiento  = Column(String(50))
    telefono_establecimiento   = Column(String(14))
    rubro_id                   = Column(Integer, ForeignKey("rubros.id_rubro"), nullable=True)
    monto                      = Column(Float, default=0.0)
    anexo1_id                  = Column(Integer, nullable=True)
    monto1                     = Column(Float, default=0.0)
    anexo2_id                  = Column(Integer, nullable=True)
    monto2                     = Column(Float, default=0.0)
    anexo3_id                  = Column(Integer, nullable=True)
    monto3                     = Column(Float, default=0.0)
    estado_tramite             = Column(String(25))
    fecha_certificado          = Column(DateTime, nullable=True)
    acta_emplazamiento         = Column(Integer, nullable=True)
    acta_infraccion            = Column(Integer, nullable=True)
    solicitudes                = Column(String(100))
    observaciones              = Column(Text)
    acta_multinfuncion         = Column(Integer, nullable=True)
    planilla_descargo          = Column(DateTime, nullable=True)
    baja                       = Column(Boolean, default=False)

    inscripto    = relationship("Inscripto", back_populates="establecimientos")
    rubro_rel    = relationship("Rubro", back_populates="establecimientos",
                                foreign_keys=[rubro_id])
    deudas       = relationship("Deuda", back_populates="establecimiento",
                                cascade="all, delete-orphan")
    auditorias   = relationship("Auditoria", back_populates="establecimiento",
                                cascade="all, delete-orphan")
    sanidad_list = relationship("Sanidad", back_populates="establecimiento",
                                cascade="all, delete-orphan")

    @property
    def monto_total(self):
        return (self.monto or 0) + (self.monto1 or 0) + (self.monto2 or 0) + (self.monto3 or 0)


class Emision(Base):
    __tablename__ = "emision"

    id_emision  = Column(String(10), primary_key=True)
    periodo     = Column(String(2))
    anio        = Column(Integer)
    vencimiento = Column(DateTime, nullable=True)
    primer_mora = Column(DateTime, nullable=True)
    segunda_mora= Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Emision {self.id_emision}>"


class Deuda(Base):
    __tablename__ = "deudas"

    codigo_deuda            = Column(Integer, primary_key=True)
    codigo_establecimiento  = Column(String(6), ForeignKey("establecimientos.codigo_establecimiento"))
    periodo                 = Column(Integer)
    anio                    = Column(Integer)
    vencimiento             = Column(DateTime, nullable=True)
    importe                 = Column(Float, default=0.0)
    pago                    = Column(Boolean, default=False)
    fecha_pago              = Column(DateTime, nullable=True)
    monto_abonado           = Column(Float, default=0.0)
    medio_pago              = Column(String(20), nullable=True)  # EFECTIVO / TRANSFERENCIA

    establecimiento = relationship("Establecimiento", back_populates="deudas")

    @property
    def saldo(self):
        if self.pago:
            return 0.0
        return (self.importe or 0.0) - (self.monto_abonado or 0.0)


class Auditoria(Base):
    __tablename__ = "auditorias"

    codigo_auditoria        = Column(Integer, primary_key=True)
    codigo_establecimiento  = Column(String(6), ForeignKey("establecimientos.codigo_establecimiento"),
                                    nullable=True)
    numero_auditoria        = Column(Float, nullable=True)
    fecha_auditoria         = Column(DateTime, nullable=True)
    alcances                = Column(String(255))
    conformidades           = Column(String(255))
    acta_multinfuncion      = Column(String(255))
    no_conformidades        = Column(Text)
    detalle_anexo           = Column(Text)
    conclusiones            = Column(Text)
    material_adjunto        = Column(Text)
    anexo_auditoria_num     = Column(Text)

    establecimiento = relationship("Establecimiento", back_populates="auditorias")


class Sanidad(Base):
    __tablename__ = "sanidad"

    codigo_sanidad              = Column(Integer, primary_key=True)
    codigo_establecimiento      = Column(String(6), ForeignKey("establecimientos.codigo_establecimiento"))
    libreta_sanitaria           = Column(Boolean, default=False)
    apellido_titular            = Column(String(50))
    nombre_titular              = Column(String(100))
    venc_libreta_titular        = Column(DateTime, nullable=True)
    apellido_empleado1          = Column(String(50))
    nombre_empleado1            = Column(String(255))
    venc_libreta_empleado1      = Column(DateTime, nullable=True)
    apellido_empleado2          = Column(String(50))
    nombre_empleado2            = Column(String(255))
    venc_libreta_empleado2      = Column(DateTime, nullable=True)
    carnet_manipulador          = Column(Boolean, default=False)
    certificado_manipulador     = Column(Boolean, default=False)
    fecha_certificado_manip     = Column(DateTime, nullable=True)
    inscripto_curso_bpm         = Column(Boolean, default=False)

    establecimiento = relationship("Establecimiento", back_populates="sanidad_list")
