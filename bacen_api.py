# Arquivo: bacen_api.py

import requests
from datetime import datetime
from config import MODALIDADES_BACEN, URL_BASE_BACEN


def buscar_taxa_media_bacen(modalidade_nome: str, data_contrato: str) -> float:
    """
    Busca a taxa de juros média do mercado (BACEN) para uma modalidade e data específicas.

    Args:
        modalidade_nome (str): Nome da modalidade (ex: "Financiamento de Veículo (PF)").
        data_contrato (str): Data de assinatura do contrato (formato DD/MM/AAAA).

    Returns:
        float: A taxa de juros média MENSAL em formato decimal (ex: 0.015 para 1.5%).
    """

    # 1. Obter o código da série
    codigo_serie = MODALIDADES_BACEN.get(modalidade_nome)
    if not codigo_serie:
        print(f"Erro: Modalidade '{modalidade_nome}' não encontrada no mapeamento.")
        return 0.0

    # 2. Formatar a data para a requisição
    # A API do BACEN geralmente precisa do mês/ano de referência (ex: '01/2023').
    try:
        # Converte 'DD/MM/AAAA' para um objeto data
        data_obj = datetime.strptime(data_contrato, '%d/%m/%Y')
        # Formata para 'MM/AAAA'
        mes_ano = data_obj.strftime('%m/%Y')
    except ValueError:
        print("Erro: Formato de data inválido. Use DD/MM/AAAA.")
        return 0.0

    # 3. Construir a URL e Parâmetros da Requisição
    url = URL_BASE_BACEN.replace("{CODIGO_SERIE}", codigo_serie)

    # Parâmetros para buscar o dado específico do mês do contrato
    params = {
        'dataInicial': f'01/{mes_ano}',  # Busca a partir do primeiro dia do mês
        'dataFinal': f'31/{mes_ano}',  # Até o final do mês
        'formato': 'json'
    }

    # 4. Fazer a Requisição à API
    try:
        response = requests.get(url, params=params, timeout=30)  # Timeout de 10 segundos
        response.raise_for_status()  # Lança exceção para erros HTTP 4xx/5xx
        dados = response.json()

        # O resultado vem como uma lista, queremos o último (ou único) valor encontrado para o mês
        if dados:
            # O campo 'valor' é uma string que precisa ser convertida
            taxa_mensal_percentual = float(dados[-1]['valor'].replace(',', '.'))

            # O BACEN retorna a taxa em % (ex: 1.5). Devolvemos em decimal (0.015) para o cálculo
            return taxa_mensal_percentual / 100
        else:
            print(f"Atenção: Taxa média não encontrada para {mes_ano} ({modalidade_nome}).")
            return 0.0

    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar ou receber dados do BACEN: {e}")
        return 0.0
    except Exception as e:
        print(f"Ocorreu um erro inesperado no processamento do JSON: {e}")
        return 0.0


# --- Teste de Módulo (para rodar diretamente no PyCharm) ---
if __name__ == "__main__":
    # Teste 1: Buscar taxa de Veículo em um mês específico
    taxa_veiculo = buscar_taxa_media_bacen(
        modalidade_nome="Financiamento de Veículo (PF)",
        data_contrato="15/05/2023"
    )
    print(f"\nTeste 1 - Taxa BACEN (Veículo): {taxa_veiculo * 100:.2f}% ao mês")

    # Teste 2: Buscar taxa de Crédito Consignado
    taxa_consignado = buscar_taxa_media_bacen(
        modalidade_nome="Crédito Consignado (PF)",
        data_contrato="10/01/2024"
    )
    print(f"Teste 2 - Taxa BACEN (Consignado): {taxa_consignado * 100:.2f}% ao mês")