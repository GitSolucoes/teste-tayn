from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

BITRIX_WEBHOOK = "https://marketingsolucoes.bitrix24.com.br/rest/5332/8zyo7yj1ry4k59b5"
FIELD_RESP_ORIGINAL = "UF_CRM_1746209622228"

logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    deal_id = data.get('data', {}).get('FIELDS', {}).get('ID')

    if not deal_id:
        return jsonify({'status': 'erro', 'mensagem': 'ID do negócio não encontrado'}), 400

    # Consulta os dados do negócio
    deal = requests.get(f"{BITRIX_WEBHOOK}/crm.deal.get", params={'id': deal_id}).json().get('result', {})
    
    assigned_by = str(deal.get('ASSIGNED_BY_ID'))
    original_responsible = str(deal.get(FIELD_RESP_ORIGINAL, ''))

    if not original_responsible or original_responsible == 'None':
        # Atualiza o campo personalizado com o responsável atual
        update = requests.post(f"{BITRIX_WEBHOOK}/crm.deal.update", json={
            'id': deal_id,
            'fields': {
                FIELD_RESP_ORIGINAL: assigned_by
            }
        }).json()
        logging.info(f"Responsável original registrado: {assigned_by}")
        return jsonify({'status': 'atualizado', 'mensagem': 'Responsável original registrado'})

    elif original_responsible != assigned_by:
        logging.info(f"Responsável mudou: de {original_responsible} para {assigned_by}")
        return jsonify({'status': 'mudou', 'mensagem': 'Responsável mudou'})

    else:
        logging.info("Não mudou a responsabilidade")
        return jsonify({'status': 'sem_mudança', 'mensagem': 'Não mudou a responsabilidade'})

if __name__ == '__main__':
    app.run(port=1400, debug=True)
