import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="Portal de Notas", layout="centered")


def parse_filename(filename):
    # Padrão: 2026.01.01_Disciplina.csv
    pattern = r"(\d{4})\.(\d{2})\.(\d{2})_(.*)\.csv"
    match = re.match(pattern, filename)
    if match:
        return {
            "display": f"{match.group(4).replace('_', ' ')} ({match.group(1)}/{match.group(2)} - {match.group(3)}º Bim)",
            "file": filename
        }
    return None


st.title("🎓 Consulta de Notas")

# Listagem automática da pasta data
files = [f for f in os.listdir("data") if f.endswith(".csv")]
options = [parse_filename(f) for f in files if parse_filename(f)]

if not options:
    st.warning("Nenhum arquivo de notas encontrado na pasta /data.")
else:
    choice = st.selectbox("Selecione a Disciplina:", [o["display"] for o in options])
    selected_file = next(o["file"] for o in options if o["display"] == choice)

    ra = st.text_input("Digite seu RA:").strip()

    if st.button("Consultar"):
        df = pd.read_csv(f"data/{selected_file}", dtype={'RA': str})
        result = df[df['RA'] == ra]

        if not result.empty:
            res = result.iloc[0]
            st.success(f"Notas para o RA: {ra}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Final", res.get('Nota Final', '-'))
            c2.metric("Prova", res.get('Nota Prova', '-'))
            c3.metric("Estudo", res.get('Nota Estudo Dirigido', '-'))
        else:
            st.error("RA não localizado nesta disciplina.")