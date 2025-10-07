# Arquivo: main_app.py

import streamlit as st
import pandas as pd
# Importamos as funções de cálculo básicas para o recálculo da tese personalizada
from calculadora_financeira import calcular_abusividade, calcular_tabela_price, calcular_tabela_sac
from config import MODALIDADES_BACEN
from typing import Dict, Union


# --- FUNÇÃO DE FORMATAÇÃO MONETÁRIA BRASILEIRA (R$ X.XXX,XX) ---
def formatar_moeda_br(valor):
    """Formata um valor float para o padrão monetário brasileiro como string."""
    if isinstance(valor, (int, float)):
        # Usa f-string com separador de milhar nativo (,) e troca a vírgula por ponto (milhar)
        # e o ponto por vírgula (decimal)
        return f"R$ {valor:,.2f}".replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", ".")
    return valor


# --- FIM FUNÇÃO DE FORMATAÇÃO ---

# --- Configuração da Página ---
st.set_page_config(
    page_title="Calculadora de Juros Abusivos",
    layout="wide"  # Layout wide para acomodar 3 colunas
)

# --- Título e Descrição ---
st.title("⚖️ Calculadora Revisional de Juros")
st.markdown(
    "Use esta ferramenta para analisar contratos de crédito e identificar o valor dos juros abusivos cobrados acima da média de mercado (BACEN), simulando as principais teses judiciais.")

# --- Área de Input (Formulário) ---
st.header("Dados do Contrato")

# Variáveis definidas antes do formulário para evitar erros de escopo
principal = 0.0
taxa_contratada = 0.0
tolerancia_personalizada = 0.0

with st.form("form_contrato"):
    # 1. Opções de Modalidade (Usando o dicionário do config.py)
    modalidade = st.selectbox(
        "Modalidade de Crédito (Referência BACEN):",
        options=list(MODALIDADES_BACEN.keys()),
        index=0
    )

    # 2. Dados Críticos (Contrato)
    col1, col2 = st.columns(2)
    with col1:
        data_contrato = st.text_input("Data da Contratação (DD/MM/AAAA):", value="15/05/2023")

        taxa_contratada_input = st.number_input(
            "Taxa de Juros Mensal Contratada (%):",
            min_value=0.01,
            max_value=10.0,
            value=2.80,  # Valor de teste
            step=0.1,
            format="%.2f",
            key="taxa_input"
        )

        # --- SOLUÇÃO PARA FORMATO BRASILEIRO: st.text_input + Limpeza ---
        principal_string_input = st.text_input(
            "Valor Principal Financiado (R$):",
            value="60.000,00",  # Valor de teste
            help="Use o padrão brasileiro: ponto para milhar e vírgula para decimal (ex: 60.000,00)",
            key="principal_string_input"
        )
        # --- FIM SOLUÇÃO ---

    with col2:
        prazo_meses = st.number_input(
            "Prazo Total do Contrato (Meses):",
            min_value=1,
            max_value=360,
            value=48,  # Valor de teste
            step=1
        )
        sistema_amortizacao = st.selectbox(
            "Sistema de Amortização:",
            options=['PRICE', 'SAC'],
            index=0
        )
        # CAMPO DE TOLERÂNCIA PERSONALIZADA
        tolerancia_personalizada_input = st.number_input(
            "Tolerância Judicial Customizada (% sobre BACEN):",
            min_value=0,
            max_value=100,
            value=30,  # Valor de teste
            step=5,
            help="Defina um percentual de tolerância diferente para testar outras teses judiciais."
        )

    # ----------------------------------------------------
    # 3. CAMPO DE UPLOAD DO ARQUIVO PDF (NOVO)
    # ----------------------------------------------------
    st.markdown("---")

    arquivo_pdf = st.file_uploader(
        "Upload do Contrato (PDF) para Análise de IA (Futuro)",
        type=['pdf'],
        help="A função de leitura automática do contrato será implementada em breve."
    )

    # ----------------------------------------------------

    # 4. Botão de Submissão
    submitted = st.form_submit_button("Calcular Abusividade")

# --- TRATAMENTO DOS DADOS FORA DO FORMULÁRIO (DEPOIS DA SUBMISSÃO) ---

# Converte taxa percentual para decimal (2.80 -> 0.028)
taxa_contratada = taxa_contratada_input / 100
# Converte tolerância percentual para decimal (30 -> 0.30)
tolerancia_personalizada = tolerancia_personalizada_input / 100

# TRATAMENTO DO VALOR PRINCIPAL (Vírgula para Ponto)
# Exemplo: "60.000,00" -> "60000.00"
principal_limpa = principal_string_input.replace('.', '').replace(',', '.')

try:
    principal = float(principal_limpa)
except ValueError:
    if submitted:
        st.error(
            "Formato do **Valor Principal** inválido. Certifique-se de usar pontos e vírgulas corretamente (ex: 60.000,00).")
    # Define 0 para evitar erro de inicialização se a conversão falhar
    principal = 0.0

# --- Área de Resultados ---
if submitted and principal > 0:
    try:
        st.subheader("📊 Resultados da Análise")

        # 1. Chamar a função de cálculo (retorna 0% e 50%)
        resultado = calcular_abusividade(
            modalidade_nome=modalidade,
            data_contrato=data_contrato,
            principal=principal,
            taxa_contratada=taxa_contratada,
            prazo_meses=prazo_meses,
            sistema_amortizacao=sistema_amortizacao
        )

        taxa_bacen = resultado['taxa_bacen']
        juros_total_original = resultado['juros_total_original']

        if taxa_bacen == 0.0:
            st.error(
                "Não foi possível obter a Taxa Média do BACEN para a modalidade e data informadas. Verifique a conexão com a internet ou os dados.")
            st.stop()

        # Exibir Resumo Geral
        col_resumo_1, col_resumo_2, col_vazio = st.columns(3)
        col_resumo_1.metric("Taxa Contratada", f"{taxa_contratada * 100:.2f}% a.m.")
        col_resumo_2.metric("Taxa Média BACEN", f"{taxa_bacen * 100:.2f}% a.m.")

        if taxa_contratada <= taxa_bacen * 1.5:
            st.success(
                "🎉 Pela tese judicial mais aceita (tolerância de 50%), a taxa do contrato está **dentro** do limite legal.")
        else:
            st.error(
                "🚨 **ABUSIVIDADE COMPROVADA!** A taxa contratada **excede** o limite de tolerância judicial (BACEN + 50%).")

        st.markdown("---")

        # 2. CALCULAR A TESE PERSONALIZADA (usando funções importadas)
        func_calculo = calcular_tabela_price if sistema_amortizacao.upper() == 'PRICE' else calcular_tabela_sac

        # Limite Judicial Personalizado: Taxa BACEN * (1 + Tolerância%)
        limite_personalizado = taxa_bacen * (1 + tolerancia_personalizada)

        taxa_recalculo_personalizada = min(taxa_contratada, limite_personalizado)

        tabela_recalculada_personalizada = func_calculo(principal, taxa_recalculo_personalizada, prazo_meses)
        juros_total_recalculado_personalizada = sum(linha['juros'] for linha in tabela_recalculada_personalizada)

        valor_abusivo_personalizado = max(0, juros_total_original - juros_total_recalculado_personalizada)

        tese_personalizada = {
            'taxa_recalculada': taxa_recalculo_personalizada,
            'valor_abusivo_total': valor_abusivo_personalizado,
        }

        # 3. Exibir Resultados das Três Teses em 3 COLUNAS
        col_tese_0, col_tese_50, col_tese_custom = st.columns(3)

        # Dicionários de resultados (obtidos de calculadora_financeira.py)
        tese_0 = resultado['tese_tolerancia_zero']
        tese_50 = resultado['tese_tolerancia_50pc']

        # --- COLUNA TESE 1 (Tolerância Zero) ---
        with col_tese_0:
            st.subheader("1. Tese Máxima Restituição")
            st.markdown("**(Tolerância 0% - Tese Agressiva)**")

            st.metric(
                "Valor Abusivo (0%)",
                f"R$ {tese_0['valor_abusivo_total']:.2f}",
                delta="Juros a Mais" if tese_0['valor_abusivo_total'] > 0 else None
            )
            st.caption(f"Taxa Justa: `{tese_0['taxa_recalculada'] * 100:.2f}% a.m.`")

        # --- COLUNA TESE 2 (Tolerância 50%) ---
        with col_tese_50:
            st.subheader("2. Tese Judicial Consolidada")
            st.markdown("**(Tolerância 50% - Tese Segura/STJ)**")

            st.metric(
                "Valor Abusivo (50%)",
                f"R$ {tese_50['valor_abusivo_total']:.2f}",
                delta="Juros a Mais" if tese_50['valor_abusivo_total'] > 0 else None
            )
            st.caption(f"Taxa Justa: `{tese_50['taxa_recalculada'] * 100:.2f}% a.m.`")

        # --- COLUNA TESE 3 (Tolerância Personalizada) ---
        with col_tese_custom:
            st.subheader("3. Tese Personalizada")
            st.markdown(f"**(Tolerância {tolerancia_personalizada_input}%)**")

            st.metric(
                f"Valor Abusivo ({tolerancia_personalizada_input}%)",
                f"R$ {tese_personalizada['valor_abusivo_total']:.2f}",
                delta="Juros a Mais" if tese_personalizada['valor_abusivo_total'] > 0 else None
            )
            st.caption(f"Taxa Justa: `{tese_personalizada['taxa_recalculada'] * 100:.2f}% a.m.`")

        st.markdown("---")

        # 4. Tabela Detalhada (mantendo a comparação Tese 50% vs Original)
        st.subheader("Detalhe da Amortização (Tabela Comparativa)")

        df_original = pd.DataFrame(resultado['tabela_original'])
        df_recalculada_50 = pd.DataFrame(tese_50['tabela_recalculada'])

        # Renomear e combinar colunas
        df_original = df_original.rename(columns={'parcela': 'Parc. Original', 'juros': 'Juros Original'})
        df_recalculada_50 = df_recalculada_50.rename(columns={'parcela': 'Parc. Tese 50%', 'juros': 'Juros Tese 50%'})

        df_final = pd.DataFrame()
        df_final['Mês'] = df_original['mes'].astype(int)
        df_final['Parc. Original'] = df_original['Parc. Original']
        df_final['Juros Original'] = df_original['Juros Original']

        df_final['Parc. Tese 50%'] = df_recalculada_50['Parc. Tese 50%']
        df_final['Juros Tese 50%'] = df_recalculada_50['Juros Tese 50%']
        df_final['Diferença Parcela'] = df_original['Parc. Original'] - df_recalculada_50['Parc. Tese 50%']

        # --- NOVO BLOCO DE FORMATAÇÃO (APLICA FORMATO BRASILEIRO R$) ---
        colunas_monetarias = [
            'Parc. Original',
            'Juros Original',
            'Parc. Tese 50%',
            'Juros Tese 50%',
            'Diferença Parcela'
        ]

        # Aplica a função de formatação para todas as colunas monetárias
        for col in colunas_monetarias:
            df_final[col] = df_final[col].apply(formatar_moeda_br)
        # --- FIM NOVO BLOCO ---

        st.dataframe(
            df_final,  # Passa o DataFrame já formatado como string
            use_container_width=True,
            # Não é mais necessário usar column_config.NumberColumn, pois os dados são strings formatadas
        )

        st.caption(
            "A tabela compara a Parcela Original com a Parcela Recalculada, usando a Tese Judicial Consolidada (Taxa BACEN + 50% de Tolerância).")

    except ValueError as e:
        st.error(f"Erro nos Dados do Contrato: {e}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado no cálculo. Detalhes: {e}")