from rest_framework import serializers

from files.models import DataSource


class UserFileSerializer(serializers.ModelSerializer):

    class Meta():
        model = DataSource
        fields = "__all__"