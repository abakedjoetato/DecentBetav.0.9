import discord
from discord.ext import commands
from typing import List, Optional

class ServerAutocomplete:
    """
    Utility class to handle server name autocompletion for Discord slash commands.
    This replaces direct server_id inputs with user-friendly server names.
    """
    
    @staticmethod
    async def get_servers_for_guild(guild_id: int, db_client):
        """
        Fetch servers associated with a specific guild from the database.
        
        Args:
            guild_id: The Discord guild ID
            db_client: MongoDB client instance
            
        Returns:
            List of server documents containing name and ID
        """
        # Assuming db_client is your MongoDB connection
        servers_collection = db_client.get_collection("servers")
        cursor = servers_collection.find({"guild_id": guild_id})
        
        servers = []
        async for server in cursor:
            servers.append(server)
        
        return servers
    
    @staticmethod
    async def autocomplete_server_name(ctx: discord.AutocompleteContext):
        """
        Autocomplete callback for server names based on the guild context.
        
        Args:
            ctx: The Discord autocomplete context
            
        Returns:
            List of server names for the autocomplete dropdown
        """
        # Get bot instance from context
        bot = ctx.bot
        guild_id = ctx.interaction.guild_id
        
        # Get servers for this guild from the database
        servers = await ServerAutocomplete.get_servers_for_guild(guild_id, bot.db_client)
        
        # Return server names for the autocomplete
        return [
            discord.OptionChoice(name=server.get("name", "Unknown"), value=str(server["_id"]))
            for server in servers
        ]
    
    @staticmethod
    def get_server_id_from_name(server_name: str, servers: List[dict]) -> Optional[str]:
        """
        Convert a server name to its corresponding server_id.
        
        Args:
            server_name: The name of the server
            servers: List of server documents
            
        Returns:
            The server ID if found, None otherwise
        """
        for server in servers:
            if server.get("name") == server_name:
                return str(server["_id"])
        return None


class AutocompleteCog(commands.Cog):
    """
    Cog providing server name autocomplete functionality for slash commands.
    """
    
    def __init__(self, bot):
        self.bot = bot
        
    # This is an example of how to use the autocomplete in a slash command
    @discord.slash_command(name="example", description="Example command using server autocomplete")
    @discord.option(
        name="server",
        description="Select a server",
        autocomplete=ServerAutocomplete.autocomplete_server_name
    )
    async def example_command(self, ctx, server: str):
        """Example command showing how to use server autocomplete"""
        # Here server is the server_id value from the autocomplete
        await ctx.respond(f"Selected server ID: {server}")
        
    # Add additional commands that need autocomplete here
        
def setup(bot):
    bot.add_cog(AutocompleteCog(bot))
