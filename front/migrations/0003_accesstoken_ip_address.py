# Generated by Django 4.0 on 2022-05-26 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('front', '0002_accesstoken_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='accesstoken',
            name='ip_address',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
    ]
