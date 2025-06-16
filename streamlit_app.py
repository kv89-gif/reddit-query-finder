import streamlit as st
import requests
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from urllib.parse import quote

nltk.download('stopwords')


def clean_html(text):
    if not text:
        return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    return text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')


def extract_top_keywords(text, top_n=10):
    stop_words = set(stopwords.words('english'))
    vectorizer = CountVectorizer(stop_words=stop_words, max_features=top_n)
    X = vectorizer.fit_transform([text])
    keywords = vectorizer.get_feature_names_out()
    return list(keywords)


def search_pushshift(query, limit=10):
    url = "https://api.pushshift.io/reddit/search/submission"
    params = {'q': query, 'size': limit, 'sort': 'desc'}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            results = []
            for post in response.json().get('data', []):
                results.append({
                    'title': post.get('title', ''),
                    'subreddit': post.get('subreddit', ''),
                    'url': f"https://www.reddit.com{post.get('permalink', '')}"
                })
            return results
    except Exception as e:
        st.error(f"Pushshift error: {e}")
    return []


def main():
    st.title("Reddit Query Finder 🧠")
    st.markdown("Paste your content and get Reddit threads where you can respond.")

    user_text = st.text_area("Enter your paragraph:", height=200)

    if user_text:
        keywords = extract_top_keywords(user_text)
        if keywords:
            query = " ".join(keywords)
            st.write(f"**Search query:** `{query}`")

            if st.button("Find Reddit Threads"):
                with st.spinner("Searching Reddit..."):
                    posts = search_pushshift(query)

                if posts:
                    st.success(f"Found {len(posts)} results:")
                    for i, post in enumerate(posts, 1):
                        st.markdown(f"{i}. [{post['title']}]({post['url']}) — r/{post['subreddit']}")
                else:
                    st.warning("No relevant posts found.")
        else:
            st.info("Couldn’t extract meaningful keywords from the input.")


if __name__ == '__main__':
    main()
