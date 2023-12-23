from django import forms


class BasicForm(forms.Form):
    name = forms.CharField(
        help_text='Digite o seu nome.',
        template_name='core/custom_field.html'
    )
    age = forms.IntegerField(
        help_text='Digite a sua idade.',
        template_name='core/custom_field.html'
    )

    def __init__(self, *args, **kwargs):
        super(BasicForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
