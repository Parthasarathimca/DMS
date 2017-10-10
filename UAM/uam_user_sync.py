from django.contrib.auth.models import User
import requests,json

def syncUser(request,*args):
    if request.user.is_authenticated and request.user.is_superuser:
        users = list(User.objects.all().values('id','username'));data = json.dumps(users)
        try:
            result = requests.post(args[0]+"/user_sync/",{'prj_name':args[1], 'client_name':args[2],'prj_user':data})
            print(result.status_code)
            if result.status_code == 200:
                return json.dumps(json.loads(result.content.decode('utf-8')))
            else:
                return json.dumps({'res': 'Invalid Server IP'})
        except Exception as e:
            return json.dumps({'res':e})
    else:
        return json.dumps({'res':'No Access to Sync'})
