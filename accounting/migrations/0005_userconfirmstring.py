# Generated by Django 5.0.4 on 2024-05-10 15:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0004_alter_customuser_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserConfirmString',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=256)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounting.customuser')),
            ],
            options={
                'db_table': 'user_confirm_string',
                'ordering': ['-create_time'],
            },
        ),
    ]
