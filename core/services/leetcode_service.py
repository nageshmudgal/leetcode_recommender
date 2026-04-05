import logging
from django.core.cache import cache
import requests

logger = logging.getLogger(__name__)

USER_SUBMISSIONS_URL = 'https://leetcode.com/api/submissions/{username}/'
ALL_PROBLEMS_URL = 'https://leetcode.com/api/problems/all/'
GRAPHQL_URL = 'https://leetcode.com/graphql'


def _fetch_user_submissions_graphql(username, limit):
    """Fetch recent public submissions through LeetCode GraphQL endpoint."""
    query = '''
    query recentSubmissions($username: String!, $limit: Int!) {
      recentSubmissionList(username: $username, limit: $limit) {
        id
        title
        titleSlug
        timestamp
        statusDisplay
        url
      }
    }
    '''

    resp = requests.post(
        GRAPHQL_URL,
        json={'query': query, 'variables': {'username': username, 'limit': limit}},
        headers={
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        timeout=20,
    )

    if resp.status_code == 404:
        raise ValueError('User not found')

    try:
        data = resp.json()
    except ValueError:
        raise ValueError('Invalid response from LeetCode GraphQL')

    if data.get('errors'):
        msg = ', '.join([err.get('message', 'unknown') for err in data['errors']])
        raise ValueError(f'LeetCode GraphQL error: {msg}')

    submissions = data.get('data', {}).get('recentSubmissionList', [])
    if not submissions:
        raise ValueError('No recent public submissions found for this user')

    parsed = []
    for item in submissions[:limit]:
        parsed.append({
            'title': item.get('title'),
            'title_slug': item.get('titleSlug'),
            'status_display': item.get('statusDisplay') or 'Unknown',
            'status': item.get('statusDisplay') or 'Unknown',
            'timestamp': item.get('timestamp'),
            'difficulty': 'Unknown',
            'url': item.get('url') or f"https://leetcode.com/problems/{item.get('titleSlug')}/",
        })

    return parsed

    parsed = []
    for item in submissions[:limit]:
        parsed.append({
            'title': item.get('title'),
            'title_slug': item.get('titleSlug'),
            'status_display': item.get('statusDisplay', 'Accepted'),
            'status': item.get('statusDisplay', 'Accepted'),
            'timestamp': item.get('timestamp'),
            'difficulty': item.get('difficulty', 'Unknown') or 'Unknown',
            'url': f"https://leetcode.com/problems/{item.get('titleSlug')}/" if item.get('titleSlug') else None,
        })

    return parsed


def fetch_user_submissions(username, limit=50):
    """Fetch recent submission data from LeetCode public API with GraphQL fallback."""
    cache_key = f'leetcode_submissions_{username}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Prefer GraphQL route; older REST endpoint is unreliable due to auth/401 issues.
    try:
        parsed = _fetch_user_submissions_graphql(username, limit)
    except Exception as e:
        logger.warning('GraphQL fetch failed (%s); falling back to REST endpoint', e)
        url = USER_SUBMISSIONS_URL.format(username=username)
        params = {'offset': 0, 'limit': limit}
        resp = requests.get(url, params=params, timeout=20)

        if resp.status_code == 404:
            raise ValueError('User not found')

        try:
            payload = resp.json()
        except ValueError:
            raise ValueError('Invalid response from LeetCode API')

        if resp.status_code == 401 or payload.get('detail'):
            raise ValueError(f"LeetCode API access error: {payload.get('detail', 'Unauthorized')} - the endpoint may require authentication.")

        parsed = payload.get('submissions_dump', [])
        if not parsed:
            parsed = []

    if not parsed:
        raise ValueError('No submission data available for this user')

    cache.set(cache_key, parsed, 60 * 15)
    return parsed


def fetch_problem_db():
    """Fetch all LeetCode problems for metadata enrichment."""
    cache_key = 'leetcode_problem_db'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    resp = requests.get(ALL_PROBLEMS_URL, timeout=20)
    try:
        all_data = resp.json().get('stat_status_pairs', [])
    except ValueError:
        raise ValueError('Failed to fetch problem database from LeetCode')

    problem_map = {}
    for entry in all_data:
        if not entry.get('stat'):
            continue
        stat = entry['stat']
        slug = stat.get('question__title_slug')
        if not slug:
            continue
        metadata = {
            'title': stat.get('question__title'),
            'slug': slug,
            'difficulty': entry.get('difficulty', {}).get('level'),
            'difficulty_str': entry.get('difficulty', {}).get('level'),
            'topic_tags': [tag.get('name') for tag in entry.get('topicTags', []) if tag.get('name')],
            'url': f'https://leetcode.com/problems/{slug}/',
        }
        # convert numeric difficulty to string
        if metadata['difficulty'] == 1:
            metadata['difficulty_str'] = 'Easy'
        elif metadata['difficulty'] == 2:
            metadata['difficulty_str'] = 'Medium'
        elif metadata['difficulty'] == 3:
            metadata['difficulty_str'] = 'Hard'

        problem_map[slug] = metadata

    cache.set(cache_key, problem_map, 60 * 60)
    return problem_map


def get_recent_accepted_problems(username, limit=20):
    """Return a deduplicated list of recent accepted problems with metadata."""
    submissions = fetch_user_submissions(username, limit=limit * 3)
    problem_db = fetch_problem_db()

    accepted = [s for s in submissions if s.get('status_display') == 'Accepted' or s.get('status') == 'AC']

    seen = set()
    recent = []
    for item in accepted:
        slug = item.get('title_slug') or item.get('titleSlug')
        if not slug or slug in seen:
            continue
        seen.add(slug)
        meta = problem_db.get(slug, {
            'title': item.get('title'),
            'slug': slug,
            'difficulty_str': item.get('difficulty') or 'Unknown',
            'topic_tags': [],
            'url': f'https://leetcode.com/problems/{slug}/',
        })
        recent.append({
            'title': meta['title'],
            'slug': slug,
            'difficulty': meta.get('difficulty_str', 'Unknown'),
            'topics': meta.get('topic_tags', []),
            'url': meta.get('url'),
            'timestamp': item.get('timestamp'),
        })
        if len(recent) >= limit:
            break

    if not recent:
        raise ValueError('No accepted submissions found for this user.')
    return recent


def analyze_solved_patterns(recent_problems):
    """Compute difficulty distribution and topic frequency."""
    difficulty_dist = {'Easy': 0, 'Medium': 0, 'Hard': 0, 'Unknown': 0}
    topic_count = {}

    for p in recent_problems:
        diff = p.get('difficulty', 'Unknown')
        if diff not in difficulty_dist:
            difficulty_dist['Unknown'] += 1
        else:
            difficulty_dist[diff] += 1

        for topic in p.get('topics', []):
            topic_count[topic] = topic_count.get(topic, 0) + 1

    sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
    return {
        'difficulty_distribution': difficulty_dist,
        'topic_frequency': sorted_topics,
    }
