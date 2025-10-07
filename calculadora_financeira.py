# Arquivo: calculadora_financeira.py

import numpy as np
import numpy_financial as npf  # Importa a biblioteca que contém a função PMT
from typing import List, Dict, Union

# Define a estrutura de uma linha da tabela de amortização
TabelaLinha = Dict[str, float]


def calcular_tabela_price(principal: float, taxa_mensal: float, prazo_meses: int) -> List[TabelaLinha]:
    """
    Gera a tabela de amortização (Sistema PRICE) e calcula o valor da parcela.
    """
    # Usa a função PMT (Payment) do numpy_financial (npf) para calcular o valor fixo da parcela
    parcela_fixa = -npf.pmt(taxa_mensal, prazo_meses, principal)

    tabela = []
    saldo_devedor = principal

    for mes in range(1, prazo_meses + 1):
        # 1. Cálculo dos Juros (sobre o saldo devedor atual)
        juros = saldo_devedor * taxa_mensal

        # 2. Cálculo da Amortização (parte da parcela que abate o principal)
        amortizacao = parcela_fixa - juros

        # 3. Atualização do Saldo Devedor
        saldo_devedor -= amortizacao

        # Ajuste para garantir que o último saldo seja exatamente zero
        if mes == prazo_meses:
            saldo_devedor = 0.0

        tabela.append({
            'mes': float(mes),
            'parcela': parcela_fixa,
            'juros': juros,
            'amortizacao': amortizacao,
            'saldo_devedor': saldo_devedor
        })

    return tabela


def calcular_tabela_sac(principal: float, taxa_mensal: float, prazo_meses: int) -> List[TabelaLinha]:
    """
    Gera a tabela de amortização (Sistema SAC) onde a amortização é constante.
    """
    amortizacao_fixa = principal / prazo_meses

    tabela = []
    saldo_devedor = principal

    for mes in range(1, prazo_meses + 1):
        # 1. Cálculo dos Juros (sobre o saldo devedor atual)
        juros = saldo_devedor * taxa_mensal

        # 2. Cálculo da Parcela
        parcela = amortizacao_fixa + juros

        # 3. Atualização do Saldo Devedor
        saldo_devedor -= amortizacao_fixa

        # Ajuste para garantir que o último saldo seja exatamente zero
        if saldo_devedor < 0.001:  # Pequeno ajuste de precisão
            saldo_devedor = 0.0

        tabela.append({
            'mes': float(mes),
            'parcela': parcela,
            'juros': juros,
            'amortizacao': amortizacao_fixa,
            'saldo_devedor': saldo_devedor
        })

    return tabela


def calcular_abusividade(
        modalidade_nome: str,
        data_contrato: str,
        principal: float,
        taxa_contratada: float,
        prazo_meses: int,
        sistema_amortizacao: str
) -> Dict[str, Union[float, Dict]]:
    """
    Calcula a abusividade comparando o contrato original com o recálculo
    usando duas teses judiciais: Tolerância Zero (Máxima Restituição)
    e Tolerância de 50% (Tese Consolidada - 1.5x Taxa BACEN).
    """
    from bacen_api import buscar_taxa_media_bacen

    # 1. Buscar a taxa de referência do mercado
    taxa_bacen = buscar_taxa_media_bacen(modalidade_nome, data_contrato)

    # 2. Definir a função de cálculo com base no sistema escolhido
    if sistema_amortizacao.upper() == 'PRICE':
        func_calculo = calcular_tabela_price
    elif sistema_amortizacao.upper() == 'SAC':
        func_calculo = calcular_tabela_sac
    else:
        raise ValueError("Sistema de Amortização inválido. Escolha 'PRICE' ou 'SAC'.")

    # 3. Gerar a Tabela ORIGINAL (com a taxa alta/contratada)
    tabela_original = func_calculo(principal, taxa_contratada, prazo_meses)
    juros_total_original = sum(linha['juros'] for linha in tabela_original)

    # -----------------------------------------------------------
    # TESE 1: SEM TOLERÂNCIA (Máxima Restituição)
    # A taxa justa é a própria Taxa BACEN (se a contratada for maior).
    # -----------------------------------------------------------

    # A Taxa Justa (Tese 1) é o menor valor entre a contratada e a Taxa BACEN
    taxa_recalculo_tese1 = min(taxa_contratada, taxa_bacen)

    tabela_recalculada_tese1 = func_calculo(principal, taxa_recalculo_tese1, prazo_meses)
    juros_total_recalculado_tese1 = sum(linha['juros'] for linha in tabela_recalculada_tese1)

    # O abusivo é a diferença total. Se for negativo, é zero (max(0, ...))
    valor_abusivo_tese1 = max(0, juros_total_original - juros_total_recalculado_tese1)

    # -----------------------------------------------------------
    # TESE 2: COM TOLERÂNCIA DE 50% (Tese Judicialmente Consolidada - 1.5x)
    # -----------------------------------------------------------

    TOLERANCIA_JUDICIAL = 0.5  # 50% de margem, o mais aceito pelo STJ (1.5x)
    limite_judicial = taxa_bacen * (1 + TOLERANCIA_JUDICIAL)

    # A Taxa Justa (Tese 2) é o menor valor entre a contratada e o Limite Judicial
    taxa_recalculo_tese2 = min(taxa_contratada, limite_judicial)

    tabela_recalculada_tese2 = func_calculo(principal, taxa_recalculo_tese2, prazo_meses)
    juros_total_recalculado_tese2 = sum(linha['juros'] for linha in tabela_recalculada_tese2)

    # O abusivo é a diferença total.
    valor_abusivo_tese2 = max(0, juros_total_original - juros_total_recalculado_tese2)

    # -----------------------------------------------------------
    # RETORNO FINAL
    # -----------------------------------------------------------

    return {
        'taxa_bacen': taxa_bacen,
        'juros_total_original': juros_total_original,
        'tabela_original': tabela_original,

        'tese_tolerancia_zero': {
            'taxa_recalculada': taxa_recalculo_tese1,
            'juros_total_recalculado': juros_total_recalculado_tese1,
            'valor_abusivo_total': valor_abusivo_tese1,
            'tabela_recalculada': tabela_recalculada_tese1
        },

        'tese_tolerancia_50pc': {
            'taxa_recalculada': taxa_recalculo_tese2,
            'juros_total_recalculado': juros_total_recalculado_tese2,
            'valor_abusivo_total': valor_abusivo_tese2,
            'tabela_recalculada': tabela_recalculada_tese2
        }
    }


# --- Teste de Módulo (para rodar diretamente no PyCharm) ---
if __name__ == "__main__":
    # Exemplo de Contrato (Taxa Contratada ALTA)
    CONTRATO = {
        'modalidade_nome': "Financiamento de Veículo (PF)",
        'data_contrato': "15/05/2023",
        'principal': 50000.00,
        'taxa_contratada': 0.025,  # 2.5% a.m. (simulação de taxa alta)
        'prazo_meses': 36,
        'sistema_amortizacao': 'PRICE'
    }

    print("--- Iniciando Cálculo de Abusividade ---")

    try:
        resultado = calcular_abusividade(**CONTRATO)

        # Resultados:
        print(f"\nModalidade: {CONTRATO['modalidade_nome']}")
        print(f"Taxa Contratada: {CONTRATO['taxa_contratada'] * 100:.2f}% a.m.")
        print(f"Taxa Média BACEN: {resultado['taxa_bacen'] * 100:.2f}% a.m.")
        print("-" * 30)

        # Tese 1
        tese1 = resultado['tese_tolerancia_zero']
        print(f"TESE 1 (Tolerância Zero - Máxima Restituição)")
        print(f"Taxa Recalculada: {tese1['taxa_recalculada'] * 100:.2f}% a.m.")
        print(f"VALOR ABUSIVO: R$ {tese1['valor_abusivo_total']:.2f}")
        print("-" * 30)

        # Tese 2
        tese2 = resultado['tese_tolerancia_50pc']
        print(f"TESE 2 (Tolerância 50% - Tese Judicial Consolidada)")
        print(f"Taxa Recalculada: {tese2['taxa_recalculada'] * 100:.2f}% a.m.")
        print(f"VALOR ABUSIVO: R$ {tese2['valor_abusivo_total']:.2f}")
        print("-" * 30)


    except ValueError as e:
        print(f"Erro no cálculo: {e}")