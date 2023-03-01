from bot.datastore.storage import MinioProvider
from bot.fuzzing.corpus_manager import CORPUS_FILES_SYNC_TIMEOUT, legalize_corpus_files, legalize_filenames
from bot.system import environment, shell


class StatsStorage(object):
    """Minio Storage Stats."""

    def __init__(self,
                 bucket_name,
                 bucket_path='/',
                 log_results=True,
                 ):
        """Inits the Corpus.

    Args:
      bucket_name: Name of the bucket for corpus synchronization.
      bucket_path: Path in the bucket where the corpus is stored.
    """
        self._bucket_name = bucket_name
        self._bucket_path = bucket_path

    @property
    def bucket_name(self):
        return self._bucket_name

    @property
    def bucket_path(self):
        return self._bucket_path

    def get_storage_path(self, suffix='', MINIOPREFIX="http://"):
        """Build corpus GCS URL for gsutil.
    Returns:
      A string giving the GCS URL.
    """
        url = MINIOPREFIX + environment.get_value("MINIO_HOST") + '/' + self.bucket_name + self.bucket_path + suffix
        if not url.endswith('/'):
            # Ensure that the bucket path is '/' terminated. Without this, when a
            # single file is being uploaded, it is renamed to the trailing non-/
            # terminated directory name instead.
            url += '/'
        return url

    def get_storage_provider(self):
        return MinioProvider()

    def rsync_from_disk(self,
                        directory,
                        timeout=CORPUS_FILES_SYNC_TIMEOUT,
                        delete=True):
        """Upload local files to Storage and remove files which do not exist locally.

    Args:
      directory: Path to directory to sync from.
      timeout: Timeout for gsutil.
      delete: Whether or not to delete files on GCS that don't exist locally.

    Returns:
      A bool indicating whether or not the command succeeded.
    """
        storage_provider = self.get_storage_provider()
        legalize_corpus_files(directory)
        return storage_provider.sync_folder_from(directory, self.get_storage_path())

    def rsync_to_disk(self,
                      directory,
                      timeout=CORPUS_FILES_SYNC_TIMEOUT,
                      delete=True):
        """Run gsutil to download corpus files from GCS.

    Args:
      directory: Path to directory to sync to.
      timeout: Timeout for gsutil.
      delete: Whether or not to delete files on disk that don't exist locally.

    Returns:
      A bool indicating whether or not the command succeeded.
    """
        shell.create_directory(directory, create_intermediates=True)

        storage_provider = self.get_storage_provider()
        return storage_provider.sync_folder_from(directory, self.get_storage_path())

    def upload_files(self, file_paths):
        """Upload files to the Storage.

    Args:
      file_paths: A sequence of file paths to upload.

    Returns:
      A bool indicating whether or not the command succeeded.
    """
        if not file_paths:
            return True

        # Get a new file_paths iterator where all files have been renamed to be
        # legal on Windows.
        file_paths = legalize_filenames(file_paths)
        storage_provider = self.get_storage_provider()
        storage_provider.sync_folder_to(file_paths, self.get_storage_path())