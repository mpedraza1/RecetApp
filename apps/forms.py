import re
from django import forms
from .models import Usuarios, Roles

# Formulario LOGIN normal (para usuarios ya registrados)
class LoginForm(forms.Form):
    correo = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

# Formulario SOLO CORREO (Para validar Primer Ingreso o Recuperación)
class ValidarCorreoForm(forms.Form):
    correo = forms.EmailField(
        label="Ingresa tu correo autorizado",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'})
    )

# Formulario NUEVA CONTRASEÑA
class NuevaPasswordForm(forms.Form):
    password = forms.CharField(
        label="Crea tu contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirmar = forms.CharField(
        label="Repite la contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    # 1. VALIDACIÓN DE REQUISITOS (Largo, Mayúscula, Símbolo)
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        # A) Validar Largo Mínimo (8 caracteres)
        if len(password) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")

        # B) Validar al menos una Mayúscula
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("La contraseña debe incluir al menos una letra mayúscula.")

        # C) Validar al menos un Símbolo
        # Buscamos cualquier carácter que NO sea letra ni número
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError("La contraseña debe incluir al menos un símbolo (@, #, $, etc).")

        return password

    # 2. VALIDACIÓN DE COINCIDENCIA (Ya la tenías, se mantiene igual)
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirmar")
        
        # Solo comparamos si p1 pasó las validaciones anteriores
        if p1 and p2 and p1 != p2:
            self.add_error('confirmar', "Las contraseñas no coinciden.")
        
        return cleaned_data

class UsuarioAdminForm(forms.ModelForm):
    # Campo para seleccionar Rol (Dropdown)
    id_rol = forms.ModelChoiceField(
        queryset=Roles.objects.all(),
        label="Rol",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Campo para el Estado (Manual, ya que es un número en la BD)
    ESTADOS = [
        (1, 'Activo'),
        (0, 'Inactivo'),
    ]
    estado = forms.ChoiceField(
        choices=ESTADOS, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Usuarios
        fields = ['nombre', 'correo', 'id_rol', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
