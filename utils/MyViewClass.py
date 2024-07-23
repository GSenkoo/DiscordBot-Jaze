import discord

class MyViewClass(discord.ui.View):
    def __init__(self, timeout : int = 180):
        super().__init__(timeout = timeout)
    
    async def on_timeout(self) -> None:
        try: message = await self.message.channel.fetch_message(self.message.id)
        except: return

        def check_is_equal(components1, components2):
            if len(components1) != len(components2):
                return False
            for index in range(len(components1)):
                if len(components1[index]["components"]) != len(components2[index]["components"]):
                    return False
                for index2 in range(len(components1[index]["components"])):
                    if components1[index]["components"][index2]["custom_id"] != components2[index]["components"][index2]["custom_id"]:
                        return False
            return True
        
        message_components = [component.to_dict() for component in message.components]
        
        if check_is_equal(message_components, self.to_components()):
            try: await message.edit(view = None)
            except: pass
