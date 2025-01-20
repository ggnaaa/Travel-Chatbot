# app.py (Flask app)
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests

RASA_API_URL = 'http://localhost:5005/webhooks/rest/webhook'  # Correct endpoint
app = Flask(__name__)
CORS(app, resources={r"/webhook": {"origins": "*"}})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({'response': "No message received."})

    try:
        rasa_response = requests.post(RASA_API_URL, json={'sender': "user", 'message': user_message}) #added sender
        rasa_response_json = rasa_response.json()
        print("Rasa Response:", rasa_response_json)

        bot_responses = []
        for response in rasa_response_json:
            if "text" in response:
                bot_responses.append(response["text"])

        if bot_responses:
            bot_response = "\n".join(bot_responses)
        else:
            bot_response = "Sorry, I didn't understand that."

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Rasa: {e}")
        if hasattr(e.response, 'content'):  # Check if response exists
            print(f"Response content: {e.response.content}")
        bot_response = "Sorry, there was an error communicating with the server."
        return jsonify({'response': bot_response}), 500 #return error code

    return jsonify({'response': bot_response})

if __name__ == "__main__":
    app.run(debug=True, port=3000)
