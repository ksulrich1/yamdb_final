from rest_framework import mixins, viewsets


class ListCreateDestroyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Concrete view for listing a queryset or creating a model instance.
    mixins.CreateModelMixin - create a model instance.
    mixins.ListModelMixin - list a queryset.
    mixins.DestroyModelMixin - Destroy a model instance.
    The GenericViewSet class does not provide any actions by default,
    but does include the base set of generic view behavior, such as
    the `get_object` and `get_queryset` methods.
    """

    pass
