"""
Emerald's Killfeed - Embed System Test Commands
Test commands for verifying all embed types work correctly
"""

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

class EmbedTest(commands.Cog):
    """Test commands for the embed system"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="test_killfeed", description="Test killfeed embed")
    async def test_killfeed(self, ctx: discord.ApplicationContext):
        """Test killfeed embed with sample data"""
        data = {
            'killer_name': 'ShadowStrike',
            'killer_faction': 'Ravens',
            'killer_kdr': '2.45',
            'killer_streak': 7,
            'victim_name': 'WastelandWolf',
            'victim_faction': 'Wolves',
            'victim_kdr': '1.89',
            'weapon': 'AK-74',
            'distance': '156'
        }
        
        embed = await EmbedFactory.build('killfeed', data)
        
        # Attach image file for thumbnail
        file = discord.File('assets/Killfeed.png', filename='Killfeed.png')
        await ctx.respond(embed=embed, file=file)
    
    @discord.slash_command(name="test_suicide", description="Test suicide embed")
    async def test_suicide(self, ctx: discord.ApplicationContext):
        """Test suicide embed with sample data"""
        data = {
            'player_name': 'LoneWanderer',
            'faction': 'Outcasts',
            'cause': 'Menu Suicide'
        }
        
        embed = await EmbedFactory.build('suicide', data)
        
        # Attach image file for thumbnail
        file = discord.File('assets/main.png', filename='main.png')
        await ctx.respond(embed=embed, file=file)
    
    @discord.slash_command(name="test_fall", description="Test fall damage embed")
    async def test_fall(self, ctx: discord.ApplicationContext):
        """Test fall damage embed with sample data"""
        data = {
            'player_name': 'CliffDiver',
            'faction': 'Daredevils'
        }
        
        embed = await EmbedFactory.build('fall', data)
        
        # Attach image file for thumbnail
        file = discord.File('assets/main.png', filename='main.png')
        await ctx.respond(embed=embed, file=file)
    
    @discord.slash_command(name="test_slots", description="Test animated slots embed")
    async def test_slots(self, ctx: discord.ApplicationContext):
        """Test animated slots with sample data"""
        data = {
            'win': True,
            'payout': 1200
        }
        
        # Use the animated slots builder
        await EmbedFactory.build_animated_slots(ctx, data)
    
    @discord.slash_command(name="test_roulette", description="Test roulette embed")
    async def test_roulette(self, ctx: discord.ApplicationContext):
        """Test roulette embed with sample data"""
        data = {
            'player_pick': 'Red',
            'result': 'Red 18',
            'win': True,
            'payout': 500,
            'bet_amount': 250
        }
        
        embed = await EmbedFactory.build('roulette', data)
        
        # Attach image file for thumbnail
        file = discord.File('assets/main.png', filename='main.png')
        await ctx.respond(embed=embed, file=file)
    
    @discord.slash_command(name="test_blackjack", description="Test blackjack embed")
    async def test_blackjack(self, ctx: discord.ApplicationContext):
        """Test blackjack embed with sample data"""
        data = {
            'player_hand': 'K♠ A♦',
            'player_total': 21,
            'dealer_hand': 'Q♣ 8♥',
            'dealer_total': 18,
            'outcome': 'BLACKJACK!',
            'payout': 750
        }
        
        embed = await EmbedFactory.build('blackjack', data)
        
        # Attach image file for thumbnail
        file = discord.File('assets/main.png', filename='main.png')
        await ctx.respond(embed=embed, file=file)
    
    @discord.slash_command(name="test_profile", description="Test profile embed")
    async def test_profile(self, ctx: discord.ApplicationContext):
        """Test profile embed with sample data"""
        data = {
            'player_name': 'DeadEyeSniper',
            'faction': 'Rangers',
            'kills': 247,
            'deaths': 89,
            'kdr': '2.78',
            'longest_streak': 15,
            'top_weapon': 'M24 SWS',
            'rival': 'QuickDraw',
            'nemesis': 'GhostReaper'
        }
        
        embed = await EmbedFactory.build('profile', data)
        
        # Attach image file for thumbnail
        file = discord.File('assets/main.png', filename='main.png')
        await ctx.respond(embed=embed, file=file)
    
    @discord.slash_command(name="test_bounty", description="Test bounty embed")
    async def test_bounty(self, ctx: discord.ApplicationContext):
        """Test bounty embed with sample data"""
        data = {
            'target_name': 'BloodHunter',
            'target_faction': 'Reapers',
            'amount': 5000,
            'set_by': 'VengefulSoul',
            'reason': 'Repeated spawn camping',
            'time_remaining': '18h 23m'
        }
        
        embed = await EmbedFactory.build('bounty', data)
        
        # Attach image file for thumbnail
        file = discord.File('assets/Bounty.png', filename='Bounty.png')
        await ctx.respond(embed=embed, file=file)
    
    @discord.slash_command(name="test_admin", description="Test admin embed")
    async def test_admin(self, ctx: discord.ApplicationContext):
        """Test admin embed with sample data"""
        data = {
            'executor': ctx.user.display_name,
            'target': 'TestPlayer',
            'command': '/test_admin',
            'outcome': 'Successfully executed'
        }
        
        embed = await EmbedFactory.build('admin', data)
        
        # Attach image file for thumbnail
        file = discord.File('assets/main.png', filename='main.png')
        await ctx.respond(embed=embed, file=file)

def setup(bot):
    bot.add_cog(EmbedTest(bot))