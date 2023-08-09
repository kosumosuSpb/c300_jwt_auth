# Generated by Django 4.2.3 on 2023-08-08 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authorization', '0005_remove_userdata_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdata',
            name='number',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
        migrations.AlterField(
            model_name='userdata',
            name='type',
            field=models.CharField(blank=True, choices=[('T', 'Tenant'), ('W', 'Worker')], max_length=25, null=True),
        ),
    ]
