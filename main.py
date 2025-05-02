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

@app.route("/change-the-chat-channel/", methods=["POST"])
def change_the_chat_channel():
    CONTACT_ID = request.args.get("CONTACT_ID")
    QUEUE_ID = request.args.get("QUEUE_ID")

    if not CONTACT_ID or not QUEUE_ID:
        return jsonify({"error": "CONTACT_ID and QUEUE_ID must be provided in the URL parameters"}), 400

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/{CODIGO_BITRIX}"
    url = f"{base_url}/imopenlines.crm.chat.getLastId?CRM.ENTITY_TYPE=CONTACT&CRM_ENTITY={CONTACT_ID}"

    response = requests.post(url)
    time.sleep(2)

    if response.status_code == 200:
        datajson = response.json()
        id_chat = datajson["result"]
        url2 = f"{base_url}/imopenlines.operator.transfer?CHAT_ID={id_chat}&QUEUE_ID={QUEUE_ID}"
        response2 = requests.post(url2)
        if response2.status_code == 200:
            return "New responsible approved"
        else:
            return f"No responsible approved: {response2.text}"
    else:
        return f"Failed to get chat ID: {response.text} - {url}"

@app.route("/change-the-chat-responsible/", methods=["POST"])
def change_the_chat_responsability():
    CONTACT_ID = request.args.get("CONTACT_ID")
    TRANSFER_ID = request.args.get("TRANSFER_ID")

    if not CONTACT_ID or not TRANSFER_ID:
        return jsonify({"error": "CONTACT_ID and TRANSFER_ID must be provided in the URL parameters"}), 400

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
    from_id = request.args.get("from_deal_id", "Não informado")
    to_id = request.args.get("to_deal_id", "Não informado")

    if from_id == "Não informado" or to_id == "Não informado":
        return {"status": "error", "message": "ID do deal não informado!"}, 400

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/{CODIGO_BITRIX}"
    url_get_activity = f"{base_url}/crm.activity.list?filter[OWNER_ID]={from_id}"
    res = requests.get(url_get_activity)

    if len(res.json()["result"]) < 1:
        return {"status": "error", "message": f"Não há atividades para serem movidas no card {from_id}"}, 404

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
        return {"status": "sucess", "message": f"Atividade movida do Card número {from_id} para o Card número {to_id}"}, 200

    return {"status": "error", "message": res2.json()["error_description"]}, 500

@app.route("/check-and-update-responsible/", methods=["POST"])
def check_and_update_responsible():
    data = request.get_json()
    deal_id = data.get("deal_id")

    if not deal_id:
        return jsonify({"error": "deal_id is required"}), 400

    base_url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/{CODIGO_BITRIX}"
    deal_url = f"{base_url}/crm.deal.get?ID={deal_id}"
    res_deal = requests.get(deal_url)

    if res_deal.status_code != 200:
        return jsonify({"error": "Failed to fetch deal", "details": res_deal.text}), 500

    deal_data = res_deal.json().get("result", {})
    current_responsible = str(deal_data.get("ASSIGNED_BY_ID"))
    custom_field_value = str(deal_data.get("UF_CRM_1746209622228") or "")

    if not custom_field_value:
        update_url = f"{base_url}/crm.deal.update"
        update_payload = {
            "ID": deal_id,
            "fields": {"UF_CRM_1746209622228": current_responsible}
        }
        res_update = requests.post(update_url, json=update_payload)
        if res_update.status_code == 200:
            return jsonify({"status": "custom field updated", "responsible": current_responsible}), 200
        else:
            return jsonify({"error": "Failed to update custom field", "details": res_update.text}), 500

    elif custom_field_value != current_responsible:
        transfer_url = f"{base_url}/imopenlines.crm.chat.getLastId?CRM.ENTITY_TYPE=DEAL&CRM_ENTITY={deal_id}"
        res_chat = requests.post(transfer_url)
        if res_chat.status_code == 200:
            chat_id = res_chat.json().get("result")
            transfer_action_url = f"{base_url}/imopenlines.operator.transfer?CHAT_ID={chat_id}&TRANSFER_ID={current_responsible}"
            res_transfer = requests.post(transfer_action_url)
            if res_transfer.status_code == 200:
                return jsonify({"status": "chat transferred", "old": custom_field_value, "new": current_responsible}), 200
            else:
                return jsonify({"error": "Failed to transfer chat", "details": res_transfer.text}), 500
        else:
            return jsonify({"error": "Failed to get chat ID", "details": res_chat.text}), 500

    return jsonify({"status": "no action needed", "responsible": current_responsible}), 200

@app.route("/")
def index():
    return "Hello, this is the application!"

if __name__ == "__main__":
    app.run(port=1400, host="0.0.0.0")
