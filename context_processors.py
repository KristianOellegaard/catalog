from models import Category
def basket(request):
    if request.session.has_key("basket"):
        return {'basket': request.session["basket"]}
    else:
        return {'basket': []}
        
def categories(request):
    return {'categories': Category.objects.all()}