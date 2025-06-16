import streamlit as st
import requests
import json
import time
from urllib.parse import quote
import re

def clean_html(text):
    """Remove HTML tags and decode HTML entities"""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # Decode common HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    return text

def search_reddit_multiple_methods(query, sort='relevance', time_filter='all', limit=25):
    """
    Try multiple methods to search Reddit
    """
    methods = [
        ("Direct JSON API", search_reddit_json),
        ("Subreddit Search", search_reddit_subreddit),
        ("Alternative Headers", search_reddit_alt_headers),
    ]
    
    for method_name, method_func in methods:
        st.info(f"🔄 Trying method: {method_name}")
        try:
            results = method_func(query, sort, time_filter, limit)
            if results:
                st.success(f"✅ Success with method: {method_name}")
                return results
            else:
                st.warning(f"⚠️ No results from method: {method_name}")
        except Exception as e:
            st.warning(f"❌ Method {method_name} failed: {str(e)}")
            continue
    
    return []

def search_reddit_json(query, sort='relevance', time_filter='all', limit=25):
    """
    Original JSON API method
    """
    url = "https://www.reddit.com/search.json"
    
    params = {
        'q': query,
        'sort': sort,
        't': time_filter,
        'limit': limit,
        'type': 'link'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    return process_reddit_data(data)

def search_reddit_alt_headers(query, sort='relevance', time_filter='all', limit=25):
    """
    Try with different headers to avoid blocking
    """
    url = "https://www.reddit.com/search.json"
    
    params = {
        'q': query,
        'sort': sort,
        't': time_filter,
        'limit': limit,
        'type': 'link'
    }
    
    headers = {
        'User-Agent': 'curl/7.68.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    return process_reddit_data(data)

def search_reddit_subreddit(query, sort='relevance', time_filter='all', limit=25):
    """
    Search within popular subreddits that might be relevant
    """
    relevant_subreddits = ['AskReddit', 'NoStupidQuestions', 'explainlikeimfive', 'LifeProTips', 'YouShouldKnow']
    all_posts = []
    
    for subreddit in relevant_subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            
            params = {
                'q': query,
                'restrict_sr': '1',
                'sort': sort,
                't': time_filter,
                'limit': 5  # Fewer per subreddit
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; RedditSearchBot/1.0)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = process_reddit_data(data)
                all_posts.extend(posts)
                
                if len(all_posts) >= limit:
                    break
                    
        except Exception as e:
            continue  # Try next subreddit
    
    return all_posts[:limit]

def process_reddit_data(data):
    """
    Process Reddit JSON data into standardized format
    """
    posts = []
    
    if 'data' in data and 'children' in data['data']:
        for post in data['data']['children']:
            try:
                post_data = post['data']
                
                post_info = {
                    'title': clean_html(post_data.get('title', '')),
                    'subreddit': post_data.get('subreddit', ''),
                    'url': f"https://www.reddit.com{post_data.get('permalink', '')}",
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'selftext': clean_html(post_data.get('selftext', ''))[:200] + '...' if post_data.get('selftext') else '',
                    'author': post_data.get('author', '[deleted]')
                }
                posts.append(post_info)
            except Exception:
                continue
    
    return posts

def generate_search_urls(query):
    """
    Generate manual search URLs as fallback
    """
    encoded_query = quote(query)
    
    urls = {
        'Reddit Search': f"https://www.reddit.com/search/?q={encoded_query}",
        'Google Site Search': f"https://www.google.com/search?q=site:reddit.com+{encoded_query}",
        'DuckDuckGo Site Search': f"https://duckduckgo.com/?q=site:reddit.com+{encoded_query}",
    }
    
    return urls

def extract_keywords(text):
    """Extract potential keywords from the input text"""
    # Simple keyword extraction - you can enhance this
    words = text.lower().split()
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords[:10]  # Return top 10 keywords

def main():
    st.set_page_config(
        page_title="Reddit Query Finder",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Reddit Query Finder")
    st.markdown("Find relevant Reddit posts to respond to based on your content!")
    
    # Sidebar for settings
    st.sidebar.header("Search Settings")
    
    # Debug mode toggle
    debug_mode = st.sidebar.checkbox("🔧 Debug Mode", help="Show detailed logging and API responses")
    
    sort_options = {
        'Relevance': 'relevance',
        'Hot': 'hot',
        'Top': 'top',
        'New': 'new',
        'Comments': 'comments'
    }
    
    time_filters = {
        'All Time': 'all',
        'Past Year': 'year',
        'Past Month': 'month',
        'Past Week': 'week',
        'Past Day': 'day',
        'Past Hour': 'hour'
    }
    
    sort_by = st.sidebar.selectbox("Sort by:", list(sort_options.keys()), index=0)
    time_filter = st.sidebar.selectbox("Time filter:", list(time_filters.keys()), index=0)
    num_results = st.sidebar.slider("Number of results:", 5, 50, 25)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Your Content")
        user_text = st.text_area(
            "Enter your text/response content:",
            height=200,
            placeholder="Paste the content you want to find relevant Reddit queries for..."
        )
        
        if user_text:
            st.subheader("Extracted Keywords")
            keywords = extract_keywords(user_text)
            if keywords:
                st.write(", ".join(keywords))
            else:
                st.write("No keywords extracted")
    
    with col2:
        st.header("Search Query")
        
        # Auto-generate search query from keywords
        if user_text:
            keywords = extract_keywords(user_text)
            suggested_query = " ".join(keywords[:5])  # Use top 5 keywords
        else:
            suggested_query = ""
        
        search_query = st.text_input(
            "Search query (auto-generated from your text):",
            value=suggested_query,
            placeholder="Enter keywords to search for on Reddit"
        )
        
        search_button = st.button("🔍 Search Reddit", type="primary", use_container_width=True)
    
    # Search results
    if search_button and search_query:
        st.header("🔍 Search Details")
        
        # Show search parameters
        with st.expander("Search Parameters", expanded=debug_mode):
            st.write(f"**Query:** {search_query}")
            st.write(f"**Sort:** {sort_by}")
            st.write(f"**Time Filter:** {time_filter}")
            st.write(f"**Results Limit:** {num_results}")
        
        with st.spinner("Searching Reddit..."):
            results = search_reddit_multiple_methods(
                search_query, 
                sort=sort_options[sort_by], 
                time_filter=time_filters[time_filter],
                limit=num_results
            )
        
        if results:
            st.success(f"Found {len(results)} relevant posts!")
            
            st.header("📋 Search Results")
            
            for i, post in enumerate(results, 1):
                with st.expander(f"{i}. r/{post['subreddit']} - {post['title'][:80]}{'...' if len(post['title']) > 80 else ''}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**Title:** {post['title']}")
                        st.markdown(f"**Subreddit:** r/{post['subreddit']}")
                        if post['selftext']:
                            st.markdown(f"**Preview:** {post['selftext']}")
                    
                    with col2:
                        st.metric("Score", post['score'])
                        st.metric("Comments", post['num_comments'])
                    
                    with col3:
                        st.markdown(f"**Author:** u/{post['author']}")
                        st.markdown(f"[**Open Post**]({post['url']})")
                        
                        # Copy link button
                        if st.button(f"📋 Copy Link", key=f"copy_{i}"):
                            st.code(post['url'])
            
            # Export results
            st.header("📤 Export Results")
            
            # Create export data
            export_data = []
            for post in results:
                export_data.append({
                    'Title': post['title'],
                    'Subreddit': post['subreddit'],
                    'URL': post['url'],
                    'Score': post['score'],
                    'Comments': post['num_comments'],
                    'Author': post['author']
                })
            
            # Convert to CSV-like format
            csv_data = "Title,Subreddit,URL,Score,Comments,Author\n"
            for post in export_data:
                csv_data += f'"{post["Title"]}",r/{post["Subreddit"]},{post["URL"]},{post["Score"]},{post["Comments"]},u/{post["Author"]}\n'
            
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv_data,
                file_name=f"reddit_results_{search_query.replace(' ', '_')}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("❌ All search methods failed. Here are some manual alternatives:")
            
            # Generate manual search URLs
            search_urls = generate_search_urls(search_query)
            
            st.header("🔗 Manual Search Options")
            st.markdown("Try these search links in your browser:")
            
            for search_name, search_url in search_urls.items():
                st.markdown(f"**{search_name}:** [Open Search]({search_url})")
                st.code(search_url)
            
            st.info("""
            **Alternative Approaches:**
            1. Use the manual search links above
            2. Try shorter, more specific keywords
            3. Search individual subreddits manually
            4. Use Google with `site:reddit.com your keywords`
            """)
    
    elif search_button and not search_query:
        st.error("Please enter a search query.")
    
    # Instructions
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        1. **Enter your content** in the text area on the left
        2. **Keywords will be automatically extracted** and used to generate a search query
        3. **Adjust the search query** if needed in the search box
        4. **Configure search settings** in the sidebar (sort order, time filter, number of results)
        5. **Click Search Reddit** to find relevant posts
        6. **Browse results** and click links to open Reddit posts
        7. **Export results** as CSV for later reference
        
        **Tips:**
        - Use specific keywords related to your content
        - Try different sort orders (relevance, hot, new, etc.)
        - Adjust time filters to find recent discussions
        - Look for posts with good engagement (high scores and comments)
        """)

if __name__ == "__main__":
    main()
