from django.contrib import admin
from core.models import User, Post, Comment


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "email",
        "username",
        "created_at",
        "updated_at"
    )

    list_filter = ("id", "username",)
    search_fields = (
        "first_name",
        "last_name",
        "email",
    )
    ordering = ("-pk",)


class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'publish')
    search_fields = ('title',)
    list_filter = ('slug',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'body', 'user', 'post', 'parent')
    search_fields = ('user__first_name', 'user__last_name',)
    list_filter = ('post__id', 'parent')


admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)

admin.site.site_header = 'Blog CMS'
