import logging
from django.shortcuts import render
from .forms import UserInputForm
from .services.leetcode_service import get_recent_accepted_problems, analyze_solved_patterns
from .services.ai_service import get_ai_recommendations

logger = logging.getLogger(__name__)


def dashboard(request):
    form = UserInputForm(request.POST or None)
    context = {'form': form}

    if request.method == 'POST':
        if 'show_recent' in request.POST and form.is_valid():
            username = form.cleaned_data['username'].strip()
            goal = form.cleaned_data['goal']
            try:
                recent = get_recent_accepted_problems(username, limit=20)
                analysis = analyze_solved_patterns(recent)
                request.session['recent_problems'] = recent
                request.session['analysis'] = analysis
                request.session['goal'] = goal
                request.session['username'] = username
                request.session['selected_goal'] = goal
                context.update({
                    'recent_problems': recent,
                    'analysis': analysis,
                    'show_recent': True,
                })
            except Exception as exc:
                logger.exception('Processing failed')
                context['error'] = str(exc)

        elif 'get_recommendations' in request.POST:
            recent = request.session.get('recent_problems')
            analysis = request.session.get('analysis')
            goal = request.session.get('selected_goal')
            if not recent or not analysis or not goal:
                context['error'] = 'No recent problems data. Please start over.'
            else:
                try:
                    recommendations = get_ai_recommendations(recent, analysis, goal, max_recs=8)
                    context.update({
                        'recent_problems': recent,
                        'analysis': analysis,
                        'recommendations': recommendations,
                        'submitted': True,
                    })
                except Exception as exc:
                    logger.exception('Processing failed')
                    context['error'] = str(exc)

    return render(request, 'core/dashboard.html', context)
