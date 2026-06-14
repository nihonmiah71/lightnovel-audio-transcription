import re

input_file = 'nani.txt'
output_file = 'nur_matches.txt'

pattern = r'<p(?: class="middle-block")?>(.+?)</p>'

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    matches = re.findall(pattern, text, re.DOTALL)

    with open(output_file, 'w', encoding='utf-8') as f_out:
        for match in matches:
            # 1. Furigana (<rt>...</rt>) samt Inhalt komplett löschen
            match = re.sub(r'<rt>.*?</rt>', '', match, flags=re.DOTALL)
            
            # (Optional) <rp> Tags löschen, falls die Quelldatei welche enthält
            match = re.sub(r'<rp>.*?</rp>', '', match, flags=re.DOTALL)

            # 2. Jetzt erst die restlichen HTML-Tags (wie <ruby>, </ruby>) entfernen
            clean_text = re.sub(r'<.*?>', '', match).strip()
            
            if clean_text:
                f_out.write(clean_text + '\n')

    print(f"Erfolgreich! {len(matches)} Treffer gespeichert.")

except FileNotFoundError:
    print("Fehler: Datei nicht gefunden.")