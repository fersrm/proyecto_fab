import pandas as pd
from collections import defaultdict
from datetime import datetime


# Para DocumentoApp


def formatea_ordena_fechas(data):
    df = pd.DataFrame(data)
    fecha_ingreso = "date_of_entry"
    fecha_egreso = "date_of_exit"
    formato = "%d/%m/%Y"
    # Convertir las columnas de fecha al formato datetime
    df[fecha_ingreso] = pd.to_datetime(df[fecha_ingreso], format=formato)
    df[fecha_egreso] = pd.to_datetime(df[fecha_egreso], format=formato)

    # Rellenar valores faltantes en "fecha egreso" con la fecha actual
    current_date = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))
    df.fillna({fecha_egreso: current_date}, inplace=True)

    # Ordenar por "fecha ingreso" y reiniciar el índice
    df.sort_values(by=fecha_ingreso, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def calcular_duracion_total(dataframe):
    total_dias = 0
    fecha_inicio = None
    fecha_fin = None
    fecha_ingreso = "date_of_entry"
    fecha_egreso = "date_of_exit"

    for index, row in dataframe.iterrows():
        if fecha_inicio is None or (
            not pd.isnull(row[fecha_ingreso]) and row[fecha_ingreso] > fecha_fin
        ):
            fecha_inicio = row[fecha_ingreso]

        fecha_fin = max(
            row[fecha_egreso],
            fecha_fin if not pd.isnull(fecha_fin) else row[fecha_egreso],
        )

        if index == len(dataframe) - 1 or (
            not pd.isnull(dataframe.loc[index + 1, fecha_ingreso])
            and dataframe.loc[index + 1, fecha_ingreso] > fecha_fin
        ):
            total_dias += (fecha_fin - fecha_inicio).days
            fecha_inicio = None
            fecha_fin = None

    return total_dias


def convierte_anios(dias):
    # Definir las constantes
    dias_por_anio = 365.25
    dias_por_mes = 30.44

    # Calcular años, meses y días
    anios = int(dias / dias_por_anio)
    meses = int((dias % dias_por_anio) / dias_por_mes)
    dias_restantes = int(dias % dias_por_mes)

    return anios, meses, dias_restantes


# Para ReporteApp


def parse_date(date_str):
    date_str = str(date_str).strip()
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]

    for fmt in formats:
        try:
            parsed_date = pd.to_datetime(date_str, format=fmt)
            return parsed_date.date()
        except ValueError:
            continue

    return None


def list_chats(query):
    region_counts = defaultdict(int)

    for nna in query:
        region_num = int(nna["location_FK__region"])
        region_counts[region_num] = nna["count"]

    final_list = []
    for i in range(1, 17):  # Para las 16 regiones
        if i in region_counts:
            final_list.append(region_counts[i])
        else:
            final_list.append(0)

    return final_list
