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

def search_reddit(query, sort='relevance', time_filter='all', limit=25):
    """
    Search Reddit using the JSON API
    """
    try:
        # Clean and encode the query
        encoded_query = quote(query)
        
        # Reddit search URL
        url = f"https://www.reddit.com/search.json"
        
        params = {
            'q': query,
            'sort': sort,
            't': time_filter,
            'limit': limit,
            'type': 'link'
        }
        
        headers = {
            'User-Agent': 'RedditQueryFinder/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        posts = []
        if 'data' in data and 'children' in data['data']:
            for post in data['data']['children']:
                post_data = post['data']
                
                # Extract relevant information
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
        
        return posts
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to Reddit: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        st.error("Error parsing Reddit response")
        return []
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return []

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
        with st.spinner("Searching Reddit..."):
            results = search_reddit(
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
            st.warning("No results found. Try different keywords or adjust your search settings.")
    
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