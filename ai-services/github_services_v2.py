import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import streamlit as st # Import Streamlit for caching
import os
GITHUB_API_URL = "https://api.github.com/search/repositories"
GITHUB_REPO_API_URL = "https://api.github.com/repos"

# --- OPTIMIZATION ---
# We will cache the results of API calls to avoid re-fetching data.
# `ttl` (time-to-live) is set to 3600 seconds (1 hour).
# This means the app will only re-fetch data from GitHub for the same
# query if it's been more than an hour.

class GitHubAnalyzer:
    """Professional GitHub repository analyzer for comprehensive research"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {"Authorization": f"token {token}"} if token else {}
        self.request_count = 0
        self.last_request_time = datetime.now()
    
    def _rate_limit_check(self):
        """Implement rate limiting to avoid API limits"""
        current_time = datetime.now()
        if (current_time - self.last_request_time).total_seconds() < 1:
            # Removed time.sleep(1) as it blocks the app.
            # Caching will reduce the number of calls, making this less necessary.
            pass
        self.last_request_time = current_time
        self.request_count += 1
    
    def _truncate_description(self, text: str, word_limit: int = 25) -> str:
        """Enhanced description truncation with better formatting"""
        if not text:
            return "No description available."
        
        # Clean up the text
        text = text.strip().replace('\n', ' ').replace('\r', '')
        words = text.split()
        
        if len(words) > word_limit:
            truncated = ' '.join(words[:word_limit])
            return f"{truncated}..."
        return text
    
    # --- OPTIMIZATION ---
    # Cache this function. It will be called for each of the top 5 repos.
    # Caching this makes the N+1 problem much less painful.
    @st.cache_data(ttl=3600)
    def get_repository_details(self, repo_full_name: str) -> Dict:
        """Get detailed information about a specific repository"""
        print(f"GitHub API: Fetching details for {repo_full_name}") # For debugging cache
        self._rate_limit_check()
        
        try:
            url = f"{GITHUB_REPO_API_URL}/{repo_full_name}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            repo_data = response.json()
            
            # Get additional metrics
            languages_url = repo_data.get('languages_url')
            
            # Fetch languages
            languages = {}
            if languages_url:
                lang_response = requests.get(languages_url, headers=self.headers)
                if lang_response.status_code == 200:
                    languages = lang_response.json()
            
            return {
                'name': repo_data.get('name'),
                'full_name': repo_data.get('full_name'),
                'description': repo_data.get('description'),
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'language': repo_data.get('language'),
                'languages': languages,
                'created_at': repo_data.get('created_at'),
                'updated_at': repo_data.get('updated_at'),
                'size': repo_data.get('size', 0),
                'open_issues': repo_data.get('open_issues_count', 0),
                'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
                'topics': repo_data.get('topics', []),
                'html_url': repo_data.get('html_url'),
                'clone_url': repo_data.get('clone_url'),
                'has_wiki': repo_data.get('has_wiki', False),
                'has_documentation': repo_data.get('has_wiki', False) or 'readme' in repo_data.get('name', '').lower()
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repository details for {repo_full_name}: {e}")
            return {}
    
    def analyze_repository_quality(self, repo_details: Dict) -> Dict:
        """Analyze repository quality metrics"""
        quality_score = 0
        factors = []
        
        # Stars-based scoring (normalized)
        stars = repo_details.get('stars', 0)
        if stars > 1000:
            quality_score += 30
            factors.append("High community adoption")
        elif stars > 100:
            quality_score += 20
            factors.append("Good community interest")
        elif stars > 10:
            quality_score += 10
            factors.append("Some community validation")
        
        # Activity scoring
        updated_at = repo_details.get('updated_at')
        if updated_at:
            try:
                last_update = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
                days_since_update = (datetime.now() - last_update).days
                
                if days_since_update < 30:
                    quality_score += 25
                    factors.append("Recently active")
                elif days_since_update < 90:
                    quality_score += 15
                    factors.append("Moderately active")
                elif days_since_update < 365:
                    quality_score += 5
                    factors.append("Somewhat maintained")
            except ValueError:
                pass
        
        # Documentation scoring
        if repo_details.get('has_documentation'):
            quality_score += 15
            factors.append("Well documented")
        
        # License scoring
        if repo_details.get('license'):
            quality_score += 10
            factors.append("Open source licensed")
        
        # Language diversity
        languages = repo_details.get('languages', {})
        if len(languages) > 1:
            quality_score += 10
            factors.append("Multi-language implementation")
        
        # Topics/tags
        topics = repo_details.get('topics', [])
        if len(topics) > 3:
            quality_score += 10
            factors.append("Well categorized")
        
        quality_level = "Excellent" if quality_score >= 70 else \
                        "Good" if quality_score >= 50 else \
                        "Fair" if quality_score >= 30 else "Basic"
        
        return {
            'score': min(quality_score, 100),
            'level': quality_level,
            'factors': factors
        }

# --- OPTIMIZATION ---
# This is the main function called by Streamlit. Caching it provides
# the biggest performance boost.
@st.cache_data(ttl=3600)
def search_github_repos(query: str, limit: int = 10, sort_by: str = 'stars') -> List[str]:
    """
    Enhanced GitHub repository search with comprehensive analysis
    
    Args:
        query (str): The search term
        limit (int): Maximum number of results
        sort_by (str): Sort criteria ('stars', 'forks', 'updated')
    
    Returns:
        list: Formatted repository information with analysis
    """
    print(f"GitHub API: Searching for {query}") # For debugging cache
    if not query:
        return []

    analyzer = GitHubAnalyzer()
    
    # Enhanced search parameters
    params = {
        'q': f"{query} stars:>10",  # Filter for repositories with some community validation
        'sort': sort_by,
        'order': 'desc',
        'per_page': min(limit, 30)  # GitHub API limit
    }
    
    try:
        analyzer._rate_limit_check()
        token = os.environ.get("GITHUB_TOKEN")  # optional
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"

        response = requests.get(GITHUB_API_URL, params=params, headers=headers, timeout=10)

        response.raise_for_status()
        data = response.json()
        
        formatted_repos = []
        items = data.get('items', [])[:limit]
        
        for i, item in enumerate(items, 1):
            # Get detailed analysis for top repositories
            if i <= 5:  # Detailed analysis for top 5 results
                # This call will now hit the cache if seen before
                detailed_info = analyzer.get_repository_details(item['full_name'])
                quality_analysis = analyzer.analyze_repository_quality(detailed_info)
                
                # Enhanced formatting with quality metrics
                repo_info = format_repository_with_analysis(item, detailed_info, quality_analysis, i)
            else:
                # Basic formatting for remaining repositories
                repo_info = format_repository_basic(item, i)
            
            formatted_repos.append(repo_info)
            
        return formatted_repos

    except requests.exceptions.RequestException as e:
        print(f"Error calling GitHub API: {e}")
        # Return a user-friendly error message
        return [f"⚠️ **GitHub API Error**: Could not fetch repositories. Please try again later."]

def format_repository_with_analysis(item: Dict, details: Dict, quality: Dict, rank: int) -> str:
    """Format repository with comprehensive analysis"""
    
    name = item['full_name']
    url = item['html_url']
    stars = item['stargazers_count']
    forks = item.get('forks_count', 0)
    language = item.get('language', 'Not specified')
    
    description = details.get('description') or item.get('description', '')
    truncated_desc = GitHubAnalyzer()._truncate_description(description)
    
    # Quality indicators
    quality_emoji = "🌟" if quality['level'] == "Excellent" else \
                    "⭐" if quality['level'] == "Good" else \
                    "✨" if quality['level'] == "Fair" else "📦"
    
    # Activity status
    updated_at = details.get('updated_at', '')
    activity_status = ""
    if updated_at:
        try:
            last_update = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
            days_ago = (datetime.now() - last_update).days
            if days_ago < 30:
                activity_status = "🟢 Active"
            elif days_ago < 90:
                activity_status = "🟡 Recent"
            else:
                activity_status = "🔴 Stable"
        except ValueError:
            activity_status = "❓ Unknown"
    
    # License info
    license_info = details.get('license', 'No license')
    license_emoji = "📄" if license_info and license_info != 'No license' else "⚠️"
    
    # Language info with percentage
    languages = details.get('languages', {})
    primary_language = language
    if languages:
        total_bytes = sum(languages.values())
        if total_bytes > 0:
            lang_percentages = []
            for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:3]:
                percentage = (bytes_count / total_bytes) * 100
                lang_percentages.append(f"{lang} ({percentage:.1f}%)")
            primary_language = ", ".join(lang_percentages)
    
    # Topics
    topics = details.get('topics', [])
    topics_str = ""
    if topics:
        topics_str = f"\n    🏷️ **Topics:** {', '.join(topics[:5])}"
    
    return f"""**{rank}. {quality_emoji} [{name}]({url})**
    ⭐ **{stars:,}** stars | 🍴 **{forks:,}** forks | {activity_status}
    💻 **Languages:** {primary_language}
    {license_emoji} **License:** {license_info}
    📝 **Description:** {truncated_desc}
    📊 **Quality Score:** {quality['score']}/100 ({quality['level']})
    ✅ **Key Factors:** {', '.join(quality['factors'][:3])}{topics_str}
    
    ---"""

def format_repository_basic(item: Dict, rank: int) -> str:
    """Basic repository formatting for lower-ranked results"""
    name = item['full_name']
    url = item['html_url']
    stars = item['stargazers_count']
    language = item.get('language', 'Not specified')
    description = item.get('description', 'No description available.')
    
    truncated_desc = GitHubAnalyzer()._truncate_description(description, 15)
    
    return f"""**{rank}. 📦 [{name}]({url})**
    ⭐ {stars:,} stars | 💻 {language}
    📝 {truncated_desc}
    
    ---"""

def analyze_repository_trends(repositories: List[str]) -> Dict:
    """Analyze trends across multiple repositories"""
    
    if not repositories:
        return {}
    
    # Extract data from formatted repositories
    total_repos = len(repositories)
    languages = {}
    total_stars = 0
    license_types = {}
    activity_levels = {'Active': 0, 'Recent': 0, 'Stable': 0}
    
    for repo in repositories:
        # Simple parsing of formatted strings (in a real implementation, 
        # you'd store structured data)
        if '⭐' in repo:
            try:
                stars_part = repo.split('⭐')[1].split('stars')[0].strip()
                stars = int(stars_part.replace('**', '').replace(',', ''))
                total_stars += stars
            except (ValueError, IndexError):
                pass
        
        # Activity parsing
        if '🟢 Active' in repo:
            activity_levels['Active'] += 1
        elif '🟡 Recent' in repo:
            activity_levels['Recent'] += 1
        elif '🔴 Stable' in repo:
            activity_levels['Stable'] += 1
    
    avg_stars = total_stars // total_repos if total_repos > 0 else 0
    
    return {
        'total_repositories': total_repos,
        'average_stars': avg_stars,
        'total_stars': total_stars,
        'activity_distribution': activity_levels,
        'dominant_activity': max(activity_levels.items(), key=lambda x: x[1])[0] if activity_levels else 'Unknown'
    }

def generate_research_summary(query: str, repositories: List[str]) -> str:
    """Generate a comprehensive research summary"""
    
    if not repositories:
        return "No repositories found for analysis."
    
    trends = analyze_repository_trends(repositories)
    
    summary = f"""## 📊 **Repository Research Summary**

**Search Query:** `{query}`

### 📈 **Quantitative Analysis**
- **Repositories Analyzed:** {trends.get('total_repositories', 0)}
- **Total Community Stars:** {trends.get('total_stars', 0):,}
- **Average Stars per Repository:** {trends.get('average_stars', 0):,}
- **Dominant Activity Level:** {trends.get('dominant_activity', 'Unknown')}

### 🔍 **Key Insights**

**Community Validation:**
The search results indicate a {'strong' if trends.get('average_stars', 0) > 500 else 'moderate' if trends.get('average_stars', 0) > 100 else 'emerging'} community interest in this domain.

**Development Activity:**
Most repositories show {'active development' if trends.get('dominant_activity') == 'Active' else 'stable maintenance' if trends.get('dominant_activity') == 'Stable' else 'recent activity'}, suggesting {'ongoing innovation' if trends.get('dominant_activity') == 'Active' else 'mature solutions' if trends.get('dominant_activity') == 'Stable' else 'evolving ecosystem'}.

**Implementation Readiness:**
The variety and quality of available repositories provide {'excellent' if trends.get('total_repositories', 0) >= 10 else 'good' if trends.get('total_repositories', 0) >= 5 else 'basic'} foundation for learning and reference.

### 🎯 **Research Recommendations**

1. **Primary References:** Focus on top 3-5 repositories with highest quality scores
2. **Technology Patterns:** Study common architectural approaches across projects
3. **Community Practices:** Review documentation and coding standards
4. **Innovation Opportunities:** Identify gaps in existing solutions

### 📚 **Academic Value**
This repository collection provides substantial academic reference material with proven implementation examples and active community discussion."""
    
    return summary

def search_advanced_repos(query: str, filters: Dict = None) -> List[str]:
    """Advanced repository search with custom filters"""
    
    default_filters = {
        'language': None,
        'min_stars': 10,
        'max_age_days': None,
        'has_license': True,
        'exclude_forks': True
    }
    
    if filters:
        default_filters.update(filters)
    
    # Build advanced query
    search_terms = [query]
    
    if default_filters['language']:
        search_terms.append(f"language:{default_filters['language']}")
    
    if default_filters['min_stars']:
        search_terms.append(f"stars:>={default_filters['min_stars']}")
    
    if default_filters['exclude_forks']:
        search_terms.append("fork:false")
    
    if default_filters['max_age_days']:
        cutoff_date = (datetime.now() - timedelta(days=default_filters['max_age_days'])).strftime('%Y-%m-%d')
        search_terms.append(f"pushed:>={cutoff_date}")
    
    advanced_query = ' '.join(search_terms)
    
    # This will now use the cached version of search_github_repos
    return search_github_repos(advanced_query, limit=15)

def get_repository_recommendations(idea: str, current_repos: List[str]) -> str:
    """Get personalized repository recommendations based on project idea"""
    
    # Extract keywords from idea for targeted search
    keywords = extract_idea_keywords(idea)
    
    recommendations = []
    
    # Search for complementary repositories
    for keyword in keywords[:3]:  # Top 3 keywords
        # This will also use the cache
        specific_repos = search_github_repos(f"{keyword} tutorial example", limit=3)
        recommendations.extend(specific_repos[:2])  # Top 2 from each search
    
    if not recommendations:
        return "No specific recommendations available at this time."
    
    return f"""## 🎯 **Personalized Repository Recommendations**

Based on your project idea: *"{idea}"*

### 📚 **Complementary Learning Resources**

{chr(10).join(recommendations)}

### 💡 **How to Use These Resources**
1. **Study Implementation Patterns** - Analyze code structure and design decisions
2. **Understand Best Practices** - Review documentation and coding standards  
3. **Identify Integration Opportunities** - Look for compatible libraries and frameworks
4. **Learn from Community** - Study issues, pull requests, and discussions

### 🔗 **Integration Strategy**
Consider how concepts from these repositories can be adapted and integrated into your unique solution."""

def extract_idea_keywords(idea: str) -> List[str]:
    """Extract relevant keywords from project idea for targeted search"""
    
    # Common technical keywords and their variations
    keyword_map = {
        'web': ['website', 'web app', 'frontend', 'backend'],
        'mobile': ['app', 'android', 'ios', 'mobile'],
        'ai': ['artificial intelligence', 'machine learning', 'neural'],
        'data': ['database', 'analytics', 'visualization'],
        'game': ['gaming', 'game development', 'unity'],
        'automation': ['bot', 'script', 'automated'],
        'api': ['rest', 'graphql', 'microservice'],
        'security': ['authentication', 'encryption', 'secure']
    }
    
    idea_lower = idea.lower()
    found_keywords = []
    
    for base_keyword, variations in keyword_map.items():
        if base_keyword in idea_lower or any(var in idea_lower for var in variations):
            found_keywords.append(base_keyword)
    
    # Add specific words from the idea that might be technical terms
    words = idea_lower.split()
    technical_words = [word for word in words if len(word) > 4 and word.isalpha()]
    found_keywords.extend(technical_words[:3])
    
    return list(dict.fromkeys(found_keywords))  # Remove duplicates while preserving order