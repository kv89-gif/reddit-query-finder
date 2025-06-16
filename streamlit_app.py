import streamlit as st
import requests
import re
from urllib.parse import quote

def clean_html(text):
    if not text:
        return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    return text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')

def extract_keywords(text):
    stop_words = set([
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
        'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    ])
    words = text.lower().split()
    return [w for w in words if w not in stop_words and len(w) > 2][:10]

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
        keywords = extract_keywords(user_text)
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
