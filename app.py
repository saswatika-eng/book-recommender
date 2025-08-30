from difflib import get_close_matches
from flask import Flask, render_template, request
import pickle
import numpy as np
import gdown   # NEW

app = Flask(__name__)

# Google Drive file IDs (replace with yours!)
file_ids = {
    "popular.pkl": "1STALpFK9kFHqTf8a0sGQXFHYigswCif4",
    "pt.pkl": "1jQVofLhJEfxkOcd4DFgfXVnA5kQMxzba",
    "books.pkl": "1338PUjFcQ3IWIjDF6jsbnYasXVVIxuJS",
    "similarity_scores.pkl": "1O9Cu3aTwVe79Xbes-ESGm3tm0CXTKxYx"
}

# Download and load pickled files
def load_pickle_from_drive(filename, file_id):
    url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url, filename, quiet=False)
    return pickle.load(open(filename, "rb"))

popular_df = load_pickle_from_drive("popular.pkl", file_ids["popular.pkl"])
pt = load_pickle_from_drive("pt.pkl", file_ids["pt.pkl"])
books = load_pickle_from_drive("books.pkl", file_ids["books.pkl"])
similarity_scores = load_pickle_from_drive("similarity_scores.pkl", file_ids["similarity_scores.pkl"])

# Normalize all titles to lowercase and strip spaces
pt.index = pt.index.str.lower().str.strip()
books['Book-Title'] = books['Book-Title'].str.lower().str.strip()
popular_df['Book-Title'] = popular_df['Book-Title'].str.strip()

@app.route('/')
def index():
    return render_template('index.html',
                           book_name=popular_df['Book-Title'].tolist(),
                           author=popular_df['Book-Author'].tolist(),
                           image=popular_df['Image-URL-M'].tolist(),
                           votes=popular_df['num_ratings'].tolist(),
                           rating=popular_df['avg_rating'].tolist()
                           )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html', pt_index=pt.index.tolist())

@app.route('/recommend_books', methods=['POST'])
def recommend():
    user_input = request.form.get('user_input')
    user_input = user_input.strip().lower()  # normalize input

    # Find closest match to user input from pt.index
    matches = get_close_matches(user_input, pt.index, n=1, cutoff=0.6)

    if not matches:
        return render_template('recommend.html', pt_index=pt.index, error="Book not found. Please choose from suggestions.", data=[])

    best_match = matches[0]
    index = np.where(pt.index == best_match)[0][0]

    similar_items = sorted(
        list(enumerate(similarity_scores[index])),
        key=lambda x: x[1], reverse=True
    )

    data = []
    used_titles = set()
    for i in similar_items:
        title = pt.index[i[0]]
        if title.lower() in used_titles:
            continue
        temp_df = books[books['Book-Title'].str.lower() == title.lower()]
        if not temp_df.empty:
            book = temp_df.drop_duplicates('Book-Title').iloc[0]
            item = [book['Book-Title'], book['Book-Author'], book['Image-URL-M']]
            data.append(item)
            used_titles.add(title.lower())
        if len(data) == 10:
            break

    return render_template('recommend.html', pt_index=pt.index, data=data)

if __name__ == '__main__':
    app.run(debug=True)
