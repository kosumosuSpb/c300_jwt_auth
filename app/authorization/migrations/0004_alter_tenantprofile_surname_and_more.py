# Generated by Django 4.2.3 on 2023-08-16 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authorization', '0003_tenantprofile_rooms_userdata_old_numbers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenantprofile',
            name='surname',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Отчество'),
        ),
        migrations.AlterField(
            model_name='workerprofile',
            name='surname',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Отчество'),
        ),
    ]
