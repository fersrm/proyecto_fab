from utils.helpers import parse_date
from datetime import datetime
import pandas as pd


class ExcelAdapter:
    def __init__(self, row):
        self.row = row

    def get_institution_name(self):
        return str(self.row["institucion"]).strip()

    def get_project_code(self):
        return int(self.row["CodProyecto"])

    def get_project_name(self):
        return str(self.row["proyecto"]).strip()

    def get_rut(self):
        return str(self.row["rut"]).strip()

    def get_sex(self):
        return True if str(self.row["sexo"]).strip().lower() == "m" else False

    def get_birthdate(self):
        return parse_date(self.row["fechanacimiento"])

    def get_name(self):
        return str(self.row["nombres"]).strip()

    def get_last_name_paternal(self):
        return str(self.row["apellido_paterno"]).strip()

    def get_last_name_maternal(self):
        return str(self.row["apellido_materno"]).strip()

    def get_address(self):
        return str(self.row["DireccionNino"]).strip()

    def get_nationality(self):
        return str(self.row["Nacionalidad"]).strip()

    def get_region(self):
        return int(self.row["RegionNino"])

    def get_commune(self):
        return str(self.row["Comuna"]).strip()

    def get_location_key(self):
        return f"{self.get_region()}-{self.get_commune()}"

    def get_solicitor_name(self):
        return str(self.row["SolicitanteIngreso"]).strip()

    def get_legal_quality_name(self):
        return str(self.row["CalidadJuridica"]).strip()

    def get_tribunal_name(self):
        return str(self.row["Tribunal"]).strip()

    def get_proceedings(self):
        return str(self.row["Expediente"]).strip()

    def get_cause_of_entry(self):
        return str(self.row["CausalIngreso_1"]).strip()

    def get_attention(self):
        return (
            True
            if str(self.row["TipoAtencion"]).strip().lower() == "residencial"
            else False
        )

    def get_cod_nna(self):
        return int(self.row["codNNA"])

    def get_admission_date(self):
        return parse_date(self.row["fechaingreso"])

    def get_discharge_date(self):
        return (
            parse_date(self.row["fechaegreso"])
            if not pd.isnull(self.row["fechaegreso"]) and self.row["fechaegreso"] != ""
            else None
        )

    def get_current(self):
        is_active = str(self.row["vigencia"]).strip().lower() == "si"

        if is_active:
            discharge_date = self.get_discharge_date()
            if discharge_date and discharge_date < datetime.now().date():
                return False
            return True
        return False
