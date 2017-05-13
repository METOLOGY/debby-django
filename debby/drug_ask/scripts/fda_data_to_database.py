from drug_ask.models import DrugModel

keywords = [
    'metformin',
    'glibenclamide',
    'glipizide',
    'gliclazide',
    'glimepiride',
    'repaglinide',
    'nateglinide',
    'acarbose',
    'miglitol',
    'pioglitazone',
    'sitagliptin',
    'saxagliptin',
    'vildagliptin',
    'linagliptin',
]

with open('../tables/36_2.csv') as file:
    for num, row in enumerate(file):
        content = row.split('\t')
        status = content[1]
        permission_type = content[6]
        chName = content[9]
        engName = content[10]
        mainIng = content[16].lower()

        is_DM_drug = False
        for key in keywords:
            if key in mainIng:
                is_DM_drug = True
                break

        if is_DM_drug and status != '已註銷':
            drug = DrugModel()
            drug.chinese_name = chName
            drug.eng_name = engName
            drug.permission_type = permission_type
            drug.main_ingredient = key
            drug.save()