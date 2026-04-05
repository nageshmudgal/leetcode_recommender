from django import forms

GOAL_CHOICES = [
    ('switch_prep', 'Switch Preparation'),
    ('interview_prep', 'Interview Preparation'),
    ('practice', 'Casual Practice'),
]

class UserInputForm(forms.Form):
    username = forms.CharField(
        max_length=50,
        required=True,
        label='LeetCode Username',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. leetcode_user'})
    )
    goal = forms.ChoiceField(
        choices=GOAL_CHOICES,
        required=True,
        label='Goal',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
