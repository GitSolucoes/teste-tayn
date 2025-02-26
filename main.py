from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import time
import random
from datetime import datetime, timedelta, timezone
import logging

app = Flask(__name__)

# Load environment variables
load_dotenv()
CODIGO_BITRIX = os.getenv('CODIGO_BITRIX')
CODIGO_BITRIX_STR = os.getenv('CODIGO_BITRIX_STR')
PROFILE = os.getenv('PROFILE')
BASE_URL_API_BITRIX = os.getenv('BASE_URL_API_BITRIX')

BITRIX_WEBHOOK_URL = f"{BASE_URL_API_BITRIX}/{PROFILE}/{CODIGO_BITRIX}/bizproc.workflow.start"

def make_request_with_retry(url, data, max_retries=3, retry_delay=5):
    """Faz a requisição e tenta novamente em caso de erro (404, 400, 500, etc.)."""
    for attempt in range(max_retries):
        try:
            print(f"🕒 Tentativa {attempt + 1} de {max_retries} para {url}")
            response = requests.post(url, json=data)
            # Verifica se a resposta tem status 200
            response.raise_for_status()
            print("✅ Requisição bem-sucedida!")
            return response  # Retorna a resposta se for bem-sucedida
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erro na tentativa {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Aguardando {retry_delay} segundos antes de tentar novamente...")
                time.sleep(retry_delay)
            else:
                print("❌ Máximo de tentativas atingido. Falha na requisição.")
    return None  # Retorna None se todas as tentativas falharem

def update_card_bitrix(card_id, name_of_field, value):
    url = f"{BASE_URL_API_BITRIX}/{PROFILE}/{CODIGO_BITRIX}/crm.deal.update"
    data = {
        'id': card_id,
        'fields': {
            name_of_field: value
        }
    }
    if value is None:
        print('⚠️ A variável "value" está nula ⚠️')
        return -1

    response = make_request_with_retry(url, data)
    if response and response.status_code == 200:
        print(f"✅ Campo '{name_of_field}' atualizado com sucesso.")
        return True
    else:
        print("❌ Falha ao atualizar o campo.")
        if response is not None:
            print(response.text)
        return None

def convert_for_gmt_minus_3(date_from_bitrix):
    hour_obj = datetime.fromisoformat(date_from_bitrix)
    hour_sub = hour_obj - timedelta(hours=6)
    new_hour_formated = hour_sub.isoformat()
    return new_hour_formated


@app.route('/update_deal', methods=['POST'])
def update_deal():
    deal_id = request.args.get("deal_id")
    random_value = request.args.get("value")
    print(f" Mudança Feita {deal_id}")
    logging.info(f" Mudança Feita {deal_id}")
    
    if not deal_id:
        return jsonify({"error": "deal_id é obrigatório"}), 400
    
    if random_value is None:
        random_value = random.randint(100000, 999999)
    
    url = "https://marketingsolucoes.bitrix24.com.br/rest/5332/s3wx07gjcfywp51q/crm.deal.update"
    params = {
        "ID": deal_id,
        "Fields[UF_CRM_1700661314351]": random_value
    }
    
    response = requests.post(url, params=params)
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1400)
