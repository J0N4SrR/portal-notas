import streamlit as st
import pandas as pd
import os
import re
import unicodedata

st.set_page_config(page_title="Portal Acadêmico", layout="centered", page_icon="📊")


def normalize_column_name(name):
    name = str(name).strip().lower()
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    return name


def parse_metadata(filename):
    pattern = r"(\d{4})\.(\d{2})\.(\d{2})_(.*)\.csv"
    match = re.match(pattern, filename)
    if match:
        return {
            "ano": match.group(1),
            "semestre": match.group(2),
            "bimestre": match.group(3),
            "disciplina": match.group(4).replace('_', ' '),
            "file": filename
        }
    return None


if not os.path.exists("data"):
    os.makedirs("data", exist_ok=True)

st.title("🎓 Portal de Resultados")

files = [f for f in os.listdir("data") if f.endswith(".csv")]
db = [parse_metadata(f) for f in files if parse_metadata(f)]

if not db:
    st.warning("Nenhum registro encontrado no sistema.")
else:
    anos = sorted(list(set(d['ano'] for d in db)), reverse=True)
    sel_ano = st.selectbox("📅 Ano", anos)

    semestres = sorted(list(set(d['semestre'] for d in db if d['ano'] == sel_ano)))
    sel_sem = st.selectbox("🗓️ Semestre", semestres)

    bimestres = sorted(list(set(d['bimestre'] for d in db if d['ano'] == sel_ano and d['semestre'] == sel_sem)))
    sel_bim = st.selectbox("🚩 Bimestre", [f"{b}º Bimestre" for b in bimestres])
    val_bim = sel_bim[0:2]

    disciplinas = [d for d in db if d['ano'] == sel_ano and d['semestre'] == sel_sem and d['bimestre'] == val_bim]
    sel_disc = st.selectbox("📘 Disciplina", [d['disciplina'] for d in disciplinas])

    selected_file = next(d['file'] for d in disciplinas if d['disciplina'] == sel_disc)

    st.divider()
    with st.expander(f"ℹ️ Informativo: {sel_disc}", expanded=True):
        st.markdown(f"""
        Esta nota compõe **8,0 pontos** da sua média final no Moodle. 
        O cálculo utiliza peso **0,8** sobre a nota do professor (0-10).
        """)

    ra_input = st.text_input("🔍 Digite seu RA:", placeholder="Ex: 2026001").strip()

    if ra_input:
        try:
            df = pd.read_csv(f"data/{selected_file}", sep=None, engine='python', decimal=',')
            df.columns = [normalize_column_name(c) for c in df.columns]

            aluno_data = df[df['ra'] == ra_input]

            if not aluno_data.empty:
                res = aluno_data.iloc[0]

                nota_final = float(res.get('nota final', 0))
                nota_prova = float(res.get('nota da prova', 0))
                nota_estudo = float(res.get('nota do estudo', 0))

                media_sala_ed = df['nota do estudo'].mean()
                media_sala_prova = df['nota da prova'].mean()

                st.success(f"### Olá!")

                c1, c2 = st.columns(2)
                c1.metric("Sua Nota Final (Peso 0.8)", f"{nota_final:.2f}")
                c2.metric("Aproveitamento Total", f"{(nota_final / 8.0) * 100:.1f}%")

                st.write("#### Comparativo com a Turma")
                col_ed, col_prova = st.columns(2)

                with col_ed:
                    delta_ed = nota_estudo - media_sala_ed
                    st.metric("Seu Estudo Dirigido", f"{nota_estudo:.2f}", delta=f"{delta_ed:.2f}")
                    st.progress(min(nota_estudo / 2.5, 1.0))

                with col_prova:
                    delta_p = nota_prova - media_sala_prova
                    st.metric("Sua Prova", f"{nota_prova:.2f}", delta=f"{delta_p:.2f}")
                    st.progress(min(nota_prova / 7.5, 1.0))
            else:
                st.error("RA não localizado.")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")