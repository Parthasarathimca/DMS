import requests


def uam_sessions_sync(request,*args):
    try:
        res = requests.get(args[0]+'/sessions_users_sync/?prj_name='+args[1]+'&client_name='+args[2]+'&prj_uid=' + str(request.user.id) + '&session_type='+args[3]+'&session_key='+args[4]+'&client_ip='+args[5]+'&prj_uname='+ str(request.user.username))
        print "response",res.__dict__
    except Exception as e:
        print(e)
