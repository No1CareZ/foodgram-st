import json

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

import constant
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
            path = settings.BASE_DIR / constant.DATA_COPY_PATH / file_name
            with open(path, encoding='utf-8') as file:
                ingredients = json.load(file)
                for ingredient in tqdm(
                    ingredients,
                    desc="Adding ingredients",
                    unit="ingredient"
                ):
                    Ingredient.objects.create(
                        name=ingredient.get('name'),
                        measurement_unit=ingredient.get('measurement_unit'),
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'File named {file_name} has: {len(ingredients)}'
                ))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'''Error! File named {file_name}'''
                    + f''' faild to load: {e}'''
                )
            )
