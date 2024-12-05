from utils.helpers import parse_date
from datetime import datetime
import pandas as pd


class ExcelBaseAdapter:
    def __init__(self, row):
        self.row = row

    # Métodos comunes a todos los adaptadores

    def get_rut(self):
        return str(self.row["RUT"]).strip().upper()

    def get_sex(self):
        return True if str(self.row["sexo"]).strip().lower() == "m" else False

    def get_birthdate(self):
        return parse_date(self.row["fecha_nacimiento"])

    def get_name(self):
        return str(self.row["nombres"]).strip().capitalize()

    def get_last_name_paternal(self):
        return str(self.row["apellido_paterno"]).strip().capitalize()

    def get_last_name_maternal(self):
        return str(self.row["apellido_materno"]).strip().capitalize()

    def get_address(self):
        return str(self.row["DireccionNino"]).strip().upper()

    def get_nationality(self):
        return str(self.row["Nacionalidad"]).strip().upper()

    def get_region(self):
        return int(self.row["RegionNino"])

    def get_commune(self):
        return str(self.row["Comuna"]).strip().upper()

    def get_location_key(self):
        return f"{self.get_region()}-{self.get_commune()}"

    def get_solicitor_name(self):
        return str(self.row["Solicitante_Ingreso"]).strip().upper()

    def get_legal_quality_name(self):
        return str(self.row["CalidadJuridica"]).strip().upper()

    def get_tribunal_name(self):
        return str(self.row["Tribunal"]).strip().upper()

    def get_proceedings(self):
        return str(self.row["Expediente"]).strip().upper()

    def get_cause_of_entry(self):
        return str(self.row["CausalIngreso_1"]).strip().upper()

    def get_cod_nna(self):
        return int(self.row["codNNA"])

    def get_tipo_proyecto(self):
        return str(self.row["tipo de programa"]).strip().upper()


class ExcelAdapter(ExcelBaseAdapter):
    def get_institution_name(self):
        return str(self.row["institucion"]).strip().upper()

    def get_project_code(self):
        return int(self.row["CodProyecto"])

    def get_project_name(self):
        return str(self.row["proyecto"]).strip().upper()

    def get_attention(self):
        return (
            True
            if str(self.row["TipoAtencion"]).strip().lower() == "residencial"
            else False
        )

    def get_admission_date(self):
        return parse_date(self.row["fechaingreso"])

    def get_discharge_date(self):
        if not pd.isnull(self.row["fechaegreso"]) and self.row["fechaegreso"] != "":
            return parse_date(self.row["fechaegreso"])
        return None

    def get_current(self):
        is_active = str(self.row["vigencia"]).strip().lower() == "si"

        if is_active:
            discharge_date = self.get_discharge_date()
            if discharge_date and discharge_date < datetime.now().date():
                return False
            return True
        return False

    def get_date_project(self):
        fecha_inicio = parse_date(self.row["Fecha de inicio"])
        fecha_egreso = self.get_discharge_date()

        # Validar que ambas fechas sean válidas y comparar
        if fecha_egreso and fecha_inicio and fecha_inicio <= fecha_egreso:
            return fecha_inicio
        return None

    def get_ability_project(self):
        return int(self.row["Capacidad"])

    def get_duration_project(self):
        return int(self.row["duracion en meses"])


class ExcelAdapterApplicants(ExcelBaseAdapter):
    def get_date_of_application(self):
        return parse_date(self.row["Fecha de Solicitud"])

    def get_priority(self):
        return int(self.row["Prioridad"])
