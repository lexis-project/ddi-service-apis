from django.urls import (path)
from django.conf.urls import (url)
from django_tus.views import TusUpload

from . import (views, globus_views, irods_setup_views, irods_user, irods_project,
               irods_listing, dataset, tus, staging)

urlpatterns = [
    path('', views.index, name='index'),
    path('dataset', dataset.Datasets, name='datasets'),
    path('dataset/download', dataset.DatasetDownload, name='datasetDownload'),
#GET downloads
#PUT creates a new dataset or adds subdatasets
#{push_methods"ssh", "grid", "globus", "directupload","empty"
#file="file contents", used in directupload
#compress_method='file' 'tar' 'targz', ...
#URL="url", used in others
#name="dataset name",
#access="user", "project", "public"
#project=""
#metadata=[]
#}
#receive an identifier back (collectionid), which can be low-level queried to see if complete/obsolete (error in transfer)/in progress

#same parameters as above, except no push_method, no compress_method
#    path('dataset/listing', views.Listing, name='Listing'),

#prior to dataset upload, user can check for permissions to submit a dataset.
#GET
#{access="user", "project", "public", 
#project=""}
#return 403 or 200 as appropriate
    path ('dataset/checkpermission', dataset.DatasetCheckPermissionAPI, name='DatasetCheckPermission'),


#get  success/failure/in progress
#parameter identifier back (collectionid) from 'dataset'
#internally metadata read.
    path('dataset/search/metadata', dataset.SearchMeta),

    path ('dataset/listing', irods_listing.ListDatasetAPI),

    path('token', views.getToken, name='getToken'),
    path('validate_token', views.validateToken, name='validateToken'),
#This gives the public key of the server
#Internally, call to low-level routines
    path('cert', views.cert, name='cert'),
#User creation. Inputs: irods username, keycloak code (aua), irods usertype, irods zone
#User is added to public group so he can access public data.
#In the view, replication can be requested. Call low-level on both irods servers as-needed.
#    path('user/create', view.CreateUser, name='createUser'),
#User deletion. Cascade delete all his data
#    path('user/delete', view.DeleteUser, name='deleteUser'),

#Admin requests that user joins a project
#inputs: irods username, irods zone, array of (group, project)
#User is added to group if needed
#project directories are created, access rights are applied to these directories
#     path('user/addToProjects', views.addToProjects, name='userAddToProjects')



    path('globus', globus_views.globusTransfer, name='globus'),




#irods initialization (once)
#POST
    path('initialize', irods_setup_views.initializeIrods, name='initializeIrods'),


#irods creation of user
#POST
#parameters: "username", "id"
#These correspond to keycloaks Username and ID
#DELETE
#parameters: "username"
    path('user', irods_user.userIrods, name='UserAPI'),

    path('admin', irods_user.adminIrods, name='AdminAPI'),
    path('support', irods_user.supportIrods, name='SupportAPI'),

#irods creation of project
#POST
#parameters: "name"
#DELETE
#parameters: "name"
    path('project', irods_project.projectIrods, name='ProjectAPI'),

#irods add/remove user to project
#POST
#parameters: "username", "projectname"
#DELETE
#parameters: "username", "projectname"
    path('project/user', irods_project.projectUserIrods, name ='ProjectUserAPI'),

#irods add/remove admin status of user to project
#POST
#parameters: "username", "projectname"
#DELETE
#parameters: "username", "projectname"
    path('project/admin', irods_project.projectAdminIrods, name ='ProjectAdminAPI'),
    url(r'^upload/$', tus.tusUpload, name='tus_upload'),
    url(r'^upload/(?P<resource_id>[0-9a-z-]+)$', tus.tusUpload, name='tus_upload_chunks'),

    path('staging/download', staging.download, name='stage_download'),
]

