from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'api.users'

    def ready(self):
        from . import signals
