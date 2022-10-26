# Generated by Django 4.0.6 on 2022-07-19 02:31

from django.db import migrations, models
import django.db.models.deletion
import jsoneditor.fields.django3_jsonfield


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0002_alter_electionseason_tallied_results_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='party',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='elections.politicalparty'),
        ),
        migrations.AlterField(
            model_name='electionseason',
            name='tallied_results',
            field=jsoneditor.fields.django3_jsonfield.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='governmentposition',
            name='college',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='elections.college'),
        ),
        migrations.AlterField(
            model_name='politicalparty',
            name='current_officials',
            field=jsoneditor.fields.django3_jsonfield.JSONField(blank=True, null=True),
        ),
    ]