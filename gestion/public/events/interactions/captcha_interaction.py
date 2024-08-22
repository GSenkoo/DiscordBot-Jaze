import discord
import secrets
from datetime import datetime
from discord.ext import commands
from utils.MyViewClass import MyViewClass


class CaptchaInteraction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guilds_attempts = {}

    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        if interaction.custom_id != "captcha_verify":
            return
        
        # --------------------------------- Vérification de l'activation du système de captcha
        captcha_enabled = await self.bot.db.get_data("captcha", "enabled", guild_id = interaction.guild.id)
        if not captcha_enabled:
            await interaction.response.send_message("> Le système de vérification n'est pas activé sur ce serveur.", ephemeral = True)
            return

        # --------------------------------- Obtention et vérification de l'éxistence du rôle des utilisateurs non vérifiés
        non_verified_role_id = await self.bot.db.get_data("captcha", "non_verified_role", guild_id = interaction.guild.id)
        non_verified_role = interaction.guild.get_role(non_verified_role_id)
        if not non_verified_role:
            await interaction.response.send_message("> Le rôle des utilisateurs non vérifiés n'est plus valide ou alors je n'y ai plus accès.", ephemeral = True)
            return
        
        # --------------------------------- Si l'utilisateur n'a pas le rôle des utilisateurs non vérifiés
        if non_verified_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("> Vous n'avez pas besoin de passer cette vérification.", ephemeral = True)
            return

        # --------------------------------- Configuration du système de tentative par serveur
        if interaction.guild.id not in self.guilds_attempts.keys():
            self.guilds_attempts[interaction.guild.id] = {}
        if interaction.user.id not in self.guilds_attempts.keys():
            self.guilds_attempts[interaction.guild.id][interaction.user.id] = 0
        
    
        async def get_captcha_embed(code, code_written, attempts):
            embed = discord.Embed(
                title = "Vérification",
                description = 
                "Pour passer la vérification vous devez copier le code à entrer ci-dessous. En cas d'échec de la vérification, vous serez immédiatement expulsé."
                + f"\n### Code à entrer\n```{code}```"
                + f"\n### Votre code\n```{code_written if code_written else 'Aucun code recopié'}```"
                + f"\nTentatives effectués : **{attempts}/3**",
                color = await self.bot.get_theme(interaction.guild.id)
            )

            return embed
        

        captcha_interaction = self
        class WriteCaptchaCode(MyViewClass):
            def __init__(self, code):
                super().__init__()
                self.code = code
                self.written_code = ""

            @discord.ui.button(emoji = "✅", row = 4)
            async def confirm_callback(self, button, interaction : discord.Interaction):
                if interaction.user.id not in captcha_interaction.guilds_attempts[interaction.guild.id].keys():
                    await interaction.response.send_message("> Merci de réclamer un nouveau menu de vérification.", ephemeral = True)
                    return
                if not interaction.guild.me.guild_permissions.kick_members:
                    await interaction.response.send_message("> Je ne peux pas vous vérifiez car je n'ai pas les permissions nécessaires pour vous expulser en cas d'échec de votre vérification.", ephemeral = True)
                    return
                if interaction.user.top_role.position >= interaction.guild.me.top_role.position:
                    await interaction.response.send_message("> Je ne peux pas vous vérifiez car votre rôle le plus élevé est hiérarchiquement suppérieur ou égal à mon rôle le plus élevé.", ephemeral = True)
                    return
                
                if len(self.written_code) != 10:
                    await interaction.response.send_message(f"> Le code à remplir fait 10 caractères, tandis que le votre en fait seulement {len(self.written_code)}.", ephemeral = True)
                    return
                
                captcha_interaction.guilds_attempts[interaction.guild.id][interaction.user.id] += 1

                # --------------------------------- En cas de code invalide
                if self.code != self.written_code:
                    if captcha_interaction.guilds_attempts[interaction.guild.id][interaction.user.id] == 3:
                        await interaction.edit(embed = discord.Embed(title = "Vérification échouée", color = await captcha_interaction.bot.get_theme(interaction.guild.id)), view = None)

                        del captcha_interaction.guilds_attempts[interaction.guild.id][interaction.user.id]

                        try: await interaction.guild.kick(interaction.user, reason = "Echec à la vérification (un total de 3 tentatives échouées)")
                        except: pass

                    else:
                        await interaction.edit(
                            embed = await get_captcha_embed(self.code, self.written_code, captcha_interaction.guilds_attempts[interaction.guild.id][interaction.user.id])
                        )                       
                
                # --------------------------------- En cas de code valide
                else:            
                    non_verified_role = interaction.guild.get_role(non_verified_role_id)
                    if not non_verified_role:
                        await interaction.response.send_message("> Le rôle des utilisateurs non vérifiés n'est plus disponible.", ephemeral = True)
                        return
                    if non_verified_role.id not in [role.id for role in interaction.user.roles]:
                        await interaction.response.send_message("> Vous n'avez plus besoin de passer cette vérification.", ephemeral = True)
                        return
                    if not interaction.guild.me.guild_permissions.manage_roles:
                        await interaction.response.send_message(f"> Je n'ai pas les permissions nécessaires pour vous retirer le rôle <@&{non_verified_role.mention}>.", ephemeral = True)
                        return
                    
                    try: await interaction.user.remove_roles(non_verified_role, reason = "Vérification passée")
                    except:
                        await interaction.response.send_message(f"> Un problème a eu lieu lors de la tentative du retrait de votre rôle {non_verified_role.mention}.", ephemeral = True)
                        return
                    
                    verified_role_id = await captcha_interaction.bot.db.get_data("captcha", "verified_role", guild_id = interaction.guild.id)
                    if verified_role_id:
                        verified_role = interaction.guild.get_role(verified_role_id)
                        if verified_role and verified_role_id not in [role.id for role in interaction.user.roles]:
                            try: await interaction.user.add_roles(verified_role, reason = "Vérification passée")
                            except: pass

                    await interaction.edit(
                        embed = discord.Embed(
                            title = "Vérification passée avec succès",
                            description = f"Vous avez réussi à entrer le code **{self.code}**. Vous avez accès à l'entièretée du serveur, vous pouvez donc désormais quitter ce salon.",
                            color = await captcha_interaction.bot.get_theme(interaction.guild.id),
                            thumbnail = interaction.guild.icon.url if interaction.guild.icon else None
                        ),
                        view = None
                    )

            @discord.ui.button(emoji = "⏪", row = 4)
            async def del_callback(self, button, interaction: discord.Interaction):
                if interaction.user.id not in captcha_interaction.guilds_attempts[interaction.guild.id].keys():
                    await interaction.response.send_message("> Merci de réclamer un nouveau menu de vérification.", ephemeral = True)
                    return
                
                if self.written_code != "":
                    self.written_code = self.written_code[:-1]
                    await interaction.edit(
                        embed = await get_captcha_embed(self.code, self.written_code, captcha_interaction.guilds_attempts[interaction.guild.id][interaction.user.id])
                    )
                else: await interaction.response.defer()

            @discord.ui.button(emoji = "❌", row = 4)
            async def clear_callback(self, button, interaction: discord.Interaction):
                if interaction.user.id not in captcha_interaction.guilds_attempts[interaction.guild.id].keys():
                    await interaction.response.send_message("> Merci de réclamer un nouveau menu de vérification.", ephemeral = True)
                    return
                
                self.written_code = ""
                await interaction.edit(
                    embed = await get_captcha_embed(self.code, self.written_code, captcha_interaction.guilds_attempts[interaction.guild.id][interaction.user.id])
                )


        code_characters = "0123456789ABCDEFGHIJ"        
        generated_code = "".join([secrets.choice(code_characters) for i in range(10)])
        write_captcha_code = WriteCaptchaCode(generated_code)

        async def put_character_callback(interaction):
            if interaction.user.id not in captcha_interaction.guilds_attempts[interaction.guild.id].keys():
                await interaction.response.send_message("> Merci de réclamer un nouveau menu de vérification.", ephemeral = True)
                return
            
            if len(write_captcha_code.written_code) >= 10:
                await interaction.response.send_message("> Le code à entrer ne fait pas plus de 10 caractères.", ephemeral = True)
                return
            
            write_captcha_code.written_code += interaction.custom_id.removeprefix("captcha_letter_")
            await interaction.edit(embed = await get_captcha_embed(write_captcha_code.code, write_captcha_code.written_code, captcha_interaction.guilds_attempts[interaction.guild.id][interaction.user.id]))


        for character in code_characters:
            button = discord.ui.Button(style = discord.ButtonStyle.primary, label = character, custom_id = "captcha_letter_" + character, disabled = True)
            if character in generated_code:
                button.disabled = False
                button.callback = put_character_callback

            write_captcha_code.add_item(button)

        await interaction.response.send_message(embed = await get_captcha_embed(write_captcha_code.code, write_captcha_code.written_code, captcha_interaction.guilds_attempts[interaction.guild.id][interaction.user.id]), view = write_captcha_code, ephemeral = True)


def setup(bot):

    bot.add_cog(CaptchaInteraction(bot))