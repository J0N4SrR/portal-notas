import streamlit as st
import pandas as pd
import os
import re
import unicodedata

st.set_page_config(page_title="Devolutiva do Docente Me. Jonas R", layout="wide", page_icon="🎓")


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

st.title("🎓 Portal Devolutiva do Docente Me. Jonas R.")

files = [f for f in os.listdir("data") if f.endswith(".csv")]
db = [parse_metadata(f) for f in files if parse_metadata(f)]

if not db:
    st.warning("⚠️ Aguardando a publicação das notas pela secretaria.")
else:
    # 1. Filtros em colunas
    f_col1, f_col2, f_col3 = st.columns(3)

    anos = sorted(list(set(d['ano'] for d in db)), reverse=True)
    with f_col1:
        sel_ano = st.selectbox("📅 Ano", anos, index=0)

    semestres = sorted(list(set(d['semestre'] for d in db if d['ano'] == sel_ano)))
    with f_col2:
        sel_sem = st.selectbox("🗓️ Semestre", semestres, index=0)

    bimestres = sorted(list(set(d['bimestre'] for d in db if d['ano'] == sel_ano and d['semestre'] == sel_sem)))
    with f_col3:
        sel_bim = st.selectbox("🎯 Bimestre", [f"{b}º Bim" for b in bimestres], index=0)
    val_bim = sel_bim[0:2]

    disciplinas = [d for d in db if d['ano'] == sel_ano and d['semestre'] == sel_sem and d['bimestre'] == val_bim]
    sel_disc = st.selectbox("📘 Selecione a Disciplina", [d['disciplina'] for d in disciplinas])

    selected_data = next(d for d in disciplinas if d['disciplina'] == sel_disc)
    selected_file = selected_data['file']
    info_path = os.path.join("data", selected_file.replace(".csv", ".md"))

    st.divider()

    # BLOCO INFORMATIVO DE ALTA VISIBILIDADE
    st.markdown("""
        <div style="background-color:#fff3cd; padding:20px; border-radius:10px; border: 3px solid #ffc107; margin-bottom:25px;">
            <h2 style="color:#856404; margin-top:0; text-align:center;">⚠️ LEIA COM ATENÇÃO: INFORMATIVO DA DISCIPLINA ⚠️</h2>
            <hr style="border: 0.5px solid #ffeeba;">
        </div>
    """, unsafe_allow_html=True)

    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.info("Consulte o plano de ensino para detalhes extras.")

    st.markdown("---")

    # RA em destaque centralizado (Hierarquia de Foco)
    c_ra1, c_ra2, c_ra3 = st.columns([1, 2, 1])
    with c_ra2:
        ra_input = st.text_input("👤 Digite seu RA para consultar:", placeholder="Ex: 2026001", max_chars=12).strip()

    if ra_input:
        with st.spinner("Analisando dados..."):
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
                    nota_f_moodle = float(res.get('nota final', 0)) * 0.8
                    nota_p = float(res.get('nota da prova', 0))
                    nota_e = float(res.get('nota do estudo', 0))

                    perc_estudo = (nota_e / 2.5) * 100
                    perc_prova = (nota_p / 7.5) * 100

                    # Centralização e Destaque da Nota (Hierarquia Visual)
                    c_res1, c_res2, c_res3 = st.columns([1, 4, 1])
                    with c_res2:
                        st.markdown(f"""
                        <div style="background-color:#f0f2f6; padding:25px; border-radius:15px; border-left: 8px solid #2e7d32; margin-bottom:20px; text-align: center;">
                            <h3 style="margin:0; color:#1e3d59; font-family:sans-serif;">📊 Nota Final (Máx. 8.0 pts)</h3>
                            <h1 style="margin:10px 0; color:#2e7d32; font-size:64px;">{nota_f_moodle:.2f}</h1>
                            <p style="margin:0; color:#555; font-weight: bold;">⚠️ SOMA OBRIGATÓRIA: Adicione este valor às suas notas de TA e TF.</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.write("#### 📈 PORCENTAGEM DE ACERTO")
                    col1, col2 = st.columns(2)

                    # Neutralidade Absoluta (Apenas cor e porcentagem)
                    def get_status_color(perc):
                        if perc >= 70: return "#2e7d32"  # Verde
                        if perc >= 50: return "#f9a825"  # Amarelo
                        return "#c62828"  # Vermelho

                    with col1:
                        color_e = get_status_color(perc_estudo)
                        st.metric("Acertos (Estudo Dirigido)", f"{perc_estudo:.1f}%")
                        # Sinalização Visual: Semáforo (HTML/CSS colorido)
                        st.markdown(f"""
                            <div style="background-color: #e0e0e0; border-radius: 10px; height: 20px; width: 100%;">
                                <div style="background-color: {color_e}; height: 20px; width: {min(perc_estudo, 100)}%; border-radius: 10px;"></div>
                            </div>
                        """, unsafe_allow_html=True)
                        st.caption(f"Valor: {nota_e:.2f} de 2.5")

                    with col2:
                        color_p = get_status_color(perc_prova)
                        st.metric("Acertos (Prova Presencial)", f"{perc_prova:.1f}%")
                        # Sinalização Visual: Semáforo (HTML/CSS colorido)
                        st.markdown(f"""
                            <div style="background-color: #e0e0e0; border-radius: 10px; height: 20px; width: 100%;">
                                <div style="background-color: {color_p}; height: 20px; width: {min(perc_prova, 100)}%; border-radius: 10px;"></div>
                            </div>
                        """, unsafe_allow_html=True)
                        st.caption(f"Valor: {nota_p:.2f} de 7.5")

                else:
                    st.error("⚠️ **RA não localizado.**\n\nVerifique se o número está correto ou se a **Disciplina/Bimestre** selecionada acima é a correta para este aluno.")
            except Exception as e:
                st.error(f"Erro ao processar dados: {e}")