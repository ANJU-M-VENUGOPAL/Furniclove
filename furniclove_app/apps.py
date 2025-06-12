from django.apps import AppConfig


class FurnicloveAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'furniclove_app'

    def ready(self):
        import furniclove_app.signals

    
