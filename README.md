# Django 5.0

04/12/2023

O Django 5.0 foi lançado dia 05 de Dezembro de 2023, e ele funciona no Python...

> **Django 5.0:** Python 3.10, 3.11 e 3.12


## Instalação

Vamos clonar um projeto semi-pronto.

```
git clone https://github.com/rg3915/django5.git
```

## requirements.txt

Veja em `requirements.txt` que temos

```
Django==5.0
django-extensions==3.2.3
psycopg2-binary==2.9.9
python-decouple==3.8
```

## docker-compose.yml

Veja também que temos `docker-compose.yml`

```yml
version: "3.8"

services:
  db:
    container_name: dicas_de_django_db
    image: postgres:14-alpine
    restart: always
    user: postgres  # importante definir o usuário
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - LC_ALL=C.UTF-8
      - POSTGRES_PASSWORD=postgres  # senha padrão
      - POSTGRES_USER=postgres  # usuário padrão
      - POSTGRES_DB=dicas_de_django_db  # necessário porque foi configurado assim no settings
    ports:
      - 5431:5432  # repare na porta externa 5431
    networks:
      - dicas-de-django-network

  pgadmin:
    container_name: dicas_de_django_pgadmin
    image: dpage/pgadmin4
    restart: unless-stopped
    volumes:
       - pgadmin:/var/lib/pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - 5051:80
    networks:
      - dicas-de-django-network


volumes:
  pgdata:
  pgadmin:

networks:
  dicas-de-django-network:
```

## Variáveis de ambiente

* Crie um `.env`

```
SECRET_KEY=yh^oeUiXF)#V5LcpT8$!WR&x2j01dP3BtDsO@Evf(*a6mu%JQr
POSTGRES_DB=dicas_de_django_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5431
```

* Veja como configuramos o `settings.py`

```python
# settings.py

from decouple import config

SECRET_KEY = config('SECRET_KEY')


INSTALLED_APPS = [
    # ...
    'django_extensions',
    'backend.core',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', 'db'),  # postgres
        'USER': config('POSTGRES_USER', 'postgres'),
        'PASSWORD': config('POSTGRES_PASSWORD', 'postgres'),
        # 'db' caso exista um serviço com esse nome.
        'HOST': config('DB_HOST', '127.0.0.1'),
        'PORT': config('DB_PORT', 5431),
    }
}

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR.joinpath('staticfiles')
```


## db_default - valores default no banco de dados

### Exemplo

```python
from django.db import models
from django.db.models.functions import Now


class Todo(models.Model):
    task = models.CharField(max_length=50)
    completed = models.BooleanField(db_default=True)
    created = models.DateTimeField(db_default=Now())

    class Meta:
        verbose_name_plural = 'Todos'

    def __str__(self):
        return self.task
```

Esta opção funciona quando você cria dados por fora da aplicação, ou seja, pelo shell do Django.

```
python manage.py shell_plus

Todo.objects.create(task='Estudar Django 5.0')
```

**Obs:** o `db_default` não aceita referência a outros campos ou modelos. Por exemplo,

```python
from django.db.models import F


class Product(models.Model):
    title = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    discount = models.DecimalField(max_digits=7, decimal_places=2, db_default=F('price') * .9)
```

```
SystemCheckError: System check identified some issues:

ERRORS:
core.Product.discount: (fields.E012) F(price) * Value(0.9) cannot be used in db_default.
```


### PostgreSQL

```
docker container exec -it dicas_de_django_db psql dicas_de_django_db

\dt

SELECT column_name, column_default FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'core_todo';
```

Ou você pode ver isso pelo pgAdmin.

imagem


## GeneratedField

https://www.paulox.net/2023/11/07/database-generated-columns-part-1-django-and-sqlite/

https://www.paulox.net/2023/11/24/database-generated-columns-part-2-django-and-postgresql/


```python
class Travel(models.Model):
    start_date = models.DatetimeField()
    end_date = models.DatetimeField()

    def duration(self):
        return self.end_date - self.start_date
```

Ou


```python

class DurationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(duration=F('end_date') - F('start_date'))


class Travel(models.Model):
    destination = models.CharField(max_length=50)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    objects = DurationManager()

    class Meta:
        ordering = ('start_date',)

    def __str__(self):
        return self.destination
```

```python
python manage.py shell_plus

travel = Travel.objects.first()

travel.duration
datetime.timedelta(days=1, seconds=32400)
```

Mas essas duas opções não existem no banco de dados, portanto não pode ser indexado.


### GeneratedField syntax

```python
class GeneratedField(expression, output_field, db_persist=None, **kwargs):
    ...
```

* `expression` é onde você vai calcular o que você precisa.

* `output_field` geralmente é onde você define o tipo de campo, baseado no Django models.

* `db_persist=True` vai persistir os dados no banco.

### Exemplo

```python
class Travel(models.Model):
    destination = models.CharField(max_length=50)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration = models.GeneratedField(
        expression=F('end_date') - F('start_date'),
        output_field=models.DurationField(),
        db_persist=True,
    )

    class Meta:
        ordering = ('start_date',)

    def __str__(self):
        return self.destination
```

Podemos ver pelo pgAdmin

imagem

ou pelo PostgreSQL

```
docker container exec -it dicas_de_django_db psql dicas_de_django_db

\dt

SELECT column_name, generation_expression, is_generated FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'core_travel';
```


### Exemplo: nome completo


```python
class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ('first_name',)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name or ""}'.strip()

    def __str__(self):
        return self.full_name
```


```
python manage.py shell_plus
```


```python
>>> person = Person.objects.create(first_name='Regis', last_name='Santos')
>>> person.full_name
'Regis Santos'

>>> Person.objects.filter(full_name='Regis Santos')
Traceback (most recent call last):
    raise FieldError(
django.core.exceptions.FieldError: Cannot resolve keyword 'full_name' into field. Choices are: first_name, id, last_name
```

Segundo Paolo Melchiorre, não podemos usar a classe `Concat`, então vamos definir nossa própria classe.

https://www.paulox.net/2023/11/24/database-generated-columns-part-2-django-and-postgresql/#a-calculated-concatenated-field


```python
from django.db.models import Value

class ConcatOp(models.Func):
    arg_joiner = " || "
    function = None
    output_field = models.TextField()
    template = "%(expressions)s"


class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    full_name = models.GeneratedField(
        expression=ConcatOp(
            "first_name", Value(" "), "last_name",
        ),
        output_field=models.TextField(),
        db_persist=True,
    )

    class Meta:
        ordering = ('full_name',)

    def __str__(self):
        return self.full_name
```

### Exemplo: subtotal, vendas

```python
class Product(models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title


class Sale(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    created = models.DateTimeField(db_default=Now())

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f'{str(self.pk).zfill(3)}'


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=7, decimal_places=2)
    subtotal = models.GeneratedField(
        expression=F('quantity') * F('price'),
        output_field=models.DecimalField(max_digits=7, decimal_places=2),
        db_persist=True,
    )

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return f'{self.pk} - {self.sale.pk} - {self.product}'
```

```
python manage.py shell_plus
```

```python
from random import randint, random

products = ("Maçã", "Banana", "Melão", "Melancia", "Morango")

for product in products:
    Product.objects.create(title=product)

person = Person.objects.create(first_name='Regis', last_name='Santos')

sale = Sale.objects.create(person=person)

products = Product.objects.all()

for product in products:
    SaleItem.objects.create(
        sale=sale,
        product=product,
        quantity=randint(1,10),
        price=randint(1,10)*random()
    )
```

```
docker container exec -it dicas_de_django_db psql dicas_de_django_db

\dt

SELECT column_name, generation_expression, is_generated FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'core_saleitem';
```

Agora vamos editar os dados:

```python
for item in SaleItem.objects.all():
    print(item.quantity, item.price, item.subtotal)

>>> sale_item = SaleItem.objects.first()

>>> sale_item
<SaleItem: 5 - 1 - Morango>

>>> sale_item.quantity = 2
>>> sale_item.save()

>>> sale_item.subtotal
Decimal('0.83')

>>> sale_item = SaleItem.objects.first()

>>> sale_item.subtotal
Decimal('1.66')
```


## Mais opções para model field choices

https://docs.djangoproject.com/en/5.0/releases/5.0/#more-options-for-declaring-field-choices

```python
Medal = models.TextChoices("Medal", "GOLD SILVER BRONZE")

# SPORT_CHOICES = [
#     ("Martial Arts", [("judo", "Judo"), ("karate", "Karate")]),
#     ("Racket", [("badminton", "Badminton"), ("tennis", "Tennis")]),
#     ("unknown", "Unknown"),
# ]

SPORT_CHOICES = {  # Using a mapping instead of a list of 2-tuples.
    "Martial Arts": {"judo": "Judo", "karate": "Karate"},
    "Racket": {"badminton": "Badminton", "tennis": "Tennis"},
    "unknown": "Unknown",
}


class Winner(models.Model):
    name = models.CharField(max_length=20)
    medal = models.CharField(max_length=9, choices=Medal.choices)
    sport = models.CharField(max_length=9, choices=SPORT_CHOICES)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
```

## update_or_create

Tem um novo argumento `create_defaults`.

```python
class Article(models.Model):
    title = models.CharField(max_length=100)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='updated_articles',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_articles'
    )

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title
```

```
python manage.py shell_plus
```

Rode os comandos duas vezes.

```python
user = User.objects.first()

Article.objects.update_or_create(
    title='Django 5.0',
    defaults={'updated_by': user},
    create_defaults={'created_by': user}
)

user = User.objects.first()

Article.objects.update_or_create(
    title='Python 3.11.7',
    defaults={'updated_by': user},
    create_defaults={'created_by': user}
)
```

## Django Forms

```
touch backend/core/forms.py
```

### as_field_group


```python
# core/forms.py
from django import forms


class BasicForm(forms.Form):
    name = forms.CharField(
        help_text='Digite o seu nome.'
    )
```

```
python manage.py shell_plus
```

```python
from django.template import Template, Context
from backend.core.forms import BasicForm

context = Context({'form': BasicForm()})
form_template = Template('{{ form }}')

print(form_template.render(context))
```

Veja o resultado com o help_text

Agora se fizermos

```python
field_template = Template('{{ form.name }}')

print(field_template.render(context))
```

Veja o resultado. Cadê o help_text?

```python
field_as_field_group = Template('{{ form.name.as_field_group }}')

print(field_as_field_group.render(context))
```

### Renderizando o template

```
mkdir -p backend/core/templates/core
touch backend/core/templates/core/form.html

touch backend/core/urls.py
```

Edite `urls.py`

```python
# urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('backend.core.urls')),
    path('admin/', admin.site.urls),
]
```

Edite `core/urls.py`

```python
# core/urls.py
from django.urls import path

from .views import form_view


urlpatterns = [
    path('', form_view),
]
```

Edite `core/views.py`

```python
# core/views.py
from django.shortcuts import render
from .forms import BasicForm


def form_view(request):
    template_name = 'core/form.html'
    form = BasicForm()
    context = {'form': form}
    return render(request, template_name, context)
```

Edite `form.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no">
  <link rel="shortcut icon" href="https://www.djangoproject.com/favicon.ico">
  <title>Django 5.0</title>

  <!-- Bootstrap core CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <form>
    <div>
      {{ form.name.as_field_group }}
    </div>
  </form>
</body>
</html>
```

### Custom field

```python
# core/forms.py
from django import forms


class BasicForm(forms.Form):
    name = forms.CharField(
        help_text='Digite o seu nome.',
        template_name='core/custom_field.html'
    )
    age = forms.IntegerField(
        help_text='Digite a sua idade.'
    )

    def __init__(self, *args, **kwargs):
        super(BasicForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
```

Crie `core/templates/core/custom_field.html`

```html
{% if field.use_fieldset %}
  <fieldset>
  {% if field.label %}{{ field.legend_tag }}{% endif %}
{% else %}
  {% if field.label %}{{ field.label_tag }}{% endif %}
{% endif %}
{{ field }}
{{ field.errors }}
{% if field.help_text %}<div class="helptext"{% if field.auto_id %} id="{{ field.auto_id }}_helptext"{% endif %}>{{ field.help_text|safe }}</div>{% endif %}
{% if field.use_fieldset %}</fieldset>{% endif %}
```

Edite `form.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no">
  <link rel="shortcut icon" href="https://www.djangoproject.com/favicon.ico">
  <title>Django 5.0</title>

  <!-- Bootstrap core CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

  <style>
    .helptext {
      margin-top: .25rem;
      color: #6c757d;
      font-size: 80%;
      font-weight: 400;
    }
  </style>
</head>
<body>
  <form class="container mt-5">
    <div>
      {{ form.name.as_field_group }}
    </div>
    <div class="mt-3">
      {{ form.age.as_field_group }}
    </div>
  </form>
</body>
</html>
```