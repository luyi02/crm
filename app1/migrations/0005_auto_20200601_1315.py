# Generated by Django 2.1 on 2020-06-01 05:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0004_auto_20200531_1325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courserecord',
            name='outline',
            field=models.TextField(verbose_name='本节课程大纲'),
        ),
    ]
