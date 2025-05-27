import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from utils.sftp_client import AsyncSFTPClient

logger = logging.getLogger(__name__)

class GameLogDiscovery:
    """
    Utility class for discovering game log files on remote SFTP servers.
    Implements corrected path logic for finding Deadside.log and CSV files.
    """
    
    def __init__(self, sftp_client: AsyncSFTPClient):
        self.sftp_client = sftp_client
        
    async def discover_deadside_log(self, host: str, server_id: str, username: str, password: str) -> Optional[str]:
        """
        Locate the Deadside.log file on the remote server.
        
        Args:
            host: SFTP server hostname
            server_id: Server ID
            username: SFTP username
            password: SFTP password
            
        Returns:
            Path to the log file if found, None otherwise
        """
        # Construct the path using the correct template with _id
        log_path = f"./{host}_{server_id}/Logs/Deadside.log"
        
        try:
            async with self.sftp_client.get_sftp_client(host, username, password) as sftp:
                try:
                    # Check if file exists
                    stat = await sftp.stat(log_path)
                    logger.info(f"Found Deadside.log at {log_path}")
                    return log_path
                except Exception as e:
                    logger.error(f"Deadside.log not found at {log_path}: {str(e)}")
                    return None
        except Exception as e:
            logger.error(f"SFTP error while discovering log file: {str(e)}")
            return None
            
    async def discover_death_logs(self, host: str, server_id: str, username: str, password: str) -> List[str]:
        """
        Discover CSV death log files on the remote server.
        
        Args:
            host: SFTP server hostname
            server_id: Server ID
            username: SFTP username
            password: SFTP password
            
        Returns:
            List of paths to CSV files
        """
        # Base path for CSV files using the correct template with _id
        csv_pattern = f"./{host}_{server_id}/actual1/deathlogs/**/*.csv"
        
        try:
            # Use glob_files to find all matching CSV files
            csv_files = await self.sftp_client.glob_files(host, username, password, csv_pattern)
            
            if csv_files:
                logger.info(f"Found {len(csv_files)} CSV death log files")
            else:
                logger.warning(f"No CSV death log files found with pattern {csv_pattern}")
                
            return csv_files
        except Exception as e:
            logger.error(f"Error discovering death log CSV files: {str(e)}")
            return []
            
    async def get_latest_logs(self, server_info: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
        """
        Get the latest log files for a server.
        
        Args:
            server_info: Dictionary containing server information
            
        Returns:
            Tuple of (deadside_log_path, list_of_csv_paths)
        """
        host = server_info.get("host")
        server_id = str(server_info.get("_id"))
        username = server_info.get("username")
        password = server_info.get("password")
        
        if not all([host, server_id, username, password]):
            logger.error(f"Missing required server info for log discovery")
            return None, []
            
        # Get both log types in parallel
        deadside_log_task = self.discover_deadside_log(host, server_id, username, password)
        csv_logs_task = self.discover_death_logs(host, server_id, username, password)
        
        deadside_log, csv_logs = await asyncio.gather(deadside_log_task, csv_logs_task)
        
        return deadside_log, csv_logs
