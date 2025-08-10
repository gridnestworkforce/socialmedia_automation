from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN =  os.environ.get("BOT_TOKEN")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        print("Telegram error:", response.text)


def get_trending_video(query):
    url = "https://twitter-api45.p.rapidapi.com/search.php"
    querystring = {
        "query": query,
        "search_type": "Top"
    }

    headers = {
        "x-rapidapi-host": "twitter-api45.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()

        for tweet in data.get("timeline", []):
            media = tweet.get("media", {})
            videos = media.get("video", [])

            for video in videos:
                variants = video.get("variants", [])
                mp4s = [v for v in variants if v.get("content_type") == "video/mp4" and "url" in v]
                if mp4s:
                    best_video = sorted(mp4s, key=lambda x: x.get("bitrate", 0), reverse=True)[0]
                    return {
                        "title": f"*{tweet.get('screen_name', query)}*",
                        "description": tweet.get("text", "No description"),
                        "hashtags": f"#{query.replace(' ', '')} #TrendingNow",
                        "url": best_video["url"]
                    }

    except Exception as e:
        print("Error fetching video:", e)

    return {
        "title": f"*{query}*",
        "description": "_No trending video found or can't fetch video URL._",
        "hashtags": f"#{query.replace(' ', '')}",
        "url": None
    }


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Received data:", data)

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        user = msg["from"]
        name = user.get("first_name", user.get("username", "Friend"))
        text = msg.get("text", "Allu Arjun").strip()

        video = get_trending_video(text)

        caption = (
            f"Hi {name}! Here's a trending video 🎬\n\n"
            f"{video['title']}\n\n"
            f"{video['description']}\n\n"
            f"{video['hashtags']}"
        )

        if video["url"]:
            url = f"{TELEGRAM_API}/sendVideo"
            payload = {
                "chat_id": chat_id,
                "video": video["url"],
                "caption": caption,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload)
            if not response.ok:
                print("Telegram error:", response.text)
                send_message(chat_id, f"{caption}\n\n[Watch Video]({video['url']})")
        else:
            send_message(chat_id, caption)

    return '', 200


if __name__ == "__main__":
    app.run(port=5000)
