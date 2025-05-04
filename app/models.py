from django.db import models





class UserCache(models.Model):
    """
    [ id, name , email , full_name , username , profile_pic , is_staff , is_active , is_superuser , created_at , updated_at]
    """
    username = models.CharField(max_length=150, unique=True )
    full_name = models.CharField(max_length=100 , null=True)
    profile_pic = models.TextField(null=True)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username



class Tenants(models.Model):
    sub_choices = (
        
        ('1', 'Free'),
        ('2', 'Premium'),
    )
    name = models.CharField(max_length=100,unique=True)
    subscription_plan = models.CharField(choices=sub_choices , max_length=100 , default="1")
    subdomain = models.CharField(max_length=150 ,unique=True)

    def __str__(self):
        return self.name
    

class TenantUsers(models.Model):
    user = models.ForeignKey(UserCache , on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenants , on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.user.username + ' in ' + self.tenant.name




class Community(models.Model):
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenants , on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    


class CommunityMembers(models.Model):
    user = models.ForeignKey(TenantUsers , on_delete=models.CASCADE)
    community = models.ForeignKey(Community , on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenants , on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

class CommunityChats(models.Model):
    CHOISES = (
        ('1' , 'text'),
        ('2' , 'image'),
        ('3' , 'video'),
        ('4' , 'audio'),
    )

    community = models.ForeignKey(Community , on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenants , on_delete=models.CASCADE)
    contenttype = models.CharField(choices=CHOISES,max_length=100)
    content = models.TextField()
    user = models.ForeignKey(TenantUsers , on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.community.name



