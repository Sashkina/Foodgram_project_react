import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient

PATH_TO_UPLOAD = '/Users/kristina/Dev/foodgram-project-react/data/'

class Command(BaseCommand):
    help = 'Наполняет БД из csv'
    def handle(self, *args, **kwargs):
        try:
            with open(
                (PATH_TO_UPLOAD + 'ingredients.csv'),
                encoding='utf8'
            ) as file:
                reader = csv.reader(file)
                for row in reader:
                    Ingredient.objects.get_or_create(
                        name=row[0],
                        measurement_unit=row[1]
                    )
                print('ingredients.csv успешно загружено')
        except Exception:
            print('Сбой загрузки ingredients.csv')
