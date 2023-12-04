import os
import json
import requests
from datetime import datetime

STACK_OVERFLOW_API = "https://api.stackexchange.com/2.3/search"
SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
STATE_FILE = "state.txt"

def get_latest_question_timestamp():
    try:
        with open(STATE_FILE, 'r') as f:
            content = f.read().strip()
            return int(content) if content else 0
    except FileNotFoundError:
        return 0

def update_latest_question_timestamp(latest_timestamp):
    with open(STATE_FILE, 'w') as f:
        f.write(str(latest_timestamp))

def fetch_questions(latest_timestamp):
    params = {
        "tagged": "open-telemetry",
        "sort": "creation",
        "site": "stackoverflow"
    }
    if latest_timestamp > 0:
        params["min"] = latest_timestamp + 1

    response = requests.get(STACK_OVERFLOW_API, params=params)
    response.raise_for_status()
    return response.json().get('items', [])

def format_question(question):
    title = question['title']
    link = question['link']
    tags = [tag for tag in question['tags'] if tag != 'open-telemetry']
    tags_str = ', '.join(tags)
    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "New StackOverflow Question",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{link}|{title}>\n*Tags:* {tags_str}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Posted at {datetime.fromtimestamp(question['creation_date']).strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ],
        "text": title
    }
    return message

def post_to_slack(message):
    headers = {"Content-Type": "application/json"}
    data = {"text": message['text'], "blocks": message['blocks']}
    response = requests.post(SLACK_WEBHOOK_URL, headers=headers, data=json.dumps(data))
    response.raise_for_status()

def main():
    latest_timestamp = get_latest_question_timestamp()
    questions = fetch_questions(latest_timestamp)

    for question in questions:
        message = format_question(question)
        post_to_slack(message)
        latest_timestamp = max(latest_timestamp, question['creation_date'])

    update_latest_question_timestamp(latest_timestamp)

if __name__ == "__main__":
    main()