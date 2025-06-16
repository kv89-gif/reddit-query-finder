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


def extract_top_keywords(text, top_n=10):
    stop_words = set([
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
        'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    ])
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    freq = {}
    for word in keywords:
        freq[word] = freq.get(word, 0) + 1
    sorted_keywords = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return [kw[0] for kw in sorted_keywords[:top_n]]


def search_pushshift(query, limit=10, after_days=None, subreddit_filter=None):
    url = "https://api.pushshift.io/reddit/search/submission"
    import time
    params = {'q': query, 'size': limit, 'sort': 'desc'}
    if after_days:
        after_timestamp = int(time.time()) - (after_days * 86400)
        params['after'] = after_timestamp
    if subreddit_filter:
        params['subreddit'] = subreddit_filter
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
            st.write(f"**Search keywords:** {', '.join(keywords)}")

            time_filter = st.selectbox("Filter posts from:", ["Any time", "Last 7 days", "Last 30 days"], index=0)
            after_days = None
            if time_filter == "Last 7 days":
                after_days = 7
            elif time_filter == "Last 30 days":
                after_days = 30

            subreddit_filter = st.text_input("Filter by subreddit (optional):")

            if st.button("Find Reddit Threads"):
                with st.spinner("Searching Reddit..."):
                    posts = []
                    seen_urls = set()
                    for kw in keywords:
                        results = search_pushshift(kw, after_days=after_days, subreddit_filter=subreddit_filter if subreddit_filter else None)
                        for r in results:
                            if r['url'] not in seen_urls:
                                posts.append(r)
                                seen_urls.add(r['url'])

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
