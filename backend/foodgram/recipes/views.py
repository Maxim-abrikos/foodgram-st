from django.shortcuts import redirect
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from .models import CookingRecipe


def redirect_to_recipe(request, recipe_id):
    if not CookingRecipe.objects.filter(id=recipe_id).exists():
        raise Http404(_('Некорректная короткая ссылка: рецепт с id={} не найден').format(recipe_id))
        
    return redirect(f'/recipes/{recipe_id}/')
