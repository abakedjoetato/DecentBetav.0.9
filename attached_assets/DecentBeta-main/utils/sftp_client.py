import asyncio
import asyncssh
import logging
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class AsyncSFTPClient:
    """
    Asynchronous SFTP client using asyncssh instead of paramiko.
    Provides pooled connections and non-blocking file operations.
    """
    
    def __init__(self):
        self.connection_pool: Dict[str, asyncssh.SSHClientConnection] = {}
        self.sftp_clients: Dict[str, asyncssh.SFTPClient] = {}
        
    @asynccontextmanager
    async def get_connection(self, host: str, username: str, password: str, port: int = 22):
        """
        Context manager to get or create an SSH connection.
        
        Args:
            host: SFTP server hostname
            username: SFTP username
            password: SFTP password
            port: SFTP port (default 22)
            
        Yields:
            An active SSH connection
        """
        conn_key = f"{username}@{host}:{port}"
        
        try:
            # Try to use existing connection
            if conn_key in self.connection_pool:
                conn = self.connection_pool[conn_key]
                if not conn.is_closed():
                    logger.debug(f"Using existing SSH connection to {conn_key}")
                    yield conn
                    return
                else:
                    # Remove closed connection
                    del self.connection_pool[conn_key]
                
            # Create new connection using the exact format specified in diagnostic
            logger.info(f"Creating new SSH connection to {conn_key}")
            conn = await asyncssh.connect(
                host, 
                username=username, 
                password=password, 
                port=port, 
                known_hosts=None
            )
            self.connection_pool[conn_key] = conn
            yield conn
            
        except asyncssh.Error as e:
            logger.error(f"SFTP handshake failed for {conn_key} - Host: {host}, Port: {port}, Username: {username}, Error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"SSH connection error to {conn_key} - Host: {host}, Port: {port}, Username: {username}, Error: {str(e)}")
            raise
            
    @asynccontextmanager
    async def get_sftp_client(self, host: str, username: str, password: str, port: int = 22):
        """
        Context manager to get or create an SFTP client.
        
        Args:
            host: SFTP server hostname
            username: SFTP username
            password: SFTP password
            port: SFTP port (default 22)
            
        Yields:
            An active SFTP client
        """
        conn_key = f"{username}@{host}:{port}"
        
        try:
            # Get SSH connection
            async with self.get_connection(host, username, password, port) as conn:
                # Create SFTP client
                sftp = await conn.start_sftp_client()
                try:
                    yield sftp
                finally:
                    if sftp:
                        sftp.exit()
        except Exception as e:
            logger.error(f"SFTP client error for {conn_key}: {str(e)}")
            raise
            
    async def close_all(self):
        """Close all connections in the pool"""
        for key, conn in self.connection_pool.items():
            try:
                if conn:
                    logger.debug(f"Closing SSH connection to {key}")
                    conn.close()
            except Exception as e:
                logger.debug(f"Error closing connection {key}: {e}")
        self.connection_pool.clear()
        
    async def list_directory(self, host: str, username: str, password: str, directory: str = "./") -> List[str]:
        """
        List files in a directory on the SFTP server.
        
        Args:
            host: SFTP server hostname
            username: SFTP username
            password: SFTP password
            directory: Directory path to list
            
        Returns:
            List of filenames in the directory
        """
        async with self.get_sftp_client(host, username, password) as sftp:
            try:
                files = await sftp.listdir(directory)
                return [str(f) for f in files]
            except asyncssh.SFTPError as e:
                logger.error(f"Failed to list directory {directory}: {str(e)}")
                return []
                
    async def read_file(self, host: str, username: str, password: str, filepath: str) -> Optional[str]:
        """
        Read a file from the SFTP server.
        
        Args:
            host: SFTP server hostname
            username: SFTP username
            password: SFTP password
            filepath: Path to the file to read
            
        Returns:
            File content as string or None if error
        """
        async with self.get_sftp_client(host, username, password) as sftp:
            try:
                async with sftp.open(filepath, 'r') as file:
                    content = await file.read()
                    return content.decode('utf-8')
            except (asyncssh.SFTPError, UnicodeDecodeError) as e:
                logger.error(f"Failed to read file {filepath}: {str(e)}")
                return None
                
    async def glob_files(self, host: str, username: str, password: str, pattern: str) -> List[str]:
        """
        Find files matching a glob pattern on the SFTP server.
        
        Args:
            host: SFTP server hostname
            username: SFTP username
            password: SFTP password
            pattern: Glob pattern to match
            
        Returns:
            List of matching file paths
        """
        async with self.get_sftp_client(host, username, password) as sftp:
            try:
                paths = await sftp.glob(pattern)
                return [str(path) for path in paths]
            except asyncssh.SFTPError as e:
                logger.error(f"Failed to glob files with pattern {pattern}: {str(e)}")
                return []
