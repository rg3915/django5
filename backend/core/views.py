from django.shortcuts import render
from .forms import BasicForm


def form_view(request):
    template_name = 'core/form.html'
    form = BasicForm()
    context = {'form': form}
    return render(request, template_name, context)
