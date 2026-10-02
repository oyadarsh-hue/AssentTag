"""Adopt existing legacy tables, then apply additive chat migrations."""
import importlib
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, migrations
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = 'Validate legacy chat tables and apply the disappearing-message schema.'

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        applied = recorder.applied_migrations()
        tables = set(connection.introspection.table_names())
        # Older copies had live tables but no register/login migration files.
        # Validate every baseline column before recording either baseline.
        adopt = []
        for app in ('register', 'login'):
            if (app, '0001_initial') in applied:
                continue
            migration = importlib.import_module(f'{app}.migrations.0001_initial').Migration
            models = [op for op in migration.operations if isinstance(op, migrations.CreateModel)
                      and op.options.get('managed', True)]
            present = [op.options.get('db_table', f'{app}_{op.name.lower()}') in tables for op in models]
            if not any(present):
                continue
            if not all(present):
                raise CommandError(f'Incomplete legacy {app} schema. Restore or reconcile its tables before upgrading.')
            for op in models:
                table = op.options.get('db_table', f'{app}_{op.name.lower()}')
                with connection.cursor() as cursor:
                    columns = {field.name for field in connection.introspection.get_table_description(cursor, table)}
                expected = set()
                for name, field in op.fields:
                    field.set_attributes_from_name(name)
                    expected.add(field.column)
                if not expected.issubset(columns):
                    raise CommandError(f'Legacy table {table} is missing expected baseline columns; no migration was adopted.')
            adopt.append(app)
        for app in adopt:
            recorder.record_applied(app, '0001_initial')
            self.stdout.write(f'Validated and adopted existing {app} baseline.')
        call_command('migrate', 'login', verbosity=options['verbosity'])
        self.stdout.write(self.style.SUCCESS('Chat timer schema is ready.'))
