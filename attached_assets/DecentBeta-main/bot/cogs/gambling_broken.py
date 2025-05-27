"""
Emerald's Killfeed - Advanced Gambling System (PHASE 4)
/slots, /blackjack, /roulette with full animations and EmbedFactory
Must use non-blocking async-safe logic with user-locks
"""

import asyncio
import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Gambling(commands.Cog):
    """
    GAMBLING (PREMIUM)
    - /slots, /blackjack, /roulette with animations
    - EmbedFactory integration with Gamble.png thumbnail
    - User-locks to prevent concurrent bets
    """

    def __init__(self, bot):
        self.bot = bot
        self.user_locks: Dict[str, asyncio.Lock] = {}
        self.active_games: Dict[str, str] = {}

    def get_user_lock(self, user_key: str) -> asyncio.Lock:
        """Get or create a lock for a user to prevent concurrent bets"""
        if user_key not in self.user_locks:
            self.user_locks[user_key] = asyncio.Lock()
        return self.user_locks[user_key]

    async def check_premium_server(self, guild_id: int) -> bool:
        """Check if guild has premium access for gambling features"""
        guild_doc = await self.bot.db_manager.get_guild(guild_id)
        if not guild_doc:
            return False

        servers = guild_doc.get('servers', [])
        for server_config in servers:
            server_id = server_config.get('server_id', 'default')
            if await self.bot.db_manager.is_premium_server(guild_id, server_id):
                return True

        return False

    async def add_wallet_event(self, guild_id: int, discord_id: int, 
                              amount: int, event_type: str, description: str):
        """Add wallet transaction event for tracking"""
        try:
            event_doc = {
                "guild_id": guild_id,
                "discord_id": discord_id,
                "amount": amount,
                "event_type": event_type,
                "description": description,
                "timestamp": datetime.now(timezone.utc)
            }

            await self.bot.db_manager.db.wallet_events.insert_one(event_doc)

        except Exception as e:
            logger.error(f"Failed to add wallet event: {e}")

    @discord.slash_command(name="slots", description="Play animated slot machine")
    async def slots(self, ctx: discord.ApplicationContext, bet: int):
        """Animated slot machine gambling game"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            user_key = f"{guild_id}_{discord_id}"

            # Check premium access
            if not await self.check_premium_server(guild_id):
                await ctx.respond("❌ **Premium Feature Required**\n\nThe Gambling System requires premium access. Contact server administrators for more information.", ephemeral=True)
                return

            # Validate bet amount
            if bet <= 0:
                await ctx.respond("❌ Bet amount must be positive!", ephemeral=True)
                return

            if bet > 10000:
                await ctx.respond("❌ Maximum bet is $10,000!", ephemeral=True)
                return

            # Use lock to prevent concurrent gambling
            async with self.get_user_lock(user_key):
                # Check if user has enough money
                wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
                if wallet['balance'] < bet:
                    await ctx.respond(
                        f"❌ Insufficient funds! You have **${wallet['balance']:,}** but need **${bet:,}**",
                        ephemeral=True
                    )
                    return

                # Deduct bet amount first
                await self.bot.db_manager.update_wallet(guild_id, discord_id, -bet, "gambling_slots")

                # Slot symbols and their values
                symbols = ['🍒', '🍋', '🍊', '🍇', '💎', '⭐', '7️⃣']
                weights = [30, 25, 20, 15, 5, 3, 2]

                # Show initial spinning state
                embed, file = await EmbedFactory.build('slots', {
                    'state': 'spinning',
                    'bet_amount': bet,
                    'thumbnail_url': 'attachment://Gamble.png'
                })
                
                if file:
                    response = await ctx.respond(embed=embed, file=file)
                else:
                    response = await ctx.respond(embed=embed)
                
                await asyncio.sleep(2)

                # Generate final results
                reels = [random.choices(symbols, weights=weights)[0] for _ in range(3)]

                # Calculate winnings
                winnings = 0
                win = False

                if reels[0] == reels[1] == reels[2]:  # All three match
                    if reels[0] == '7️⃣':
                        winnings = bet * 100
                        win = True
                    elif reels[0] == '💎':
                        winnings = bet * 50
                        win = True
                    elif reels[0] == '⭐':
                        winnings = bet * 25
                        win = True
                    else:
                        winnings = bet * 10
                        win = True
                elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
                    winnings = bet * 2
                    win = True

                # Update wallet with winnings (bet was already deducted)
                if winnings > 0:
                    await self.bot.db_manager.update_wallet(guild_id, discord_id, winnings, "gambling_slots")

                # Add wallet event
                net_result = winnings - bet
                await self.add_wallet_event(
                    guild_id, discord_id, net_result, "gambling_slots",
                    f"Slots: {' '.join(reels)} | Bet: ${bet:,}"
                )

                # Get updated balance
                updated_wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)

                # Final result display using EmbedFactory
                embed, file = await EmbedFactory.build('slots', {
                    'state': 'result',
                    'win': win,
                    'payout': winnings if win else 0,
                    'bet_amount': bet,
                    'new_balance': updated_wallet['balance'],
                    'thumbnail_url': 'attachment://Gamble.png'
                })
                
                if file:
                    await response.edit_original_message(embed=embed, file=file)
                else:
                    await response.edit_original_message(embed=embed)

        except Exception as e:
            logger.error(f"Failed to process slots: {e}")
            await ctx.respond("❌ Slots game failed. Please try again.", ephemeral=True)

    @discord.slash_command(name="blackjack", description="Play interactive blackjack")
    async def blackjack(self, ctx: discord.ApplicationContext, bet: int):
        """Interactive blackjack card game with button controls"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            user_key = f"{guild_id}_{discord_id}"

            # Check premium access
            if not await self.check_premium_server(guild_id):
                await ctx.respond("❌ **Premium Feature Required**\n\nThe Gambling System requires premium access. Contact server administrators for more information.", ephemeral=True)
                return

            # Validate bet
            if bet <= 0:
                await ctx.respond("❌ Bet amount must be positive!", ephemeral=True)
                return

            if bet > 5000:
                await ctx.respond("❌ Maximum bet is $5,000!", ephemeral=True)
                return

            # Use lock to prevent concurrent games
            async with self.get_user_lock(user_key):
                # Check balance
                wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
                if wallet['balance'] < bet:
                    await ctx.respond(
                        f"❌ Insufficient funds! You have **${wallet['balance']:,}** but need **${bet:,}**",
                        ephemeral=True
                    )
                    return

                await ctx.defer()

                # Create deck
                suits = ['♠️', '♥️', '♦️', '♣️']
                ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
                deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
                random.shuffle(deck)

                # Deal initial cards with animation
                player_cards = []
                dealer_cards = []

                # Dealing animation
                embed, file = await EmbedFactory.build('blackjack', {
                    'status': '🃏 **DEALING CARDS...** 🃏',
                    'player_cards': ['🂠', '🂠'],
                    'dealer_cards': ['🂠', '🂠'],
                    'player_value': 0,
                    'dealer_value': 0,
                    'bet_amount': bet,
                    'thumbnail_url': 'attachment://Gamble.png'
                })
                await ctx.edit_original_response(embed=embed, file=file)
                await asyncio.sleep(1)

                # Deal actual cards
                player_cards = [deck.pop(), deck.pop()]
                dealer_cards = [deck.pop(), deck.pop()]

                def card_value(cards):
                    """Calculate hand value"""
                    value = 0
                    aces = 0

                    for card in cards:
                        rank = card[:-2]
                        if rank in ['J', 'Q', 'K']:
                            value += 10
                        elif rank == 'A':
                            aces += 1
                            value += 11
                        else:
                            value += int(rank)

                    while value > 21 and aces > 0:
                        value -= 10
                        aces -= 1

                    return value

                player_value = card_value(player_cards)
                dealer_value_hidden = card_value([dealer_cards[0]])  # Only show first card
                dealer_value = card_value(dealer_cards)

                # Check for natural blackjack
                if player_value == 21:
                    if dealer_value == 21:
                        result_text = "🤝 **PUSH** - Both have Blackjack!"
                        net_result = 0
                    else:
                        result_text = "🎯 **BLACKJACK!** 🎯"
                        winnings = int(bet * 2.5)
                        net_result = winnings - bet
                else:
                    # Show initial hands (dealer card hidden)
                    dealer_display = [dealer_cards[0], '🂠']

                    embed, file = await EmbedFactory.build('blackjack', {
                        'status': '🎯 **YOUR TURN** 🎯',
                        'player_cards': player_cards,
                        'dealer_cards': dealer_display,
                        'player_value': player_value,
                        'dealer_value': dealer_value_hidden,
                        'bet_amount': bet,
                        'show_buttons': True,
                        'thumbnail_url': 'attachment://Gamble.png'
                    })

                    # Create action buttons
                    view = BlackjackView(deck, player_cards, dealer_cards, bet, guild_id, discord_id, self.bot)
                    await ctx.edit_original_response(embed=embed, file=file, view=view)
                    return  # Let the view handle the rest

                # Handle immediate resolution (blackjacks)
                success = await self.bot.db_manager.update_wallet(
                    guild_id, discord_id, net_result, "gambling_blackjack"
                )

                if success:
                    await self.add_wallet_event(
                        guild_id, discord_id, net_result, "gambling_blackjack",
                        f"Blackjack: P:{player_value} D:{dealer_value} | Bet: ${bet:,}"
                    )

                    updated_wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)

                    embed, file = await EmbedFactory.build('blackjack', {
                        'status': result_text,
                        'player_cards': player_cards,
                        'dealer_cards': dealer_cards,
                        'player_value': player_value,
                        'dealer_value': dealer_value,
                        'bet_amount': bet,
                        'net_result': net_result,
                        'new_balance': updated_wallet['balance'],
                        'thumbnail_url': 'attachment://Gamble.png'
                    })
                    await ctx.edit_original_response(embed=embed, file=file)

        except Exception as e:
            logger.error(f"Failed to process blackjack: {e}")
            await ctx.respond("❌ Blackjack game failed. Please try again.", ephemeral=True)

    @discord.slash_command(name="roulette", description="Play animated roulette")
    async def roulette(self, ctx: discord.ApplicationContext, bet: int, choice: str):
        """Animated roulette wheel game"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            user_key = f"{guild_id}_{discord_id}"

            # Check premium access
            if not await self.check_premium_server(guild_id):
                await ctx.respond("❌ **Premium Feature Required**\n\nThe Gambling System requires premium access. Contact server administrators for more information.", ephemeral=True)
                return

            # Validate bet
            if bet <= 0:
                await ctx.respond("❌ Bet amount must be positive!", ephemeral=True)
                return

            if bet > 2000:
                await ctx.respond("❌ Maximum bet is $2,000!", ephemeral=True)
                return

            # Validate choice
            valid_choices = {
                'red', 'black', 'odd', 'even', 'low', 'high',
                '0', '00'
            }

            for i in range(1, 37):
                valid_choices.add(str(i))

            if choice.lower() not in valid_choices:
                await ctx.respond(
                    "❌ Invalid choice! Use: red, black, odd, even, low (1-18), high (19-36), or numbers (0-36, 00)",
                    ephemeral=True
                )
                return

            # Use lock to prevent concurrent games
            async with self.get_user_lock(user_key):
                # Check balance
                wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
                if wallet['balance'] < bet:
                    await ctx.respond(
                        f"❌ Insufficient funds! You have **${wallet['balance']:,}** but need **${bet:,}**",
                        ephemeral=True
                    )
                    return

                await ctx.defer()

                # Roulette setup
                red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
                black_numbers = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

                # Animation frames - ball spinning
                spinning_frames = [
                    "🎯 Ball spinning... ⚡",
                    "🎯 Ball slowing... 🌀",
                    "🎯 Ball dropping... ⬇️"
                ]

                # Show spinning animation
                for frame in spinning_frames:
                    embed, file = await EmbedFactory.build('roulette', {
                        'status': frame,
                        'player_choice': choice.upper(),
                        'bet_amount': bet,
                        'result': '❓',
                        'thumbnail_url': 'attachment://Gamble.png'
                    })
                    await ctx.edit_original_response(embed=embed, file=file)
                    await asyncio.sleep(1)

                # Final result
                spin_options = ['0', '00'] + [str(i) for i in range(1, 37)]
                result = random.choice(spin_options)

                # Calculate winnings
                winnings = 0
                choice_lower = choice.lower()

                if choice_lower == result:
                    # Exact number match
                    winnings = bet * 35
                elif result not in ['0', '00']:
                    result_num = int(result)

                    if choice_lower == 'red' and result_num in red_numbers:
                        winnings = bet * 2
                    elif choice_lower == 'black' and result_num in black_numbers:
                        winnings = bet * 2
                    elif choice_lower == 'odd' and result_num % 2 == 1:
                        winnings = bet * 2
                    elif choice_lower == 'even' and result_num % 2 == 0:
                        winnings = bet * 2
                    elif choice_lower == 'low' and 1 <= result_num <= 18:
                        winnings = bet * 2
                    elif choice_lower == 'high' and 19 <= result_num <= 36:
                        winnings = bet * 2

                net_result = winnings - bet

                # Determine result color
                if result == '0' or result == '00':
                    result_color = '🟢'
                elif result != '0' and result != '00' and int(result) in red_numbers:
                    result_color = '🔴'
                else:
                    result_color = '⚫'

                # Update wallet
                success = await self.bot.db_manager.update_wallet(
                    guild_id, discord_id, net_result, "gambling_roulette"
                )

                if success:
                    await self.add_wallet_event(
                        guild_id, discord_id, net_result, "gambling_roulette",
                        f"Roulette: {result} | Choice: {choice} | Bet: ${bet:,}"
                    )

                    updated_wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)

                    status = '🎉 **WINNER!** 🎉' if winnings > 0 else '💸 **HOUSE WINS** 💸'

                    embed, file = await EmbedFactory.build('roulette', {
                        'status': status,
                        'player_choice': choice.upper(),
                        'bet_amount': bet,
                        'result': f"{result_color} {result}",
                        'winnings': winnings,
                        'net_result': net_result,
                        'new_balance': updated_wallet['balance'],
                        'thumbnail_url': 'attachment://Gamble.png'
                    })
                    await ctx.edit_original_response(embed=embed, file=file)
                else:
                    await ctx.followup.send("❌ Failed to process bet. Please try again.")

        except Exception as e:
            logger.error(f"Failed to process roulette: {e}")
            await ctx.respond("❌ Roulette game failed. Please try again.", ephemeral=True)


class BlackjackView(discord.ui.View):
    """Interactive blackjack buttons"""

    def __init__(self, deck, player_cards, dealer_cards, bet, guild_id, discord_id, bot):
        super().__init__(timeout=60)
        self.deck = deck
        self.player_cards = player_cards
        self.dealer_cards = dealer_cards
        self.bet = bet
        self.guild_id = guild_id
        self.discord_id = discord_id
        self.bot = bot
        self.game_over = False

    def card_value(self, cards):
        """Calculate hand value"""
        value = 0
        aces = 0

        for card in cards:
            rank = card[:-2]
            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                aces += 1
                value += 11
            else:
                value += int(rank)

        while value > 21 and aces > 0:
            value -= 10
            aces -= 1

        return value

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🃏")
    async def hit_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.game_over:
            return

        # Draw card
        self.player_cards.append(self.deck.pop())
        player_value = self.card_value(self.player_cards)

        if player_value > 21:
            # Bust
            await self.end_game(interaction, "💥 **BUST!** You went over 21!", -self.bet)
        else:
            # Continue game
            dealer_display = [self.dealer_cards[0], '🂠']
            dealer_value_hidden = self.card_value([self.dealer_cards[0]])

            embed, file = await EmbedFactory.build('blackjack', {
                'status': '🎯 **YOUR TURN** 🎯',
                'player_cards': self.player_cards,
                'dealer_cards': dealer_display,
                'player_value': player_value,
                'dealer_value': dealer_value_hidden,
                'bet_amount': self.bet,
                'show_buttons': True,
                'thumbnail_url': 'attachment://Gamble.png'
            })
            await interaction.response.edit_message(embed=embed, file=file, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.game_over:
            return

        # Dealer plays
        dealer_value = self.card_value(self.dealer_cards)
        while dealer_value < 17:
            self.dealer_cards.append(self.deck.pop())
            dealer_value = self.card_value(self.dealer_cards)

        player_value = self.card_value(self.player_cards)

        # Determine winner
        if dealer_value > 21:
            await self.end_game(interaction, "🎉 **DEALER BUST!** You win!", self.bet)
        elif player_value > dealer_value:
            await self.end_game(interaction, "🏆 **YOU WIN!**", self.bet)
        elif dealer_value > player_value:
            await self.end_game(interaction, "😔 **DEALER WINS**", -self.bet)
        else:
            await self.end_game(interaction, "🤝 **PUSH** - It's a tie!", 0)

    async def end_game(self, interaction, result_text, net_result):
        """End the blackjack game and update wallet"""
        self.game_over = True

        # Update wallet
        success = await self.bot.db_manager.update_wallet(
            self.guild_id, self.discord_id, net_result, "gambling_blackjack"
        )

        if success:
            # Add wallet event
            gambling_cog = self.bot.get_cog('Gambling')
            if gambling_cog:
                await gambling_cog.add_wallet_event(
                    self.guild_id, self.discord_id, net_result, "gambling_blackjack",
                    f"Blackjack: P:{self.card_value(self.player_cards)} D:{self.card_value(self.dealer_cards)} | Bet: ${self.bet:,}"
                )

            updated_wallet = await self.bot.db_manager.get_wallet(self.guild_id, self.discord_id)

            embed, file = await EmbedFactory.build('blackjack', {
                'status': result_text,
                'player_cards': self.player_cards,
                'dealer_cards': self.dealer_cards,
                'player_value': self.card_value(self.player_cards),
                'dealer_value': self.card_value(self.dealer_cards),
                'bet_amount': self.bet,
                'net_result': net_result,
                'new_balance': updated_wallet['balance'],
                'thumbnail_url': 'attachment://Gamble.png'
            })

            # Remove buttons
            self.clear_items()
            await interaction.response.edit_message(embed=embed, file=file, view=self)
        else:
            await interaction.response.edit_message(content="❌ Failed to process bet. Please try again.", embed=None, view=None)


def setup(bot):
    bot.add_cog(Gambling(bot))