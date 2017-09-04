import csv
import os
import re

import django

from debby import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'debby.settings'
django.setup()


def run():
    from consult_food.models import SynonymModel
    chat_table_dir = os.path.join(settings.PROJECT_DIR, 'chat_table')
    file_path = os.path.join(chat_table_dir, 'food_names.csv')
    queries = SynonymModel.objects.all().distinct().values_list('synonym', flat=True)

    with open(file_path, 'w', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
        for name in queries:
            name = re.sub(r'\([^)]*\)', '', name)
            name = re.sub(r'\([^)]*\）', '', name)
            name = re.sub(r'\([^)]*', '', name)
            name = name.rstrip(')')
            writer.writerow([name, name])


if __name__ == '__main__':
    run()
