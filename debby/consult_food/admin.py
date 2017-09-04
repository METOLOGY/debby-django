from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core import urlresolvers
from django.utils.safestring import mark_safe

from .models import TaiwanSnackModel, SynonymModel, NutritionModel, TFDAModel, ICookIngredientModel, ICookDishModel, WikiFoodTranslateModel


class SynonymModelInline(GenericTabularInline):
    model = SynonymModel


class NutritionModelInline(admin.StackedInline):
    model = NutritionModel


@admin.register(NutritionModel)
class NutritionModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'nutrition_amount_image_tag', 'six_group_portion_image_tag',
                    'gram_tag', 'calories_tag', 'protein_tag', 'fat_tag', 'carbohydrates_tag',
                    'fruit_amount_tag', 'vegetable_amount_tag',
                    'grain_amount_tag', 'protein_food_amount_tag',
                    'diary_amount_tag', 'oil_amount_tag',
                    )

    def six_group_portion_image_tag(self, obj):
        if obj.six_group_portion_image:
            return mark_safe('<a href="{}"><img src="{}" width="150" height="150"/></a>'.format(
                obj.six_group_portion_image.url, obj.six_group_portion_image_preview.url))
        else:
            return ''

    def nutrition_amount_image_tag(self, obj):
        if obj.nutrition_amount_image:
            return mark_safe('<a href="{}"><img src="{}" width="150" height="150"/></a>'.format(
                obj.nutrition_amount_image.url, obj.nutrition_amount_image_preview.url))
        else:
            return ''

    def gram_tag(self, obj):
        return '{:.1f}'.format(obj.gram)

    def calories_tag(self, obj):
        return '{:.1f}'.format(obj.calories)

    def protein_tag(self, obj):
        return '{:.1f}'.format(obj.protein)

    def fat_tag(self, obj):
        return '{:.1f}'.format(obj.fat)

    def carbohydrates_tag(self, obj):
        return '{:.1f}'.format(obj.carbohydrates)

    def fruit_amount_tag(self, obj):
        return '{:.1f}'.format(obj.fruit_amount)

    def vegetable_amount_tag(self, obj):
        return '{:.1f}'.format(obj.vegetable_amount)

    def grain_amount_tag(self, obj):
        return '{:.1f}'.format(obj.grain_amount)

    def protein_food_amount_tag(self, obj):
        return '{:.1f}'.format(obj.protein_food_amount)

    def diary_amount_tag(self, obj):
        return '{:.1f}'.format(obj.diary_amount)

    def oil_amount_tag(self, obj):
        return '{:.1f}'.format(obj.oil_amount)

    six_group_portion_image_tag.short_description = '六大類'
    nutrition_amount_image_tag.short_description = "營養含量"


@admin.register(TaiwanSnackModel)
class TaiwanSnackFoodAdmin(admin.ModelAdmin):
    inlines = [SynonymModelInline]
    list_display = ('id', 'name', 'count_word', 'synonym_fields', 'nutrition_link')
    list_select_related = True
    list_filter = ('name',)

    def synonym_fields(self, obj):
        return obj.list_synonyms()

    synonym_fields.short_description = "代稱"

    def nutrition_link(self, obj):
        url = urlresolvers.reverse("admin:consult_food_nutritionmodel_changelist")
        url = "{}?id={}".format(url, obj.nutrition.id)
        return '<a href="%s">%s: %s</a>' % (url, obj.nutrition.id, obj.nutrition.name)

    nutrition_link.allow_tags = True
    nutrition_link.short_description = "營養 model"


@admin.register(TFDAModel)
class FoodModelAdmin(admin.ModelAdmin):
    inlines = [SynonymModelInline]
    list_display = ('id', 'sample_name', 'list_synonyms', 'nutrition_link',)

    def nutrition_link(self, obj):
        url = urlresolvers.reverse("admin:consult_food_nutritionmodel_changelist")
        url = "{}?id={}".format(url, obj.nutrition.id)
        return '<a href="%s">%s: %s</a>' % (url, obj.nutrition.id, obj.nutrition.name)

    nutrition_link.allow_tags = True
    nutrition_link.short_description = "營養呈現"


@admin.register(ICookIngredientModel)
class ICookIngredientModelAdmin(admin.ModelAdmin):
    inlines = [SynonymModelInline]
    list_display = ('id', 'name', 'source_link', 'nutrition_link',)

    def source_link(self, obj):
        if obj.source.startswith('https'):
            return '<a href={}>第三方網頁</a>'.format(obj.source)
        else:
            return obj.source

    def nutrition_link(self, obj):
        if obj.nutrition:
            url = urlresolvers.reverse("admin:consult_food_nutritionmodel_changelist")
            url = "{}?id={}".format(url, obj.nutrition.id)
            return '<a href="%s">%s: %s</a>' % (url, obj.nutrition.id, obj.nutrition.name)
        else:
            return ''

    nutrition_link.allow_tags = True
    nutrition_link.short_description = "營養呈現"

    source_link.allow_tags = True
    source_link.short_description = "原連結"


@admin.register(ICookDishModel)
class ICookDishModelAdmin(admin.ModelAdmin):
    inlines = [SynonymModelInline]
    list_display = ('id', 'name', 'source_link',
                    'nutrition_amount_image_tag', 'six_group_portion_image_tag', 'nutrition_link')

    def source_link(self, obj):
        source_id = obj.source_url.rsplit('/', 1)[-1]
        return '<a href={}>ICook 編號:{}</a>'.format(obj.source_url, source_id)

    def nutrition_link(self, obj):
        if obj.nutrition:
            url = urlresolvers.reverse("admin:consult_food_nutritionmodel_changelist")
            url = "{}?id={}".format(url, obj.nutrition.id)
            return '<a href="%s">%s: %s</a>' % (url, obj.nutrition.id, obj.nutrition.name)
        else:
            return ''

    def six_group_portion_image_tag(self, obj):
        nutrition = obj.nutrition
        if nutrition.six_group_portion_image:
            return mark_safe('<a href="{}"><img src="{}" width="150" height="150"/></a>'.format(
                nutrition.six_group_portion_image.url, nutrition.six_group_portion_image_preview.url))
        else:
            return ''

    def nutrition_amount_image_tag(self, obj):
        nutrition = obj.nutrition
        if nutrition.nutrition_amount_image:
            return mark_safe('<a href="{}"><img src="{}" width="150" height="150"/></a>'.format(
                nutrition.nutrition_amount_image.url, nutrition.nutrition_amount_image_preview.url))
        else:
            return ''

    six_group_portion_image_tag.short_description = '六大類'
    nutrition_amount_image_tag.short_description = "營養含量"

    nutrition_link.allow_tags = True
    nutrition_link.short_description = "營養 model"

    source_link.allow_tags = True
    source_link.short_description = "ICook 連結"


@admin.register(SynonymModel)
class SynonymModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'synonym', 'content_type', 'object_id',
                    'source_link')
    search_fields = ('synonym',)

    def source_link(self, obj):
        nutrition = obj.content_object.nutrition
        url = urlresolvers.reverse("admin:consult_food_nutritionmodel_changelist")
        url = "{}?id={}".format(url, nutrition.id)

        return '<a href="%s">%s: %s</a>' % (url, nutrition.id, nutrition.name)

    source_link.allow_tags = True
    source_link.short_description = "營養連結"

@admin.register(WikiFoodTranslateModel)
class WikiTranslateModelAdmin(admin.ModelAdmin):
    list_display = ('english', 'chinese', )
    fields = ('english', 'chinese', )
    search_fields = ('english', 'chinese', )