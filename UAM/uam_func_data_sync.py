import requests


def uam_func_sync(request,*args):
    try:
        requests.get(args[0]+'/functions_sync/?prj_name='+args[1]+'&client_name='+args[2]+'&prj_uid=' + str(request.user.id) + '&func_module='+args[3]+'&func_page='+args[4])
    except Exception as e:
        print(e)
