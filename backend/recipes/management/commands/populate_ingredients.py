import json
from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Command to unpack initial ingridents from json_file.
    """
    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        file_name = options['json_file']
        try:
            path = settings.BASE_DIR / 'data_copy' / file_name
            with open(path, encoding='utf-8') as file:
                ingredients = json.load(file)
                for i in ingredients:
                    Ingredient.objects.create(
                        name=i.get('name'),
                        measurement_unit=i.get('measurement_unit'),
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Загружен файл {file_name} на: {len(ingredients)}'
                ))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Загрузка окнчена с ошибкой! \
                    Файл {file_name} не загружен: {e}'
                )
            )
