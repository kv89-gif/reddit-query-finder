import streamlit as st
import re
from urllib.parse import quote


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


def generate_reddit_search_links(keywords, time_filter=None):
    base_url = "https://www.reddit.com/search/?q="
    phrases = []
    for i in range(len(keywords)):
        for j in range(i + 1, min(i + 4, len(keywords))):
            phrase = " ".join(keywords[i:j+1])
            phrases.append(phrase)
    unique_phrases = list(dict.fromkeys(phrases))
    if time_filter:
        return [f"{base_url}{quote(p)}&t={time_filter}" for p in unique_phrases]
    return [f"{base_url}{quote(p)}" for p in unique_phrases]


def main():
    st.title("Reddit Query Finder 🧠")
    st.markdown("Paste your content and get Reddit search links for threads where you can respond.")

    user_text = st.text_area("Enter your paragraph:", height=200)

    if user_text:
        time_filter_map = {
            "Any time": None,
            "Past 24 hours": "day",
            "Past week": "week",
            "Past month": "month",
            "Past 6 months": "6months"
        }
        selected_time = st.selectbox("Filter posts by time:", list(time_filter_map.keys()), index=0)
        time_filter = time_filter_map[selected_time]

        keywords = extract_top_keywords(user_text)
        if keywords:
            st.write(f"**Search keywords:** {', '.join(keywords)}")

            search_button = st.button("Show Reddit Search Links")
            if search_button:
                search_links = generate_reddit_search_links(keywords, time_filter=time_filter)

                if search_links:
                    st.success("Click the links below to search Reddit for related queries:")
                    for i, link in enumerate(search_links, 1):
                        st.markdown(f"{i}. [Search Reddit]({link})")

                    all_links_text = "\n".join(search_links)
                    st.download_button("📋 Copy All Search Links", data=all_links_text, file_name="reddit_search_links.txt")

                    st.markdown(f"🔗 First result will open below:")
                    st.markdown(f"<iframe src='{search_links[0]}' width='100%' height='600'></iframe>", unsafe_allow_html=True)
        else:
            st.info("Couldn’t extract meaningful keywords from the input.")


if __name__ == '__main__':
    main()
