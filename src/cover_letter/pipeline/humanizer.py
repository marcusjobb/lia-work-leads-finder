import llm_client


_CLOSING_REWRITE_HINT = {
    "lia": "'Studierna har gett...', 'En LIA-praktik hos er ger möjlighet att...'",
    "junior": "'Erfarenheten från X har gett...', 'En tjänst hos er ger möjlighet att...'",
    "senior": "'Rollen som X innebar...', 'En tjänst hos er skulle innebära...'",
    "any": "'Erfarenheten från X har gett...', 'En tjänst hos er skulle innebära...'",
}
_CLOSING_TOPIC = {
    "lia": "vad studenten vill åstadkomma under LIA",
    "junior": "vad sökande vill bidra med och lära sig i rollen",
    "senior": "vad sökande vill åstadkomma och bidra med i rollen",
    "any": "vad sökande vill bidra med i rollen",
}


async def humanize(letter: str, search_mode: str = "lia") -> str:
    """Make AI-generated letter feel more naturally written."""
    prompt = (
        "Du är en redaktör. Bearbeta detta ansökningsbrev så att det låter som skrivet av en människa.\n\n"
        "Regler:\n"
        "- Bryt upp meningar längre än ~30 ord till kortare, men kombinera meningar kortare än 8 ord med närmaste granne\n"
        "- Variera meningslängden — sikta på 12-20 ord i snitt, undvik att ha fler än 2 korta meningar i rad\n"
        "- Ta bort AI-konstruktioner: 'Det är värt att notera', 'Dessutom', 'Vidare', "
        "'vilket resulterar i', 'i syfte att', 'i enlighet med', 'inte minst'\n"
        "- Ta bort klichéer: 'komplexa tekniska problem', 'lika delar människor och innovation', "
        "'spännande projekt', 'förhoppningsvis bidra till', 'presentera min profil nearmare'\n"
        "- Portfolio-mening: om den är vag ('visar mitt intresse', 'utforska och implementera') — "
        "ersätt med en konkret mening om vad som faktiskt finns i repot\n"
        "- Ersätt em-streck (–) med komma eller punkt\n"
        "- Byt ut 'vi' mot 'jag' när subjektet är den sökande\n"
        "- Reducera antalet meningar som börjar med 'Jag' — målet är max 4-5 'jag' totalt i hela brevet. "
        f"Omformulera genom att sätta ämnet/handlingen först: 'Erfarenheten som X har lärt mig...', "
        f"{_CLOSING_REWRITE_HINT[search_mode]}\n"
        "- Ta bort upprepning av samma ord inom samma mening\n"
        "- Om sista stycket börjar med 'Tack för att ni läser' — ta bort den meningen\n"
        f"- Om brevet slutar med 'ser fram emot att höra från er' — ersätt med en konkret mening om {_CLOSING_TOPIC[search_mode]}\n"
        "- Behåll alla fakta, namn, tekniktermer och URLs exakt som de är\n"
        "- Ändra INTE strukturen (antal stycken, hälsningsfras)\n"
        "- Returnera bara den bearbetade texten, ingen kommentar\n\n"
        f"Brev:\n{letter}"
    )
    result = await llm_client.complete(prompt)
    return result.strip()
