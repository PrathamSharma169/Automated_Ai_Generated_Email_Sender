import os
import pandas as pd
from flask import Flask, request, render_template, jsonify
from groq import Groq
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

sendgrid_client = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

email_statuses = {}

@app.route('/')
def index():
    return render_template("form.html")

@app.route('/process', methods=['POST'])
def process():
    global email_statuses
    prompt_template = request.form['prompt']
    file = request.files['file']
    data = pd.read_csv(file)

    for index, row in data.iterrows():
        custom_prompt = prompt_template
        for column_name in row.index:
            placeholder = "{" + column_name + "}"
            if placeholder in custom_prompt:
                custom_prompt = custom_prompt.replace(placeholder, str(row[column_name]))

        custom_prompt = f"Generate only the main content message:\n{custom_prompt}"

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": custom_prompt}],
            model="llama3-8b-8192",
        )
        main_content = chat_completion.choices[0].message.content
        main_content = main_content.split("\n", 1)[-1].strip()

        email = row['email']

        message = Mail(
            from_email="yourgmail@gmail.com", # enter your gmail id by which you want to send mail
            to_emails=email,
            subject="Customized Message",
            plain_text_content=main_content
        )

        try:
            response = sendgrid_client.send(message)
            if response.status_code == 202:
                status = "Sent"
            else:
                status = f"Failed (Status Code: {response.status_code})"
        except Exception as e:
            status = f"Failed (Error: {str(e)})"

        email_statuses[email] = {"status": status, "delivery_status": "Pending"}

        time.sleep(1)

    return render_template("status.html", email_statuses=email_statuses)
@app.route('/webhook', methods=['POST'])
def webhook():
    global email_statuses
    """Handle webhook events from SendGrid."""
    events = request.get_json()
    for event in events:
        email = event.get("email")
        event_type = event.get("event")
        event_type = event.get("event")

        if email in email_statuses:
            if event_type == "delivered":
                email_statuses[email]["delivery_status"] = "Delivered"
            elif event_type == "open":
                email_statuses[email]["delivery_status"] = "Opened"
            elif event_type == "bounce":
                email_statuses[email]["delivery_status"] = "Bounced"
            elif event_type == "dropped":
                email_statuses[email]["delivery_status"] = "Failed"

    return jsonify({"status": "success"}), 200

@app.route('/dashboard')
def dashboard():
    """Render a dashboard with the email statuses."""
    return render_template("dashboard.html", email_statuses=email_statuses)

if __name__ == '__main__':
    app.run(debug=True)
