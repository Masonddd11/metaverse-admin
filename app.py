from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

NEXTJS_API_URL = os.getenv("NEXTJS_API_URL")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user-progress', methods=['POST', 'GET'])
def user_progress():
    if request.method == 'POST':
        token = request.form.get('token')
        if not token:
            flash('Token is required', 'error')
            return redirect(url_for('index'))
        # Redirect to the same route with the token as a query parameter
        return redirect(url_for('user_progress', token=token))
    
    token = request.args.get('token')
    if not token:
        flash('Token is required', 'error')
        return redirect(url_for('index'))

    try:
        response = requests.get(NEXTJS_API_URL, headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 401:
            flash('Unauthorized', 'error')
            return redirect(url_for('index'))
        response.raise_for_status()
        user_progress_data = response.json()

        aggregated_data = {}
        for progress in user_progress_data:
            user_email = progress['user']['email']
            if user_email not in aggregated_data:
                aggregated_data[user_email] = {
                    'email': user_email,
                    'questions_answered': 0,
                    'videos_watched': 0,
                    'points': 0,
                    'completed_count': 0,
                    'createdAt': progress['createdAt'],
                    'updatedAt': progress['updatedAt']
                }
            aggregated_data[user_email]['questions_answered'] += len(progress['questionSet']['questions'])
            aggregated_data[user_email]['videos_watched'] += len(progress['questionSet']['Video'])
            aggregated_data[user_email]['points'] += progress['points']
            if progress['completed']:
                aggregated_data[user_email]['completed_count'] += 1

        for user_email, data in aggregated_data.items():
            data['completed'] = data['completed_count'] >= 4

        user_progress_data = list(aggregated_data.values())

        # Sorting
        sort_by = request.args.get('sort', 'email')
        order = request.args.get('order', 'asc')
        reverse = (order == 'desc')
        user_progress_data.sort(key=lambda x: x[sort_by], reverse=reverse)

    except requests.RequestException as e:
        print(f"Error fetching user progress data: {e}")
        user_progress_data = []

    return render_template('user_progress.html', user_progress=user_progress_data)

if __name__ == '__main__':
    app.run(debug=True, port=8000)