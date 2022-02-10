from irods.session import iRODSSession
from irods.access import iRODSAccess

token = ""
session = iRODSSession(host="lexis-lb-1.srv.lrz.de", port=1247, authentication_scheme='openid',
         openid_provider='keycloak_openid',
        zone="LRZLexisZone", access_token=token, user="lrz_rods",
        block_on_authURL=False)

# Adds federated user own rights
coll = session.collections.get("/LRZLexisZone/user")
for col_proj in coll.subcollections:
   print(col_proj.name)
   for col in col_proj.subcollections:
      print (col.name)
      try:
        fed_user = col.name
        acl_user = iRODSAccess("own", col.path, fed_user, "IT4ILexisZone")
        session.permissions.set(acl_user, admin=True)
      except:
        print(col.name + " failed")


# adds rodsadmin as owner of users directories and /user/<project>/

coll = session.collections.get("/LRZLexisZone/user")
for col_proj in coll.subcollections:
   print(col_proj.name)
   acl_project = iRODSAccess("own", col_proj.path, "rodsadmin", "LRZLexisZone")
   session.permissions.set(acl_project)
   for col in col_proj.subcollections:
      print (col.name)
      try:
        fed_user = col.name
        acl_user = iRODSAccess("own", col.path, "rodsadmin", "LRZLexisZone")
        session.permissions.set(acl_user, admin=True)
        acl_user2 = iRODSAccess('inherit', col.path)
        session.permissions.set(acl_user2)
      except:
        print(col.name + " failed")


# Adds rodsadmin as owner of projects under /project and /public
coll = session.collections.get("/LRZLexisZone/project")
coll2 = session.collections.get("/LRZLexisZone/public")
for col_proj in coll.subcollections:
  acl_project = iRODSAccess("own", col_proj.path, "rodsadmin", "LRZLexisZone")
  session.permissions.set(acl_project)
for col_public in coll2.subcollections:
  acl_public = iRODSAccess("own", col_public.path, "rodsadmin", "LRZLexisZone")
  session.permissions.set(acl_public)

# Go over all user project dir, enable inheritance and put user from all zones access to own
session = iRODSSession(host='irods.it4i.lexis.tech', port=1247, user='rods', password='', zone='IT4ILexisZone')
coll = session.collections.get("/IT4ILexisZone/user")
for col_proj in coll.subcollections:
  print("Checking project: " + col_proj.name)
  for col_user in col_proj.subcollections:
    print (col_user.name)
    try:
      user = col_user.name
      acl_user_lrz = iRODSAccess('own', col_user.path, user, "LRZLexisZone")
      acl_user_it4i = iRODSAccess('own', col_user.path, user, "IT4ILexisZone")
      acl_user = iRODSAccess('inherit', col_user.path)
      session.permissions.set(acl_user_lrz, recursive=True, admin=True)
      session.permissions.set(acl_user_it4i, recursive=True, admin=True)
      session.permissions.set(acl_user, admin=True)
    except:
      print("Failed for user " + col_user.name + " in project " + col_proj.name)

#Go over all home dirs and set inheritance to True
session = iRODSSession(host='lexis-lb-1.srv.lrz.de', port=1247, user='rods', password='', zone='LRZLexisZone')
coll = session.collections.get("/LRZLexisZone/home")
for col in coll.subcollections:
      print (col.name)
      if "IT4ILexisZone" not in col.name:
        try:
          print(col.path)
          acl_home = iRODSAccess('inherit', col.path)
          session.permissions.set(acl_home, admin=True)
        except:
          print("Failed to set inheritance for user: " + col.name)
