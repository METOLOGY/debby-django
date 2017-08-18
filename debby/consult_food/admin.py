from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core import urlresolvers
from django.utils.safestring import mark_safe

from .models import TaiwanSnackModel, SynonymModel, NutritionModel, FoodModel, ICookIngredientModel


class SynonymModelInline(GenericTabularInline):
    model = SynonymModel


class NutritionModelInline(admin.StackedInline):
    model = NutritionModel


@admin.register(NutritionModel)
class NutritionModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'six_group_portion_image_tag', 'nutrition_amount_image_tag')

    def six_group_portion_image_tag(self, obj):
        if obj.six_group_portion_image:
            return mark_safe('<a href="{}"><img src="{}" width="200" height="200"/></a>'.format(
                obj.six_group_portion_image.url, obj.six_group_portion_image_preview.url))
        else:
            return ''

    def nutrition_amount_image_tag(self, obj):
        if obj.nutrition_amount_image:
            return mark_safe('<a href="{}"><img src="{}" width="200" height="200"/></a>'.format(
                obj.nutrition_amount_image.url, obj.nutrition_amount_image_preview.url))
        else:
            return ''

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
        url = urlresolvers.reverse("admin:consult_food_nutritionmodel_change", args=[obj.nutrition.id])
        return '<a href="%s">%s: %s</a>' % (url, obj.nutrition.id, obj.nutrition.name)

    nutrition_link.allow_tags = True
    nutrition_link.short_description = "營養呈現"


@admin.register(FoodModel)
class FoodModelAdmin(admin.ModelAdmin):
    inlines = [SynonymModelInline]
    list_display = ('id', 'sample_name', 'list_synonyms', 'nutrition_link',)

    def nutrition_link(self, obj):
        url = urlresolvers.reverse("admin:consult_food_nutritionmodel_change", args=[obj.nutrition.id])
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
            url = urlresolvers.reverse("admin:consult_food_nutritionmodel_change", args=[obj.nutrition.id])
            return '<a href="%s">%s: %s</a>' % (url, obj.nutrition.id, obj.nutrition.name)
        else:
            return ''

    nutrition_link.allow_tags = True
    nutrition_link.short_description = "營養呈現"

    source_link.allow_tags = True
    source_link.shot_description = "原連結"
