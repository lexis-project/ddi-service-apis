"""
Auth backend using LRZ kennung

"""


from mozilla_django_oidc.auth import OIDCAuthenticationBackend

#If other claims need to be added, change the user model, eg. as shown by
#https://wsvincent.com/django-custom-user-model-tutorial/

class MyOIDCAB(OIDCAuthenticationBackend):
    def update_user(self, user, claims):
        print("claims=<%s>"%claims)
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.irods_name = claims.get('preferred_username', '')
        user.save()

        return user

    def create_user(self, claims):
        user = super(MyOIDCAB, self).create_user(claims)
        return self.update_user (user, claims)

