import streamlit as st
import pandas as pd
import os
import re
import unicodedata

st.set_page_config(page_title="Portal Acadêmico", layout="centered", page_icon="🎓")


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
    st.warning("⚠️ Aguardando a publicação das notas pela secretaria.")
else:
    anos = sorted(list(set(d['ano'] for d in db)), reverse=True)
    sel_ano = st.selectbox("📅 Selecione o Ano", anos)

    semestres = sorted(list(set(d['semestre'] for d in db if d['ano'] == sel_ano)))
    sel_sem = st.selectbox("🗓️ Selecione o Semestre", semestres)

    bimestres = sorted(list(set(d['bimestre'] for d in db if d['ano'] == sel_ano and d['semestre'] == sel_sem)))
    sel_bim = st.selectbox("🚩 Selecione o Bimestre", [f"{b}º Bimestre" for b in bimestres])
    val_bim = sel_bim[0:2]

    disciplinas = [d for d in db if d['ano'] == sel_ano and d['semestre'] == sel_sem and d['bimestre'] == val_bim]
    sel_disc = st.selectbox("📘 Selecione a Disciplina", [d['disciplina'] for d in disciplinas])

    selected_data = next(d for d in disciplinas if d['disciplina'] == sel_disc)
    selected_file = selected_data['file']
    info_path = os.path.join("data", selected_file.replace(".csv", ".md"))

    st.divider()

    with st.expander(f"ℹ️ Entenda como sua nota é calculada em {sel_disc}", expanded=False):
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.info("Consulte o informativo oficial para detalhes sobre a composição da nota.")

    ra_input = st.text_input("🔍 Digite seu RA para consultar:", placeholder="Ex: 2026001").strip()

    if ra_input:
        with st.spinner("Buscando suas notas..."):
            try:
                df = pd.read_csv(os.path.join("data", selected_file), sep=None, engine='python', decimal=',', dtype=str)
                df.columns = [normalize_column_name(c) for c in df.columns]
                df['ra'] = df['ra'].str.strip()

                for col in ['nota do estudo', 'nota da prova', 'nota final']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce').fillna(0)

                aluno_data = df[df['ra'] == ra_input]

                if not aluno_data.empty:
                    res = aluno_data.iloc[0]

                    # Aplicação do peso institucional 0.8 sobre a nota bruta final
                    nota_bruta_final = float(res.get('nota final', 0))
                    nota_f_moodle = nota_bruta_final * 0.8

                    nota_p = float(res.get('nota da prova', 0))
                    nota_e = float(res.get('nota do estudo', 0))

                    perc_estudo = (nota_e / 2.5) * 100
                    perc_prova = (nota_p / 7.5) * 100

                    st.success("### ✅ Resultados Localizados")

                    st.container(border=True).metric(
                        label="SUA NOTA NO MOODLE (Peso 0.8 aplicado)",
                        value=f"{nota_f_moodle:.2f} Pts"
                    )
                    st.warning(
                        "⚠️ **SOMA OBRIGATÓRIA:** Pegue o valor acima e **some** com suas notas de **TA e TF** do Moodle para saber sua média final de 10 pontos.")

                    st.write("---")
                    st.write("#### 📊 Aproveitamento de Conhecimento (% de acertos)")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Estudo Dirigido")
                        st.metric("Acertos", f"{perc_estudo:.1f}%")
                        st.progress(min(perc_estudo / 100, 1.0))
                        st.caption(f"Valor alcançado: {nota_e:.2f} de 2.5")

                    with col2:
                        st.subheader("Prova Presencial")
                        st.metric("Acertos", f"{perc_prova:.1f}%")
                        st.progress(min(perc_prova / 100, 1.0))
                        st.caption(f"Valor alcançado: {nota_p:.2f} de 7.5")

                else:
                    st.error("❌ RA não localizado. Verifique se selecionou o Bimestre e Disciplina corretos.")
            except Exception as e:
                st.error(f"Erro ao processar cálculos: {e}")