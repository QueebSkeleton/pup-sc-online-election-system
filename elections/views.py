from django.shortcuts import render

from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'elections/index.html', {})


@login_required
def vote(request):
    return render(request, 'elections/vote.html', {})
