"""阿里云 OSS 上传与签名 URL 生成"""

import os
import logging
import oss2
from urllib.parse import quote

from config import Config

logger = logging.getLogger(__name__)

_bucket = None


def _normalize_endpoint(endpoint):
    if not endpoint:
        return ''
    if endpoint.startswith('http://'):
        return endpoint[len('http://'):]
    if endpoint.startswith('https://'):
        return endpoint[len('https://'):]
    return endpoint


def _derive_public_endpoint():
    # 优先使用显式配置，其次将 -internal endpoint 退化为公网 endpoint
    if Config.OSS_PUBLIC_ENDPOINT:
        return _normalize_endpoint(Config.OSS_PUBLIC_ENDPOINT)
    ep = _normalize_endpoint(Config.OSS_ENDPOINT)
    return ep.replace('-internal.', '.')


def _get_bucket():
    global _bucket
    if _bucket is None:
        auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
        endpoint = Config.OSS_ENDPOINT
        if not endpoint.startswith('http'):
            endpoint = f'https://{endpoint}'
        _bucket = oss2.Bucket(auth, endpoint, Config.OSS_BUCKET_NAME)
    return _bucket


def upload_to_oss(local_path, oss_key):
    """上传本地文件到 OSS，完成后删除本地文件"""
    bucket = _get_bucket()
    logger.info(f'开始上传到 OSS: {oss_key}')
    bucket.put_object_from_file(oss_key, local_path)
    logger.info(f'OSS 上传完成: {oss_key}')
    # 删除本地文件，释放服务器磁盘
    try:
        os.remove(local_path)
        logger.info(f'已删除本地文件: {local_path}')
    except OSError as e:
        logger.warning(f'删除本地文件失败: {e}')


def generate_signed_url(oss_key, filename, expires=300):
    """生成带签名的临时下载 URL（默认 5 分钟有效）"""
    bucket = _get_bucket()

    # Content-Disposition 使浏览器触发下载而不是播放
    params = {
        'response-content-disposition': f'attachment; filename="{quote(filename)}"'
    }

    # 先生成签名 URL，再替换 host，避免上传和下载必须共用同一个 endpoint
    url = bucket.sign_url('GET', oss_key, expires, params=params)

    upload_host = f"{Config.OSS_BUCKET_NAME}.{_normalize_endpoint(Config.OSS_ENDPOINT)}"
    if Config.OSS_CDN_DOMAIN:
        download_origin = Config.OSS_CDN_DOMAIN
        if not download_origin.startswith('http'):
            download_origin = f'https://{download_origin}'
    else:
        public_host = f"{Config.OSS_BUCKET_NAME}.{_derive_public_endpoint()}"
        download_origin = f'https://{public_host}'

    url = url.replace(f'https://{upload_host}', download_origin)
    url = url.replace(f'http://{upload_host}', download_origin)

    return url


def delete_from_oss(oss_key):
    """从 OSS 删除文件"""
    try:
        bucket = _get_bucket()
        bucket.delete_object(oss_key)
        logger.info(f'已从 OSS 删除: {oss_key}')
    except Exception as e:
        logger.warning(f'OSS 删除失败: {oss_key}, {e}')
