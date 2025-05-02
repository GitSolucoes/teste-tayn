from flask import Flask, request, jsonify
import requests
import logging
import time
app = Flask(__name__)

BITRIX_WEBHOOK = "https://marketingsolucoes.bitrix24.com.br/rest/5332/8zyo7yj1ry4k59b5"
CHAT_TRANSFER_URL = "https://grupo--solucoes-teste-tayn.rvc6im.easypanel.host/change-the-chat-channel/"  
FIELD_RESP_ORIGINAL = "UF_CRM_1746209622228"

logging.basicConfig(level=logging.INFO)

def extrair_numero(string):
    return string.split("_")[-1]

# ROTA PARA TRANSFERENCIA DE BATE-PAPO NA BITRIX BATENDO COM RESPONSAVEL INDO PRA FILA
@app.route("/change-the-chat-channel/", methods=["POST"])
def change_the_chat_channel():
    CONTACT_ID = request.args.get("CONTACT_ID")
    QUEUE_ID = request.args.get("QUEUE_ID")

    if not CONTACT_ID or not QUEUE_ID:
        return (
            jsonify(
                {
                    "error": "CONTACT_ID and QUEUE_ID must be provided in the URL parameters"
                }
            ),
            400,
        )

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/8zyo7yj1ry4k59b5"
    url = f"{base_url}/imopenlines.crm.chat.getLastId?CRM.ENTITY_TYPE=CONTACT&CRM_ENTITY={CONTACT_ID}"

    print(f"URL: {url}")

    response = requests.post(url)
    time.sleep(2)

    if response.status_code == 200:
        datajson = response.json()
        id_chat = datajson["result"]

        url2 = f"{base_url}/imopenlines.operator.transfer?CHAT_ID={id_chat}&QUEUE_ID={QUEUE_ID}"
        print(f"url que esta sendo postada: {url2}")
        response2 = requests.post(url2)

        if response2.status_code == 200:
            return "New responsible approved"
        else:
            return f"No responsible approved: {response2.text}"
    else:
        return f"Failed to get chat ID: {response.text} - {url}"


# NOVA ROTA PARA TRANSFERENCIA DE BATE-PAPO COM RESPONSÁVEL
@app.route("/change-the-chat-responsible/", methods=["POST"])
def change_the_chat_responsability():
    CONTACT_ID = request.args.get("CONTACT_ID")
    TRANSFER_ID = request.args.get("TRANSFER_ID")

    if not CONTACT_ID or not TRANSFER_ID:
        return (
            jsonify(
                {
                    "error": "CONTACT_ID and TRANSFER_ID must be provided in the URL parameters"
                }
            ),
            400,
        )

    TRANSFER_ID = extrair_numero(TRANSFER_ID)

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/8zyo7yj1ry4k59b5"
    url = f"{base_url}/imopenlines.crm.chat.getLastId?CRM.ENTITY_TYPE=CONTACT&CRM_ENTITY={CONTACT_ID}"

    response = requests.post(url)
    time.sleep(2)

    if response.status_code == 200:
        datajson = response.json()
        id_chat = datajson["result"]

        url2 = f"{base_url}/imopenlines.operator.transfer?CHAT_ID={id_chat}&TRANSFER_ID={TRANSFER_ID}"
        response2 = requests.post(url2)

        if response2.status_code == 200:
            return "New responsible approved"
        else:
            return f"No responsible approved: {response2.text}"
    else:
        return f"Failed to get chat ID: {response.text}"

# ROTA PARA TRANSFERENCIA DE BATE-PAPO NA BITRIX PARA OUTRO CARD

@app.route("/finalize-chat/", methods=["POST"])
def finalize_chat():
    DEAL_ID = request.args.get("DEAL_ID")

    if not DEAL_ID:
        return jsonify({"error": "DEAL_ID must be provided in the URL parameters"}), 400

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/8zyo7yj1ry4k59b5"
    url_get_chat = f"{base_url}/imopenlines.crm.chat.get?CRM_ENTITY_TYPE=DEAL&CRM_ENTITY={DEAL_ID}"

    response = requests.get(url_get_chat)
    time.sleep(2)

    if response.status_code == 200:
        datajson = response.json()
        print("Response JSON:", datajson)  

       
        if "result" in datajson and isinstance(datajson["result"], list) and len(datajson["result"]) > 0:
            chat_id = datajson["result"][0]["CHAT_ID"]  

            url_finish_chat = f"{base_url}/imopenlines.operator.another.finish?CHAT_ID={chat_id}"
            response2 = requests.post(url_finish_chat)

            if response2.status_code == 200:
                return jsonify({"status": "success", "message": "Chat finalized successfully"})
            else:
                return jsonify({"error": "Failed to finalize chat", "details": response2.text}), 500
        else:
            return jsonify({"error": "CHAT_ID not found in response"}), 404
    else:
        return jsonify({"error": "Failed to get CHAT_ID", "details": response.text}), 500




@app.route("/transfer-chat-between-deals/", methods=["POST", "GET"])
def transfer_chat_between_deals():
    #pegar o id do card antigo
    from_id = request.args.get("from_deal_id", "Não informado")
    #e ir para o outro
    to_id = request.args.get("to_deal_id", "Não informado")

    if from_id == "Não informado":
        return {"status": "error", "message": "ID do deal não informado!"}, 400

    if to_id == "Não informado":
        return {"status": "error", "message": "ID do deal não informado!"}, 400

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/8zyo7yj1ry4k59b5"

    url_get_activity = f"{base_url}/crm.activity.list?filter[OWNER_ID]={from_id}"

    res = requests.get(url_get_activity)

    if len(res.json()["result"]) < 1:
        return {
            "status": "error",
            "message": f"Não há atividades para serem movidas no card {from_id}",
        }, 404

    activity_id = res.json()["result"][0]["ID"]

    url_move = f"{base_url}/crm.activity.binding.move"

    payload = {
        "activityId": activity_id,
        "sourceEntityId": from_id,
        "targetEntityId": to_id,
        "sourceEntityTypeId": 2,
        "targetEntityTypeId": 2,
    }

    res2 = requests.get(url=url_move, params=payload)

    if res2.status_code == 200:
        return {
            "status": "sucess",
            "message": f"Atividade movida do Card número {from_id} para o Card número {to_id}",
        }, 200

    return {
        "status": "error",
        "message": res2.json()["error_description"],
    }, 500


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

      
        transfer_url = f"{CHAT_TRANSFER_URL}?CONTACT_ID={contact_id}&TRANSFER_ID={assigned_by}"
        try:
            transfer_response = requests.post(
                "https://grupo--solucoes-teste-tayn.rvc6im.easypanel.host/change-the-chat-responsible/",
                params={"CONTACT_ID": contact_id, "TRANSFER_ID": assigned_by}
            )


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
