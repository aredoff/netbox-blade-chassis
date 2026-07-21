from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dcim', '0237_module_remove_local_context_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceBayTemplateLayout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_x', models.PositiveIntegerField(default=0, help_text='Horizontal slot index within the row (0-based, left to right).', verbose_name='position X')),
                ('position_y', models.PositiveIntegerField(default=0, help_text='Row index within the chassis (0-based, top to bottom).', verbose_name='position Y')),
                ('device_bay_template', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='blade_layout', to='dcim.devicebaytemplate')),
            ],
            options={
                'verbose_name': 'device bay template layout',
                'verbose_name_plural': 'device bay template layouts',
                'ordering': ('position_y', 'position_x'),
            },
        ),
    ]
