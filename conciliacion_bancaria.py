
import pandas as pd
import pdfplumber

password_pdf = "contraseña"
ruta_pdf = "extracto" # ubicacion en documentos

# Lista temporal para guardar todas las filas de todas las páginas
todas_las_filas = []

with pdfplumber.open(ruta_pdf, password=password_pdf) as pdf:
  for pagina in pdf.pages:
    tabla = pagina.extract_table()
    if tabla:
# Añadimos las filas de esta página a nuestra lista global
      todas_las_filas.extend(tabla)

# Separamos los encabezados (la primera fila) del resto de los datos
encabezados = todas_las_filas[0]
datos = todas_las_filas[1:]

# Creamos el DataFrame de Pandas
df_extracto = pd.DataFrame(datos, columns=encabezados)

# Eliminamos las filas repetidas donde la columna 'Fecha del movimiento' dice el texto del encabezado
df_extracto = df_extracto[
    df_extracto["Fecha del movimiento"] != "Fecha del movimiento"
]

# Resetear el índice para que quede ordenado del 0 en adelante
df_extracto = df_extracto.reset_index(drop=True)

#  Limpiamos la columna 'Valor' para quitar $, comas y convertirla a tipo float(numerica)
df_extracto["Valor"] = (
    df_extracto["Valor"]
    .astype(str)
    .str.replace("$", "", regex=False)  # Quita el símbolo de pesos
    .str.replace(",", "", regex=False)  # Quita las comas de miles
    .str.strip()  # Elimina espacios vacíos
    .astype(float)  # Convierte finalmente a número decimal
)

#  limpiar la columna 'Saldo' para quitar $, comas y convertirla a tipo float(numerica)
df_extracto["Saldo"] = (
    df_extracto["Saldo"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
    .astype(float)
)

# Agregamos el libro auxiliar de banco.
ruta = "libro_axuliar_banco" # ubicion en documentos
libro_auxiliar=pd.read_excel(ruta)


#  Asegurar que las columnas sean numéricas y rellenar los vacíos (NaN) con 0
libro_auxiliar["Debito"] = (
    pd.to_numeric(libro_auxiliar["Debito"], errors="coerce").fillna(0)
)
libro_auxiliar["Credito"] = (
    pd.to_numeric(libro_auxiliar["Credito"], errors="coerce").fillna(0)
)

# Calcular el valor neto del auxiliar para homologarlo con el extracto del banco:
# Débito (entradas de dinero) = positivo (+)
# Crédito (salidas de dinero) = negativo (-)
libro_auxiliar["Valor_Auxiliar"] = (
    libro_auxiliar["Debito"] - libro_auxiliar["Credito"]
)

# Realizamos el cruce (merge) con dataframe del extracto bancario (df_extracto)
conciliacion = pd.merge(
    df_extracto,
    libro_auxiliar,
    left_on=["Fecha del movimiento", "Valor"],
    right_on=["Fecha del movimiento", "Valor_Auxiliar"],
    how="outer",
    indicator=True,
)

# Traducimos los nombres en inglés a español contable
conciliacion["Estado_Conciliacion"] = conciliacion["_merge"].map(
    {
        "both": "Conciliado (Cuadra en Banco y Siigo)",
        "left_only": "Solo en Banco (Falta registrar en Siigo)",
        "right_only": "Solo en Siigo (Pendiente de reflejar en Banco)",
    }
)

# Muestra de resumen en consola
print("--- INFORME DE CONCILIACIÓN BANCARIA ---")
print(conciliacion["Estado_Conciliacion"].value_counts())


# Exportar el resultado detallado a un archivo de Excel para revisión final (Documentos)
conciliacion.to_excel("resultado_conciliacion_final.xlsx", index=False)
print(
    "\n¡Proceso terminado! El archivo 'resultado_conciliacion_final.xlsx' fue"
    " guardado con éxito."
)

