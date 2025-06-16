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

def search_with_reddit_api(query, client_id, client_secret, user_agent, sort='relevance', time_filter='all', limit=25):
    """
    Search Reddit using official OAuth API
    """
    try:
        # Get access token
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        data = {'grant_type': 'client_credentials'}
        headers = {'User-Agent': user_agent}
        
        token_response = requests.post('https://www.reddit.com/api/v1/access_token',
                                     auth=auth, data=data, headers=headers)
        
        if token_response.status_code != 200:
            st.error(f"Failed to get Reddit token: {token_response.status_code}")
            return []
        
        token = token_response.json()['access_token']
        
        # Search with token
        headers = {
            'Authorization': f'bearer {token}',
            'User-Agent': user_agent
        }
        
        params = {
            'q': query,
            'sort': sort,
            't': time_filter,
            'limit': limit,
            'type': 'link'
        }
        
        search_response = requests.get('https://oauth.reddit.com/search',
                                     headers=headers, params=params)
        
        if search_response.status_code == 200:
            data = search_response.json()
            return process_reddit_data(data)
        else:
            st.error(f"Search failed: {search_response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Reddit API error: {str(e)}")
        return []

def search_pushshift_api(query, sort='score', time_filter='all', limit=25):
    """
    Use Pushshift API as alternative (if available)
    """
    try:
        url = "https://api.pushshift.io/reddit/search/submission"
        
        params = {
            'q': query,
            'size': limit,
            'sort': sort,
        }
        
        # Add time filter
        if time_filter != 'all':
            import datetime
            now = datetime.datetime.now()
            if time_filter == 'day':
                after = now - datetime.timedelta(days=1)
            elif time_filter == 'week':
                after = now - datetime.timedelta(weeks=1)
            elif time_filter == 'month':
                after = now - datetime.timedelta(days=30)
            elif time_filter == 'year':
                after = now - datetime.timedelta(days=365)
            
            params['after'] = int(after.timestamp())
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            posts = []
            
            for post in data.get('data', []):
                post_info = {
                    'title': post.get('title', ''),
                    'subreddit': post.get('subreddit', ''),
                    'url': f"https://www.reddit.com{post.get('permalink', '')}",
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_utc': post.get('created_utc', 0),
                    'selftext': post.get('selftext', '')[:200] + '...' if post.get('selftext') else '',
                    'author': post.get('author', '[deleted]')
                }
                posts.append(post_info)
            
            return posts
        else:
            return []
            
    except Exception as e:
        st.warning(f"Pushshift API error: {str(e)}")
        return []

def generate_search_urls(query):
    """
    Generate manual search URLs as primary solution
    """
    encoded_query = quote(query)
    
    urls = {
        'Reddit Search (Direct)': f"https://www.reddit.com/search/?q={encoded_query}",
        'Google Site Search': f"https://www.google.com/search?q=site:reddit.com+{encoded_query}",
        'DuckDuckGo Site Search': f"https://duckduckgo.com/?q=site:reddit.com+{encoded_query}",
        'Bing Site Search': f"https://www.bing.com/search?q=site:reddit.com+{encoded_query}",
    }
    
    return urls

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
    
    # Important notice about Reddit API
    st.warning("""
    ⚠️ **Important**: Reddit blocks automated requests from cloud hosting services. 
    This app now provides **manual search links** that you can click to find relevant posts.
    
    For automated searching, you need Reddit API credentials (see instructions below).
    """)
    
    # Sidebar for settings
    st.sidebar.header("Search Settings")
    
    # API Configuration
    st.sidebar.subheader("🔑 Reddit API (Optional)")
    use_api = st.sidebar.checkbox("Use Reddit API", help="Requires Reddit app credentials")
    
    if use_api:
        client_id = st.sidebar.text_input("Client ID", type="password")
        client_secret = st.sidebar.text_input("Client Secret", type="password")
        user_agent = st.sidebar.text_input("User Agent", value="RedditSearchApp/1.0")
        
        if st.sidebar.button("ℹ️ How to get API credentials"):
            st.sidebar.markdown("""
            1. Go to https://www.reddit.com/prefs/apps
            2. Click "Create App"
            3. Choose "script" type
            4. Get your Client ID and Secret
            """)
    
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
        
        search_button = st.button("🔍 Find Reddit Posts", type="primary", use_container_width=True)
    
    # Search results
    if search_button and search_query:
        results = []
        
        # Try Reddit API if credentials provided
        if use_api and client_id and client_secret:
            st.info("🔄 Trying Reddit Official API...")
            with st.spinner("Searching with Reddit API..."):
                results = search_with_reddit_api(
                    search_query, client_id, client_secret, user_agent,
                    sort=sort_options[sort_by], 
                    time_filter=time_filters[time_filter],
                    limit=num_results
                )
        
        # Try Pushshift as backup
        if not results:
            st.info("🔄 Trying Pushshift API...")
            with st.spinner("Searching with Pushshift..."):
                results = search_pushshift_api(
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
        
        # Always show manual search options
        st.header("🔗 Manual Search Links")
        st.markdown("**Click these links to search Reddit manually:**")
        
        search_urls = generate_search_urls(search_query)
        
        for search_name, search_url in search_urls.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{search_name}:** [Open Search]({search_url})")
            with col2:
                if st.button(f"📋", key=f"copy_url_{search_name}"):
                    st.code(search_url)
    
    elif search_button and not search_query:
        st.error("Please enter a search query.")
    
    # Instructions
    with st.expander("ℹ️ How to Use This App"):
        st.markdown("""
        ## 🚀 **Quick Start (Manual Search)**
        1. Enter your content in the text area
        2. Review the auto-generated keywords and search query
        3. Click "Find Reddit Posts"
        4. Use the **Manual Search Links** to find relevant posts
        
        ## 🔑 **For Automated Search (Optional)**
        1. Get Reddit API credentials:
           - Go to https://www.reddit.com/prefs/apps
           - Click "Create App" → Choose "script"
           - Copy Client ID and Secret
        2. Enable "Use Reddit API" in sidebar
        3. Enter your credentials
        4. Search automatically!
        
        ## 💡 **Tips**
        - Manual search links work immediately - no setup required
        - Use specific keywords for better results
        - Try different search engines (Google, DuckDuckGo, Bing)
        - Look for posts with good engagement (scores/comments)
        """)

if __name__ == "__main__":
    main()
    
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
