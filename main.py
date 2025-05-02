import requests
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import time

load_dotenv()
CODIGO_BITRIX = os.getenv("CODIGO_BITRIX")

app = Flask(__name__)


def extrair_numero(string):
    start_index = string.index("_") + 1
    numero = string[start_index:]
    return numero


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

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/{CODIGO_BITRIX}"
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

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/{CODIGO_BITRIX}"
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

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/{CODIGO_BITRIX}"
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

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/{CODIGO_BITRIX}"

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


@app.route("/")
def index():
    return "Hello, this is the application!"

if __name__ == "__main__":
    app.run(port=1400, host="0.0.0.0")
