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

    st.divider()
    with st.expander(f"ℹ️ Informativo de Avaliação: {sel_disc}", expanded=True):
        st.markdown(f"""
        ### Como sua nota é composta:
        Sua dedicação em sala e nos estudos é valorizada em duas etapas que somam **8,0 pontos**:

        *   **🛡️ Estudo Dirigido (2,5 pts):** Seu esforço semanal e base de conhecimento.
        *   **🚀 Prova (7,5 pts):** Sua conquista final e consolidação do aprendizado.

        *O sistema ajusta automaticamente o total para a média institucional (Peso 0.8).*
        """)

    ra_input = st.text_input("🔍 Digite seu RA para ver sua caminhada:", placeholder="Ex: 2026001").strip()

    if ra_input:
        with st.spinner("Preparando seu dashboard..."):
            try:
                df = pd.read_csv(f"data/{selected_file}", sep=None, engine='python', decimal=',')
                df.columns = [normalize_column_name(c) for c in df.columns]

                media_sala_ed = df['nota do estudo'].mean()
                media_sala_prova = df['nota da prova'].mean()

                aluno_data = df[df['ra'] == ra_input]

                if not aluno_data.empty:
                    res = aluno_data.iloc[0]

                    nota_final = float(res.get('nota final', 0))
                    nota_prova = float(res.get('nota da prova', 0))
                    nota_estudo = float(res.get('nota do estudo', 0))

                    percentual_aproveitamento = (nota_final / 8.0) * 100
                    delta_ed = nota_estudo - media_sala_ed
                    delta_prova = nota_prova - media_sala_prova

                    st.markdown(f"### Olá! Veja seu progresso:")

                    col_main1, col_main2 = st.columns(2)
                    col_main1.metric("Resultado Geral (0-8.0)", f"{nota_final:.2f}")
                    col_main2.metric("Aproveitamento da Jornada", f"{percentual_aproveitamento:.1f}%")
                    st.progress(min(nota_final / 8.0, 1.0))

                    st.write("#### Detalhamento das Etapas")
                    col_ed, col_prova = st.columns(2)

                    with col_ed:
                        st.write(f"**Estudo Dirigido** ({nota_estudo:.2f} de 2.5)")
                        st.progress(min(nota_estudo / 2.5, 1.0))
                        st.metric("Diferença vs Sala", f"{delta_ed:+.2f}", delta_color="normal")

                    with col_prova:
                        st.write(f"**Prova Presencial** ({nota_prova:.2f} de 7.5)")
                        st.progress(min(nota_prova / 7.5, 1.0))
                        st.metric("Diferença vs Sala", f"{delta_prova:+.2f}", delta_color="normal")

                    st.divider()
                    if nota_final >= 7.0:
                        st.success(
                            "🌟 **Excelente!** Você demonstrou um domínio admirável do conteúdo. Continue com essa dedicação!")
                    elif nota_final >= 5.0:
                        st.info(
                            "✨ **Bom caminho!** Você conquistou uma base sólida. Que tal focar nos pontos da prova para brilhar ainda mais?")
                    else:
                        st.warning(
                            "⚠️ **Atenção:** Esta etapa serve como um mapa para onde precisamos focar mais. Vamos reforçar os estudos dirigidos juntos?")
                else:
                    st.error("❌ RA não localizado. Verifique se o número está correto.")
            except Exception as e:
                st.error(f"Erro ao carregar dashboard: {e}")