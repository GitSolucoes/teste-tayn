from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

BITRIX_WEBHOOK = "https://marketingsolucoes.bitrix24.com.br/rest/5332/8zyo7yj1ry4k59b5"
CHAT_TRANSFER_URL = "https://seu-dominio.com/change-the-chat-responsible"  # Troque pela variável real
FIELD_RESP_ORIGINAL = "UF_CRM_1746209622228"

logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    deal_id = request.form.get('data[FIELDS][ID]')

    if not deal_id:
        return jsonify({'status': 'erro', 'mensagem': 'ID do negócio não encontrado'}), 400

    response = requests.get(f"{BITRIX_WEBHOOK}/crm.deal.get", params={'id': deal_id})
    result = response.json().get('result', {})
    
    assigned_by = str(result.get('ASSIGNED_BY_ID', ''))
    original_responsible = str(result.get(FIELD_RESP_ORIGINAL, ''))
    contact_id = str(result.get('CONTACT_ID', ''))

    if not original_responsible or original_responsible == 'None':
        update = requests.post(f"{BITRIX_WEBHOOK}/crm.deal.update", json={
            'id': deal_id,
            'fields': {
                FIELD_RESP_ORIGINAL: assigned_by
            }
        }).json()
        logging.info(f"Responsável original registrado: {assigned_by}")
        return jsonify({'status': 'atualizado', 'mensagem': 'Responsável original registrado'})

    elif original_responsible != assigned_by:
        # Atualiza campo com novo responsável
        update = requests.post(f"{BITRIX_WEBHOOK}/crm.deal.update", json={
            'id': deal_id,
            'fields': {
                FIELD_RESP_ORIGINAL: assigned_by
            }
        }).json()
        logging.info(f"Responsável mudou: de {original_responsible} para {assigned_by} — Campo atualizado")

        # Chama a URL de transferência de chat
        transfer_url = f"{CHAT_TRANSFER_URL}?CONTACT_ID={contact_id}&TRANSFER_ID={assigned_by}"
        try:
            transfer_response = requests.get(transfer_url)
            if transfer_response.status_code == 200:
                logging.info(f"Transferência de chat feita com sucesso: {transfer_url}")
            else:
                logging.warning(f"Falha na transferência de chat: {transfer_response.status_code} — {transfer_url}")
        except Exception as e:
            logging.error(f"Erro ao transferir chat: {e}")

        return jsonify({'status': 'mudou', 'mensagem': 'Responsável mudou, campo atualizado e chat transferido'})

    else:
        logging.info("Não mudou a responsabilidade")
        return jsonify({'status': 'sem_mudança', 'mensagem': 'Não mudou a responsabilidade'})


if __name__ == "__main__":
    app.run(port=1400, host="0.0.0.0")
