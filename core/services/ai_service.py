import logging
import os

logger = logging.getLogger(__name__)

AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower()  # gemini only
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

client = None
if AI_PROVIDER == 'gemini':
    try:
        import google.generativeai as genai
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            client = genai
        else:
            logger.warning('GOOGLE_API_KEY not set. Gemini calls will fail.')
    except ImportError:
        logger.exception('google-generativeai module is not installed. Use pip install google-generativeai')
else:
    logger.warning('Only Gemini provider is supported. Set AI_PROVIDER=gemini')


def format_recent_problems(recent_problems):
    lines = []
    for p in recent_problems:
        lines.append(f"- {p['title']} ({p['difficulty']}) [{', '.join(p['topics'] or ['General'])}] -> {p['url']}")
    return '\n'.join(lines)


def get_ai_recommendations(recent_problems, analysis, goal, max_recs=8):
    if client is None:
        raise RuntimeError('Gemini client is not configured. Set GOOGLE_API_KEY.')

    overview = format_recent_problems(recent_problems)
    topic_str = ', '.join([t for t, _ in analysis.get('topic_frequency', [])]) or 'General'

    prompt = f"""You are an intelligent LeetCode coach.
Given the following user data:
- Goal: {goal}
- Recent solved problems:
{overview}
- Difficulty distribution: {analysis.get('difficulty_distribution')}
- Topic frequency: {analysis.get('topic_frequency')}

Identify weak areas and recommend {max_recs} new LeetCode problem suggestions in the user's interest.
For each recommendation, provide:
1) Name
2) Difficulty (Easy/Medium/Hard)
3) Primary topic
4) URL (complete LeetCode problem link)
5) Reason (one or two sentences explaining why this is a good recommendation based on the user's solved patterns)

Return response as JSON array of objects with these keys: name, difficulty, topic, url, reason.
"""

    text = None
    model_candidates = ['gemini-3.6-flash', 'gemini-flash-latest', 'gemini-pro-latest', 'gemini-2.5-flash']
    for model_name in model_candidates:
        try:
            model = client.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            logger.info('Gemini model used: %s', model_name)
            text = response.text if response and hasattr(response, 'text') else None
            break
        except Exception as e:
            error_msg = str(e)
            logger.warning('Gemini model %s failed: %s', model_name, error_msg)
            if 'model_not_found' in error_msg.lower() or 'quota' in error_msg.lower():
                continue
            raise RuntimeError('Failed to fetch recommendations from Gemini: %s' % e)

    if not text:
        raise RuntimeError('Failed to fetch recommendations from Gemini: All models exhausted (possibly due to quota limits). Please check your Google AI API usage at https://ai.google.dev/gemini-api/docs/rate-limits')
    # Try to parse JSON from output
    import json
    try:
        # locate first JSON-like part
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1:
            recs = json.loads(text[start:end + 1])
        else:
            raise ValueError('No JSON found')
    except Exception:
        logger.warning('Could not parse JSON, falling back to text parse')
        # Fallback: no parse
        return [{'name': 'Could not parse AI output', 'difficulty': 'N/A', 'topic': 'N/A', 'url': '#'}]

    recommendations = []
    for item in recs:
        if not isinstance(item, dict):
            continue
        name = item.get('name') or item.get('title') or 'Unknown'
        difficulty = item.get('difficulty') or 'Unknown'
        topic = item.get('topic') or 'General'
        url = item.get('url') or item.get('link') or '#'
        reason = item.get('reason') or item.get('explanation') or 'No explanation provided.'

        recommendations.append({
            'name': name,
            'difficulty': difficulty,
            'topic': topic,
            'url': url,
            'reason': reason,
        })

    return recommendations
