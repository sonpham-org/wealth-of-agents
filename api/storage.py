"""
Cloud storage manager for simulation outputs
Supports multiple storage backends (S3, GCS, local)
"""
import os
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False


class StorageManager:
    """Manages storage of simulation outputs to cloud and local filesystem"""
    
    def __init__(self, storage_type: str = "local", bucket_name: Optional[str] = None):
        """
        Initialize storage manager
        
        Args:
            storage_type: 'local', 's3', or 'gcs'
            bucket_name: Name of cloud storage bucket (required for cloud storage)
        """
        self.storage_type = storage_type
        self.bucket_name = bucket_name
        # Use /app/data/output for persistent storage on Railway (volume mount)
        data_dir = os.getenv("DATA_DIR", "/app/data" if os.path.exists("/app/data") else ".")
        self.local_base_path = Path(data_dir) / "output"
        self.local_base_path.mkdir(parents=True, exist_ok=True)
        
        if storage_type == "s3":
            if not S3_AVAILABLE:
                raise ImportError("boto3 not installed. Run: pip install boto3")
            self.s3_client = boto3.client('s3')
            if not bucket_name:
                raise ValueError("bucket_name required for S3 storage")
    
    def save_simulation_output(self, run_id: str, output_dir: Path) -> Dict[str, Any]:
        """
        Save simulation output to configured storage
        
        Args:
            run_id: Unique identifier for the simulation run
            output_dir: Local directory containing simulation outputs
            
        Returns:
            Dict with storage location information
        """
        result = {
            "run_id": run_id,
            "storage_type": self.storage_type,
            "timestamp": datetime.now().isoformat(),
            "files": []
        }
        
        if self.storage_type == "local":
            # Already saved locally, just record the location
            result["location"] = str(output_dir.absolute())
            result["files"] = [str(f.relative_to(output_dir)) for f in output_dir.rglob("*") if f.is_file()]
            
        elif self.storage_type == "s3":
            # Upload all files to S3
            uploaded_files = self._upload_to_s3(run_id, output_dir)
            result["location"] = f"s3://{self.bucket_name}/{run_id}/"
            result["files"] = uploaded_files
            
        return result
    
    def _upload_to_s3(self, run_id: str, output_dir: Path) -> list:
        """Upload all files in output directory to S3"""
        uploaded_files = []
        
        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                # Create S3 key maintaining directory structure
                relative_path = file_path.relative_to(output_dir)
                s3_key = f"{run_id}/{relative_path}"
                
                try:
                    # Upload file
                    self.s3_client.upload_file(
                        str(file_path),
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={
                            'Metadata': {
                                'run_id': run_id,
                                'uploaded_at': datetime.now().isoformat()
                            }
                        }
                    )
                    uploaded_files.append(str(relative_path))
                    print(f"✓ Uploaded: {s3_key}")
                except ClientError as e:
                    print(f"✗ Failed to upload {file_path}: {e}")
        
        return uploaded_files
    
    def get_simulation_output(self, run_id: str, output_path: Optional[Path] = None) -> Path:
        """
        Retrieve simulation output from storage
        
        Args:
            run_id: Unique identifier for the simulation run
            output_path: Local path to download to (creates temp if None)
            
        Returns:
            Path to local directory containing outputs
        """
        if self.storage_type == "local":
            return self.local_base_path / run_id
            
        elif self.storage_type == "s3":
            if output_path is None:
                output_path = Path(f"/tmp/simulation_outputs/{run_id}")
            
            output_path.mkdir(parents=True, exist_ok=True)
            self._download_from_s3(run_id, output_path)
            return output_path
        
        raise ValueError(f"Unknown storage type: {self.storage_type}")
    
    def _download_from_s3(self, run_id: str, output_path: Path):
        """Download all files for a run from S3"""
        # List all objects with the run_id prefix
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=f"{run_id}/")
        
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                s3_key = obj['Key']
                # Remove run_id prefix to get relative path
                relative_path = s3_key[len(f"{run_id}/"):]
                local_file = output_path / relative_path
                
                # Create parent directories
                local_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    self.s3_client.download_file(
                        self.bucket_name,
                        s3_key,
                        str(local_file)
                    )
                    print(f"✓ Downloaded: {relative_path}")
                except ClientError as e:
                    print(f"✗ Failed to download {s3_key}: {e}")
    
    def list_runs(self) -> list:
        """List all available simulation runs"""
        if self.storage_type == "local":
            if not self.local_base_path.exists():
                return []
            return [d.name for d in self.local_base_path.iterdir() if d.is_dir()]
            
        elif self.storage_type == "s3":
            # List unique run_id prefixes
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Delimiter='/'
            )
            
            if 'CommonPrefixes' not in response:
                return []
            
            return [prefix['Prefix'].rstrip('/') for prefix in response['CommonPrefixes']]
        
        return []
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a simulation run from storage"""
        if self.storage_type == "local":
            run_path = self.local_base_path / run_id
            if run_path.exists():
                shutil.rmtree(run_path)
                return True
            return False
            
        elif self.storage_type == "s3":
            # Delete all objects with run_id prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=f"{run_id}/")
            
            objects_to_delete = []
            for page in pages:
                if 'Contents' in page:
                    objects_to_delete.extend([{'Key': obj['Key']} for obj in page['Contents']])
            
            if objects_to_delete:
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                return True
            return False
        
        return False


# Singleton instance
_storage_manager = None

def get_storage_manager() -> StorageManager:
    """Get or create the global storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        # Check environment variables for configuration
        storage_type = os.getenv("STORAGE_TYPE", "local")
        bucket_name = os.getenv("S3_BUCKET_NAME")
        
        _storage_manager = StorageManager(
            storage_type=storage_type,
            bucket_name=bucket_name
        )
    
    return _storage_manager
