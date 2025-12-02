from django.shortcuts import redirect
from functools import wraps

def login_personalizado_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Aquí verificamos TU lógica manual
        if 'usuario_id' not in request.session:
            # Si no hay usuario en sesión, al login
            return redirect('login')
        
        # Si hay usuario, ejecuta la vista normal
        return view_func(request, *args, **kwargs)
    return _wrapped_view