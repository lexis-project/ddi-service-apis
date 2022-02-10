import shutil
import os
import hashlib
from keycloak import KeycloakOpenID
from transfer import systems
import json


def get_token():
    keycloak_config = systems.systems['keycloak']

    keycloak_openid = KeycloakOpenID(server_url=keycloak_config['KEYCLOAK_URL'], 
    realm_name = "LEXIS_AAI", 
    client_id=keycloak_config['OIDC_RP_CLIENT_ID'], 
    client_secret_key=keycloak_config['OIDC_RP_CLIENT_SECRET'])

    # Token
    return keycloak_openid.token(os.environ.get("LEXIS_TEST_USER"), os.environ.get("LEXIS_TEST_PASSWORD"), 
        scope = ['openid','profile',' email', 'offline_access'])['access_token']
    
    

    
def generate_dataset(path):
    """
    Create the following structure in path:
        <path>/:
            - dataset/
                - data0.dat
                - data1.dat

    Create archive of it at <path>/dataset.zip.

    Parameters
    ----------
    path - Where to generate the dataset at

    Returns
    -------
    Array of tuples with names and hashes of all files in the dataset.
    """

    dataset_dir = os.path.join(path, 'dataset')
    os.makedirs(dataset_dir)

    # Create a bunch of files in the dir and store their hashes
    hashes = []
    for f in range(2):
        file = os.path.join(dataset_dir, 'data{0}.dat'.format(f))
        hash = generate_file(file, 10)
        hashes.append((file, hash))

    # Create an archive of the directory
    # dataset.zip
    shutil.make_archive(base_name=dataset_dir, root_dir=path, base_dir=dataset_dir, format="zip")
    return hashes


def generate_file(path, size):
    
        random_data = os.urandom(size * 1048576)
        hash = str(hashlib.md5(random_data).hexdigest())

        with open(path, 'wb') as fout:
            fout.write(random_data)
        return hash
    