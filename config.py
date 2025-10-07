# Arquivo: config.py

# Dicionário que mapeia a descrição da modalidade para o Código da Série no BACEN (SGS)
# Estes códigos representam as taxas médias mensais de juros para Pessoas Físicas e Jurídicas.
MODALIDADES_BACEN = {
    "Financiamento de Veículo (PF)": "25488",  # Exemplo de código de série
    "Crédito Pessoal Não-consignado (PF)": "25484", # Exemplo de código de série
    "Crédito Consignado (PF)": "25492",
    "Capital de Giro (PJ)": "20745",
    "Crédito Imobiliário com Taxas de Mercado (PF)": "21763"
    # IMPORTANTE: Você pode adicionar ou verificar mais códigos no site do BACEN
}

# URL base para a API do BACEN (SGS - Sistema Gerenciador de Séries)
# {CODIGO_SERIE} será substituído pela chave do dicionário acima.
URL_BASE_BACEN = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{CODIGO_SERIE}/dados?format=json"