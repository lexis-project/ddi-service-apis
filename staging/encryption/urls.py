from django.urls import path
from . import views

urlpatterns = [
    path(
        '',
        views.index,
        name='index'),
    path(
        'encrypt',
        views.encrypt,
        name='encrypt'),
    path(
        'encrypt/<path:req_id>',
        views.encryption_status,
        name='check_status'),
    path(
        'decrypt',
        views.decrypt,
        name='decrypt'),
    path(
        'decrypt/<path:req_id>',
        views.decryption_status,
        name='check_decryption_status'),
    path(
        'compress',
        views.compress,
        name='compress'),
    path(
        'compress/<path:req_id>',
        views.compression_status,
        name='check_status'),
    path(
        'compress_encrypt',
        views.compress_encrypt,
        name='compress_encrypt'),
    path(
        'compress_encrypt/<path:req_id>',
        views.compression_encryption_status,
        name='check_status'),
    path(
        'decrypt_decompress',
        views.decrypt_decompress,
        name='decrypt_decompress'),
    path(
        'decrypt_decompress/<path:req_id>',
        views.decryption_decompression_status,
        name='check_status'),
    path(
        'decompress',
        views.decompress,
        name='compress'),
    path(
        'decompress/<path:req_id>',
        views.decompression_status,
        name='check_status'),
]