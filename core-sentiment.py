from flask import Flask, render_template, request
from googleapiclient.discovery import build
from textblob import TextBlob
from thai_sentiment import get_sentiment
import langid
import re
from statistics import mean  # Import the mean function for calculating the average sentiment score

app = Flask(__name__)

# Set up your YouTube Data API credentials
api_key = 'AIzaSyDvQ3ZiXV1XZjg_eQ7Oy7vnfiu4CnKCpbc'  # Replace with your actual API key

# Function to retrieve comments from a YouTube video
# Function to retrieve comments from a YouTube video
def get_youtube_comments(video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments = []  # สร้างรายการเปล่าเพื่อเก็บความคิดเห็นทั้งหมด
    page_token = None

    while True:
        results = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            maxResults=1000,  # ระบุจำนวนความคิดเห็นที่ต้องการในแต่ละรอบ
            pageToken=page_token  # ใช้หน้าถัดไปถ้ามี
        ).execute()

        for item in results['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        if 'nextPageToken' in results:
            page_token = results['nextPageToken']
        else:
            break  # หยุดเมื่อไม่มีหน้าถัดไป

    return comments


# Function to detect the language of a comment
def detect_language(comment):
    try:
        lang, _ = langid.classify(comment)
        return lang
    except:
        return 'en'  # Default to English if language detection fails

# Function to analyze sentiment for a list of comments
def analyze_sentiment(comments):
    sentiment_results = []
    lang2 = 0
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    comment_counts = {}

    for comment in comments:
        lang = detect_language(comment)
        if lang == 'th':
            lang2 = 1
            th_sentiment, th_scores = get_sentiment(comment)
            sentiment_label = th_sentiment
            sentiment_scores = th_scores
        else:
            lang2 = 2
            en_blob = TextBlob(comment)
            en_sentiment = en_blob.sentiment.polarity

            if en_sentiment > 0:
                sentiment_label = 'pos'
            elif en_sentiment < 0:
                sentiment_label = 'neg'
            else:
                sentiment_label = 'neu'

            sentiment_scores = en_sentiment

        sentiment_results.append({
            'comment': comment,
            'sentiment_label': sentiment_label,
            'sentiment_scores': sentiment_scores,
            'lang2': lang2
        })

        # Count the sentiment for each comment
        if comment in comment_counts:
            comment_counts[comment][sentiment_label] += 1
        else:
            comment_counts[comment] = {'pos': 0, 'neu': 0, 'neg': 0}
            comment_counts[comment][sentiment_label] = 1

    total_comments = len(sentiment_results)

    if total_comments > 0:
        for result in sentiment_results:
            sentiment_label = result['sentiment_label']
            if sentiment_label == 'pos':
                positive_count += 1
            elif sentiment_label == 'neu':
                neutral_count += 1
            elif sentiment_label == 'neg':
                negative_count += 1

        positive_percentage = round((positive_count / total_comments) * 100, 2)
        negative_percentage = round((negative_count / total_comments) * 100, 2)
        neutral_percentage = round((neutral_count / total_comments) * 100, 2)
    else:
        positive_percentage = 0.00
        negative_percentage = 0.00
        neutral_percentage = 0.00

    # Create a dictionary for the sentiment percentages
    sentiment_percentages = {
        'positive_percentage': positive_percentage,
        'negative_percentage': negative_percentage,
        'neutral_percentage': neutral_percentage
    }
    return sentiment_results, sentiment_percentages, total_comments



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url']
        video_id = extract_video_id(video_url)
        if video_id:
            comments = get_youtube_comments(video_id)
            sentiment_results, sentiment_percentages,total_comments = analyze_sentiment(comments)

            return render_template('result.html', video_id=video_id, sentiment_results=sentiment_results, sentiment_percentages=sentiment_percentages, total_comments=total_comments)
        else:
            return "Invalid YouTube URL. Please provide a valid URL."

    return render_template('index.html')

def extract_video_id(url):
    # Extract the video ID from a YouTube URL
    # Example 1: https://www.youtube.com/watch?v=VIDEO_ID
    # Example 2: https://youtu.be/VIDEO_ID
    match = re.search(r'(?:v=|youtu.be/)([a-zA-Z0-9_-]+)', url)
    if match:
        video_id = match.group(1)
        return video_id
    else:
        return None

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
