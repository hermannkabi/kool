from django.db import models
from django.contrib.auth.models import User 

class Transaction(models.Model):
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='from_set')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='to_set')
    amount = models.FloatField()
    date_sent = models.DateTimeField('date sent')
    notes = models.CharField(max_length=150, default='')
    group_id = models.PositiveSmallIntegerField("group id", blank=True, null=True)
    
        

    def __str__(self):
        return self.from_user.username.capitalize() + " => " + self.to_user.username.capitalize() + " (" + str(self.amount) + ")"
    


class Group(models.Model):
    
    group_name = models.CharField(max_length=150)
    members = models.ManyToManyField(User)
    desc = models.CharField(max_length=255, default='')


    def __str__(self):
        return "Grupp: " + self.group_name

    def __unicode__(self):
        return 



class UserPrefs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group_id = models.PositiveSmallIntegerField(null=True)