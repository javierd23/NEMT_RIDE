from django.contrib import admin

from .models import Ride, RideStatus, Ride_Event


@admin.register(RideStatus)
class RideStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'status')
    search_fields = ('status',)


class RideEventInline(admin.TabularInline):
    model = Ride_Event
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('description', 'created_at')


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id_ride', 'status', 'id_rider', 'id_driver', 'pickup_time', 'updated_at')
    list_filter = ('status',)
    search_fields = ('id_rider__email', 'id_driver__email')
    readonly_fields = ('updated_at',)
    autocomplete_fields = ('id_rider', 'id_driver')
    inlines = (RideEventInline,)

    fieldsets = (
        (None, {'fields': ('status', 'id_rider', 'id_driver', 'pickup_time')}),
        ('Pickup location', {'fields': ('pickup_latitude', 'pickup_longitude')}),
        ('Dropoff location', {'fields': ('dropoff_latitude', 'dropoff_longitude')}),
        ('Timestamps', {'fields': ('updated_at',)}),
    )


@admin.register(Ride_Event)
class RideEventAdmin(admin.ModelAdmin):
    list_display = ('id_ride_event', 'id_ride', 'description', 'created_at')
    search_fields = ('id_ride__id_ride', 'description')
    readonly_fields = ('created_at',)
