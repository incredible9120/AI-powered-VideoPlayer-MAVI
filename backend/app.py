import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import asyncio
from dotenv import load_dotenv
import openai
from time import sleep
import json

load_dotenv()

MAVI_API_KEY = os.getenv("MAVI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CALLBACK_URI = os.getenv("CALLBACK_URI")
client = openai.Client(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)  # Allow React frontend to communicate

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def summarize_text(long_text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes text.",
            },
            {
                "role": "user",
                "content": f"Please summarize the following story of transcription of video:\n\n{long_text}. And no need to describe about the transcription, only story.",
            },
        ],
        temperature=0.5,
        max_tokens=200,
    )

    summary = response.choices[0].message.content
    return summary


@app.route("/analyzeFile", methods=["POST"])
async def analyze_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video = request.files["video"]
    filepath = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(filepath)
    print(f"Video saved: {filepath}")
    upload_video(video)

    # TODO: Replace this with real analysis (e.g., use MAVI API)

    dummy_analysis = {
        "filename": video.filename,
        "duration": "00:01:23",  # fake duration
        "scenes": [
            {"start": 0, "end": 30, "mood": "Happy"},
            {"start": 30, "end": 83, "mood": "Tense"},
        ],
    }

    return jsonify(dummy_analysis)


@app.route("/analyzeURL", methods=["POST"])
async def analyze_url():
    # if "url" not in request.data:
    #     return jsonify({"error": "No video url provided"}), 400
    try:
        videoURL = request.form.get("url")
        print(f"Video URL: {videoURL}")
        # global videoNo
        # videoNo = asyncio.run(upload_video(videoURL))
        # print(f"VideoNo: {videoNo}")

        dummy_analysis = await subscribe_to_video()
        print(dummy_analysis)
        # dummy_analysis = {
        #     "filename": videoURL,
        #     "duration": "00:05:43",  # fake duration
        #     "scenes": [
        #         {"start": 0, "end": 30, "mood": "Happy"},
        #         {"start": 30, "end": 83, "mood": "Tense"},
        #     ],
        # }
        return jsonify(dummy_analysis)
    except Exception as e:
        return (
            jsonify({"code": "5000", "msg": "Error processing data", "error": str(e)}),
            500,
        )


@app.route("/topic", methods=["POST"])
async def receive_topic():
    print("Received topic")
    try:
        data = request.json
        query = data.get("query")

        if not query:
            return {"error": "No topicIndex provided"}
        print(query)
        response_data = await extract_clip_from_query(query)

        videos = response_data["data"]["videos"]

        # Sort videos by score in descending order
        sorted_videos = sorted(videos, key=lambda v: v["score"], reverse=True)

        # Extract top 5
        top_5_videos = sorted_videos[:5]

        # Print or use them as needed
        for i, video in enumerate(top_5_videos, start=1):
            print(f"Top {i}:")
            print(f"  Score: {video['score']}")
            print(
                f"  Fragment: {video['fragmentStartTime']} - {video['fragmentEndTime']}"
            )
            print(f"  Video No: {video['videoNo']}")
            print()

        # return top_5_videos
        return (
            jsonify(
                {"code": "0000", "msg": "Top 5 extracted", "topVideos": top_5_videos}
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"code": "5000", "msg": "Error processing data", "error": str(e)}),
            500,
        )


async def subscribe_to_video(videoNo: str = "mavi_video_579880731732480000"):
    headers = {"Authorization": MAVI_API_KEY}

    data = {
        "videoNo": videoNo,  # The video ID to transcribe
        "type": "VIDEO",  # Specify "AUDIO" for audio-only, "VIDEO" for video-only
        "callBackUri": CALLBACK_URI,  # Optional callback URL for status notifications
    }
    headers = {"Authorization": MAVI_API_KEY}
    # response = requests.post(
    #     "https://mavi-backend.openinterx.com/api/serve/video/subTranscription",
    #     headers=headers,
    #     json=data,
    # )

    # print(f"subtranscription:{response.json()}")
    params = {"taskNo": "project_580034559027056640"}
    # response.json().get("data").get("taskNo")
    response = requests.get(
        "https://mavi-backend.openinterx.com/api/serve/video/getTranscription",
        headers=headers,
        params=params,
    )
    summarizedText = summarize_text(response.json().get("data").get("transcriptions"))
    print(summarizedText)
    return summarizedText


async def upload_video(url):
    headers = {"Authorization": MAVI_API_KEY}  # API key

    SAMPLE_VIDEO_URL = url
    CALLBACK_URI = os.getenv("CALLBACK_URI")

    # Video file details
    data = {"url": SAMPLE_VIDEO_URL}

    # Optional callback URL for task status notifications
    params = {}
    if CALLBACK_URI:
        params["callBackUri"] = CALLBACK_URI

    response = requests.post(
        "https://mavi-backend.openinterx.com/api/serve/video/uploadUrl",
        json=data,
        params=params,
        headers=headers,
    )
    await asyncio.sleep(30)
    return response.json().get("data").get("videoNo")


async def extract_clip_from_query(
    query: str = "happy mood", videoNo: str = "mavi_video_579880731732480000"
):
    try:
        print(query, videoNo)
        headers = {"Authorization": MAVI_API_KEY}

        data = {
            "videoNos": [videoNo],
            "searchValue": query,  # Natural language search query
        }

        response = requests.post(
            "https://mavi-backend.openinterx.com/api/serve/video/searchVideoFragment",
            headers=headers,
            json=data,
        )

        print(response.json())

        return response.json()

        # return {"status": "upload started", "mavi_response": mavi_response}

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/describe", methods=["POST"])
async def chat_with_video():
    try:
        headers = {"Authorization": MAVI_API_KEY}  # API key
        data = request.json
        timestamp = data.get("timestamp")
        print(int(timestamp))
        data = {
            "videoNos": [
                "mavi_video_579880731732480000"
            ],  # List of video IDs to chat about
            "message": f"Summarize the following story until {int(timestamp)}s",  # User query
            "history": [],  # Optional chat history (empty for a new conversation)
            "stream": False,  # Set to True for streaming response
        }

        response = requests.post(
            "https://mavi-backend.openinterx.com/api/serve/video/chat",
            headers=headers,
            json=data,
        )
        response_string = response.text
        print(response_string)
        json_string = response_string[len("data:") :]
        print(json_string)

        response_json = json.loads(json_string)
        print(type(response_json))

        print("=====")
        print(response_json)
        print("=====")

        print("----")
        print(response_json["data"])
        print("----")

        print("*****")
        print(response_json["data"]["msg"])
        print("*****")

        msg_data = response_json["data"]["msg"]

        return jsonify(msg_data)

    except Exception as e:
        return (
            jsonify({"code": "5000", "msg": "Error processing data", "error": str(e)}),
            500,
        )


if __name__ == "__main__":
    # asyncio.run(chat_with_video())
    # asyncio.run(extract_clip_from_query())
    app.run(debug=True)
