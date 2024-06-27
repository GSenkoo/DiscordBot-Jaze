"""
MIT License with Attribution Clause

Copyright (c) 2024 GSenkoo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

**Attribution:**
All copies, modifications, or substantial portions of the Software must include
the original author attribution as follows:
"This software includes work by GSenkoo (github)".

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import discord
from discord.ext.pages import Paginator, Page, PaginatorButton
from typing import Union, List

class CustomPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user != interaction.user:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return False
        return True
    
    async def on_timeout(self) -> None:
        try:
            if self.disable_on_timeout:
                for item in self.children:
                    item.disabled = True

                page = self.pages[self.current_page]
                page = self.get_page_content(page)
                files = page.update_files()

                await self.message.edit(
                    view = None,
                    files = files or [],
                    attachments = [],
                )
        except: pass


class PaginatorCreator:
    async def create_paginator(
        self,
        title : Union[str, list],
        embed_color : int,
        data_list : list,
        data_per_page : int = 10,
        pages_looped : bool = False,
        no_data_message : str = "Aucune donnée.",
        page_counter : bool = True,
        custom_rows : List[discord.ui.View] = None,
        without_button_if_onepage : bool = True,
        timeout : int = 300
    ) -> Union[CustomPaginator, list]:
        """
        Paramètres
        --------------------------------------------
        title `Union[str, list]` :
            si type(title) == str : Titre affiché au-dessus de chaques pages
            si type(title) == list : Chaques index de title sera le titre de la page corespondante (avec le même index)
        embed_color `int` :
            Le couleur des embed
        data_list `list` :
            La liste de vos données ("data_per_page" données seront affichés par pages)
        data_per_page `int`, default `10`:
            Le nombre de donnée par page
        pages_looped `bool`, default `False` :
            Oui/Non pour activer le parcours des pages en boucles (quand l'utilisateur essaye d'aller à la prochaine page à la dernière page, il sera redirigé vers la première page)
        no_data_message `str`, default `Aucune donnée` :
            Message qui sera affiché 
        page_counter `bool`, default `True` :
            Activer ou non le compteur de page (dans le footer)
        custom_rows `List[discord.ui.View]`, default `None`) :
            Fonctionne comme l'argument "title" (quand il donnée en frome de liste), mais avec une liste de classe discord.ui.View
        without_button_if_onepage `bool`, default `True`) :
            Retirer les boutons si une seule page est générée
        timeout `int`, default `600` :
            Expiration des boutons après un certains temps d'inutilisation

        Return
        --------------------------------------------
        `Union[utils.Paginator.CustomPaginator, list]`
        
        ⚠ Si le paginator n'a qu'une seule page et que "without_button_if_onepage" est définis à True alors :
            La fonction renverra une liste avec UN SEUL embed à l'intérieur : [discord.Embed]
        Sinon:
            L'instance du paginator (utils.Paginator.CustomPaginator) sera renvoyé.

        
        Exemples pour title (quand il est une liste) et custom_rows
        --------------------------------------------
        ```
        title: ["title_page1", "title_page2", "title_page3"],
        custom_rows: [RowClass1ForPage1, RowClass2ForePage2, RowClass3ForePage3]
        ```
        """
        data_list = [
            data_list[i : i+data_per_page] for i in range(0, len(data_list), data_per_page)
        ]

        pages = [
            Page(
                embeds = [
                    discord.Embed(
                        title = title if type(title) == str else title[index],
                        description = "\n".join(data),
                        color = embed_color
                    ).set_footer(text = f"Page {index + 1}/{len(data_list)}" if page_counter else "")
                ],
                custom_view = custom_rows[index] if custom_rows else None
            ) for index, data in enumerate(data_list)
        ]

        if len(pages) <= 1 and without_button_if_onepage:
            return [
                discord.Embed(
                    title = title,
                    description = "\n".join(data_list[0]) if data_list else no_data_message,
                    color = embed_color
                ).set_footer(text = f"Page 1/1" if page_counter else "")
            ]
        
        if len(pages) == 0:
            pages.append(
                Page(
                    embeds = [
                        discord.Embed(
                            title = title,
                            description = no_data_message,
                            color = embed_color
                        ).set_footer(text = f"Page 1/1" if page_counter else "")
                    ]
                )
            )

        buttons = [
            PaginatorButton("prev", label="◀", style=discord.ButtonStyle.primary, row = 4),
            PaginatorButton("next", label="▶", style=discord.ButtonStyle.primary, row = 4),
        ]

        paginator = CustomPaginator(
            pages = pages,
            custom_buttons = buttons,
            use_default_buttons = False,
            show_indicator = False,
            loop_pages = pages_looped,
            timeout = timeout
        )

        return paginator