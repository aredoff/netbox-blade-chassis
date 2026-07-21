from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from dcim.api.serializers_.racks import RackElevationDetailFilterSerializer
from dcim.api.serializers_.rackunits import RackUnitSerializer
from dcim.models import Rack

from netbox_blade_chassis.svg.racks import BladeChassisRackElevationSVG


class RackElevationAPIView(APIView):
    queryset = Rack.objects.all()

    def get(self, request, pk):
        rack = get_object_or_404(Rack.objects.restrict(request.user, 'view'), pk=pk)
        serializer = RackElevationDetailFilterSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(serializer.errors, 400)

        data = serializer.validated_data

        if data['render'] == 'svg':
            highlight_params = []
            for param in request.GET.getlist('highlight'):
                try:
                    highlight_params.append(param.split(':', 1))
                except ValueError:
                    pass

            drawing = BladeChassisRackElevationSVG(
                rack,
                user=request.user,
                unit_width=data['unit_width'],
                unit_height=data['unit_height'],
                legend_width=data['legend_width'],
                margin_width=data['margin_width'],
                include_images=data['include_images'],
                base_url=request.build_absolute_uri('/'),
                highlight_params=highlight_params,
            )
            return HttpResponse(drawing.render(data['face']).tostring(), content_type='image/svg+xml')

        elevation = rack.get_rack_units(
            face=data['face'],
            user=request.user,
            exclude=data['exclude'],
            expand_devices=data['expand_devices'],
        )

        if q := data['q']:
            q = q.lower()
            elevation = [
                unit for unit in elevation
                if q in str(unit['id']) or q in str(unit['name']).lower()
            ]

        rack_units = RackUnitSerializer(elevation, many=True, context={'request': request})
        return Response(rack_units.data)
