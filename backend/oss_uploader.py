"""阿里云 OSS 上传与签名 URL 生成"""

import os
import logging
import oss2
from urllib.parse import quote

from config import Config

logger = logging.getLogger(__name__)

_bucket = None


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

    if Config.OSS_CDN_DOMAIN:
        # 使用 CDN 域名：生成 OSS 签名 URL 后替换域名
        url = bucket.sign_url('GET', oss_key, expires, params=params)
        # 替换 OSS endpoint 为 CDN 域名
        oss_host = f'{Config.OSS_BUCKET_NAME}.{Config.OSS_ENDPOINT}'
        cdn_domain = Config.OSS_CDN_DOMAIN
        if not cdn_domain.startswith('http'):
            cdn_domain = f'https://{cdn_domain}'
        url = url.replace(f'https://{oss_host}', cdn_domain)
        url = url.replace(f'http://{oss_host}', cdn_domain)
    else:
        url = bucket.sign_url('GET', oss_key, expires, params=params)

    return url


def delete_from_oss(oss_key):
    """从 OSS 删除文件"""
    try:
        bucket = _get_bucket()
        bucket.delete_object(oss_key)
        logger.info(f'已从 OSS 删除: {oss_key}')
    except Exception as e:
        logger.warning(f'OSS 删除失败: {oss_key}, {e}')
