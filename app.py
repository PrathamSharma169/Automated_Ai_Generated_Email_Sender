import os
import pandas as pd
from flask import Flask, request, render_template, jsonify
from groq import Groq
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time

app = Flask(__name__)

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize SendGrid client
sendgrid_client = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

# In-memory store for email statuses (replace with a database for persistence)
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
        # Customize the prompt using only the placeholders
        custom_prompt = prompt_template
        for column_name in row.index:
            placeholder = "{" + column_name + "}"
            if placeholder in custom_prompt:
                custom_prompt = custom_prompt.replace(placeholder, str(row[column_name]))

        # Add instruction for Groq API to avoid introductory text
        custom_prompt = f"Generate only the main content message:\n{custom_prompt}"

        # Generate message using Groq API
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": custom_prompt}],
            model="llama3-8b-8192",
        )
        main_content = chat_completion.choices[0].message.content
        main_content = main_content.split("\n", 1)[-1].strip()

        # Extract email ID from row
        email = row['email']

        # Send email using SendGrid
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

        # Initialize delivery status to "Pending" after email is sent
        email_statuses[email] = {"status": status, "delivery_status": "Pending"}

        # Optional delay to respect rate limits
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

        # Update email status based on the event type
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
