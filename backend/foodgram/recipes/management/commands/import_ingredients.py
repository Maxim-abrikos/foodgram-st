from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from recipes.models import ProductComponent
import json


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default='data/ingredients.json',
            help=_('Путь к JSON файлу с продуктами (относительно корня проекта)') 
        )
        
    def handle(self, *args, **options):
        file_path = options['path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                ingredients = [
                    ProductComponent(
                        **{'title': item['name'], 'unit_type': item['measurement_unit']}
                    )
                    for item in json.load(file)
                ]

                existing_count = ProductComponent.objects.count()
                
                ProductComponent.objects.bulk_create(ingredients, ignore_conflicts=True)
                
                added_count = ProductComponent.objects.count() - existing_count

                self.stdout.write(
                    self.style.SUCCESS(
                        _(f'Успешно импортировано {added_count} из {len(ingredients)} ингредиентов')
                    )
                )


        except Exception as e:
            self.stdout.write(
            self.style.ERROR(_(f'Ошибка при обработке файла {file_path}: {e}'))
            )