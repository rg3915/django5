from django.db.models import F, Value
from django.db import models
from django.db.models.functions import Now

from django.contrib.auth.models import User


class Todo(models.Model):
    task = models.CharField(max_length=50)
    completed = models.BooleanField(db_default=True)
    created = models.DateTimeField(db_default=Now())

    class Meta:
        verbose_name_plural = 'Todos'

    def __str__(self):
        return self.task


# class Product(models.Model):
#     title = models.CharField(max_length=50)
#     price = models.DecimalField(max_digits=7, decimal_places=2)
#     # discount = models.DecimalField(max_digits=7, decimal_places=2, db_default=F('price') * .9)


# class DurationManager(models.Manager):
#     def get_queryset(self):
#         return super().get_queryset().annotate(duration=F('end_date') - F('start_date'))


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
        ordering = ('first_name',)

    def __str__(self):
        return self.full_name


class Product(models.Model):
    title = models.CharField(max_length=50)

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


Medal = models.TextChoices("Medal", "GOLD SILVER BRONZE")

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
