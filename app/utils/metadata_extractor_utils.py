from app.config import settings
from app.services.crypto import decrypt
from app.services.metadata_extractor import PostgresExtractor, MetadataExtractor

DRIVER_TO_METADATA_EXTRACTOR_TYPE = {
    'postgresql': PostgresExtractor
}


async def get_metadata_extractor_by_conn_string(conn_string: str) -> MetadataExtractor:
    decrypted_conn_string = decrypt(settings.encryption_key, bytes.fromhex(conn_string))
    if decrypted_conn_string:
        decrypted_conn_string = decrypted_conn_string.decode('utf-8')
        driver = decrypted_conn_string.split('://', maxsplit=1)[0]
        metadata_extractor_class = DRIVER_TO_METADATA_EXTRACTOR_TYPE[driver]
        metadata_extractor: MetadataExtractor = metadata_extractor_class(conn_string=decrypted_conn_string)
        return metadata_extractor
