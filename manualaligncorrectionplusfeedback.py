import os
import re
import json
import tkinter as tk
from tkinter import filedialog
from pykakasi import kakasi
from difflib import SequenceMatcher

# --- KONFIGURATION ---
MIN_CHAR_COUNT = 30
MATCH_THRESHOLD = 0.45  # Herabgesetzt auf den stabileren Wert der Simulation

kks = kakasi()


# ==============================
# === ASS-KONVERTIERUNG START ===
# ==============================

def convert_time_to_ass(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int(round((seconds % 1) * 100))
    if centiseconds == 100:
        centiseconds = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def wrap_text(text, max_chars=45):
    """Harter Zeichenumbruch pro ursprünglicher Zeile"""
    if not text:
        return ""
    
    lines = []
    
    # Zeilenweise verarbeiten (respektiert die vorhandenen Zeilenumbrüche)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
            
        current = []
        count = 0
        
        for char in line:
            current.append(char)
            count += 1
            
            if count >= max_chars:
                lines.append("".join(current))
                current = []
                count = 0
                
        if current:
            lines.append("".join(current))
    
    return r"\N".join(lines)


def txt_to_ass(input_path):
    base_path, _ = os.path.splitext(input_path)
    output_path = base_path + ".ass"

    pattern = re.compile(r"\[\s*([\d.]+)\s*->\s*([\d.]+)\s*\]\s*(.*)")
    blocks = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                start, end, text = match.groups()
                blocks.append({
                    "start": float(start),
                    "end": float(end),
                    "text": text.strip()
                })

    ass_content = [
        "[Script Info]",
        "Title: 5-Block Left Aligned",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Text,MS Gothic,38,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,7,20,20,20,1",
        "Style: Timer,MS Gothic,42,&H00FFFF00,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,7,20,20,20,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    for i in range(len(blocks)):
        current = blocks[i]
        start_ass = convert_time_to_ass(current["start"])
        end_ass = convert_time_to_ass(current["end"])
        duration = int(current["end"] - current["start"])

        # Linksbuendige Positionen (Alignment 7)
        if i - 2 >= 0:
            ass_content.append(f'Dialogue: 0,{start_ass},{end_ass},Text,,0,0,0,,{{\\pos(120,100)}}{wrap_text(blocks[i-2]["text"])}')

        if i - 1 >= 0:
            ass_content.append(f'Dialogue: 0,{start_ass},{end_ass},Text,,0,0,0,,{{\\pos(120,300)}}{wrap_text(blocks[i-1]["text"])}')
        
        # Aktueller Block
        current_text = wrap_text(current["text"])
        ass_content.append(f'Dialogue: 0,{start_ass},{end_ass},Text,,0,0,0,,{{\\pos(120,500)}}●{current_text}')
        
        # Nächster Block
        if i + 1 < len(blocks):
            ass_content.append(f'Dialogue: 0,{start_ass},{end_ass},Text,,0,0,0,,{{\\pos(120,700)}}{wrap_text(blocks[i+1]["text"])}')

        # Nächster Block
        if i + 2 < len(blocks):
            ass_content.append(f'Dialogue: 0,{start_ass},{end_ass},Text,,0,0,0,,{{\\pos(120,900)}}{wrap_text(blocks[i+2]["text"])}')


        # Countdown
        for sec in range(duration):
            t_start = convert_time_to_ass(current["start"] + sec)
            t_end = convert_time_to_ass(current["start"] + sec + 1)
            remaining = duration - sec
            ass_content.append(f'Dialogue: 5,{t_start},{t_end},Timer,,0,0,0,,{{\\pos(1750,490)}}{remaining}')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ass_content))

    print(f"✅ ASS-Datei erfolgreich generiert: {output_path}")


# ==============================
# === ASS-KONVERTIERUNG ENDE ===
# ==============================


def to_hiragana(text):
    if not text: return ""
    trans_table = str.maketrans(
        'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモヤャユュヨョラリルレロワヮヰヱヲンヴヵヶ',
        'ぁあぃいううぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもやゃゆゅよょらりるれろわゎゐゑをんゔゕゖ'
    )
    text = text.translate(trans_table)
    result = kks.convert(text)
    hira = "".join([item['hira'] for item in result])
    hira = hira.translate(trans_table)
    hira = re.sub(r'[^\u3040-\u309Fー]', '', hira)
    return hira


def find_best_match_in_area(target, ki_full_string, search_start, search_end):
    search_area = ki_full_string[search_start:search_end]
    if not target or not search_area:
        return 0, search_start, ""
    
    best_score = 0
    best_ki_idx = search_start
    window_size = min(40, len(target))
    
    for i in range(0, len(search_area) - window_size + 1, 1):
        candidate = search_area[i:i + window_size]
        score = SequenceMatcher(None, target[:window_size], candidate).ratio()
        if score > best_score:
            value_modifier = 1.0
            if i + window_size >= len(search_area) - 5:
                value_modifier = 1.15
            
            modified_score = score * value_modifier
            if modified_score > best_score:
                best_score = min(1.0, modified_score)
                best_ki_idx = search_start + i

    if best_score < MATCH_THRESHOLD:
        for n in range(12, 5, -1):
            if len(target) < n: continue
            ngram = target[:n]
            if ngram in search_area:
                pos = search_area.index(ngram)
                candidate = search_area[pos:pos + len(target)]
                score = SequenceMatcher(None, target, candidate).ratio()
                if score > best_score:
                    best_score = score
                    best_ki_idx = search_start + pos
                    break
                    
    return best_score, best_ki_idx, ki_full_string[best_ki_idx:best_ki_idx + len(target)]


def process_from_json(json_path, text_path, output_folder, base_name):
    output_path = os.path.join(output_folder, f"{base_name}_zeitmarken.txt")
    log_path = os.path.join(output_folder, f"{base_name}_mapping_log.txt")
    json_log_path = os.path.join(output_folder, f"{base_name}_mapping_details.json")

    print(f"\n--- Verarbeite aus JSON-Quelle: {base_name} ---")

    # 1. Text laden und Blöcke konsolidieren
    print("⏳ Lade und verarbeite Skript-Textdatei...")
    with open(text_path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    consolidated_blocks, block_hira_list = [], []
    current_block = ""
    for line in raw_lines:
        current_block = (current_block + " " + line).strip()
        if len(current_block) >= MIN_CHAR_COUNT:
            consolidated_blocks.append(current_block)
            block_hira_list.append(to_hiragana(current_block))
            current_block = ""
    if current_block:
        consolidated_blocks.append(current_block)
        block_hira_list.append(to_hiragana(current_block))

    # 2. Bereits existierende KI-Transkription aus JSON laden
    print(f"⏳ Lade KI-Segmente aus: {os.path.basename(json_path)}")
    with open(json_path, "r", encoding="utf-8") as f:
        ai_segments = json.load(f)

    # 3. KI-Zeitstrahl erstellen (Granular auf Zeichenebene)
    print("⏳ Generiere KI-Timeline auf Zeichenebene...")
    ki_timeline = []
    for seg in ai_segments:
        hira = to_hiragana(seg['text'])
        if not hira: continue
        if len(hira) > 5 and len(set(hira)) <= 2: continue

        seg_duration = seg['end'] - seg['start']
        step = seg_duration / len(hira) if len(hira) > 0 else 0
        
        consecutive_count = 0
        for i, char in enumerate(hira):
            consecutive_count = (consecutive_count + 1) if ki_timeline and char == ki_timeline[-1]["char"] else 1
            if consecutive_count > 3: continue
            ki_timeline.append({
                "char": char, 
                "t": seg['start'] + (i * step),
                "seg_end": seg['end'],
                "seg_text": hira
            })

    ki_full_string = "".join([x["char"] for x in ki_timeline])
    total_ki_len = len(ki_timeline)

    if total_ki_len == 0:
        print("❌ FEHLER: Keine gültigen KI-Daten in der JSON gefunden. Abbruch.")
        return

    # 4. Zeitstempel-Mapping mit Zwei-Wege-Suche
    print(f"\n🚀 Starte Zeitstempel-Mapping ({len(consolidated_blocks)} Blöcke zu mappen)...")
    final_output = []
    mapping_logs = []
    json_mapping_details = []
    
    last_ki_index = 0
    last_end_time = 0.0
    block_idx = 0
    num_blocks = len(consolidated_blocks)

    while block_idx < num_blocks:
        block = consolidated_blocks[block_idx]
        block_hira = block_hira_list[block_idx]
        block_len = len(block_hira)

        search_start = max(0, last_ki_index - 100)
        search_end = min(total_ki_len, last_ki_index + 1200)

        # Fortschritts-Log alle 10 Blöcke oder bei schwierigen Stellen
        if block_idx % 10 == 0 or block_idx == num_blocks - 1:
            prozent = (block_idx / num_blocks) * 100
            print(f"   [Fortschritt: {prozent:5.1f}%] Verarbeite Block {block_idx+1}/{num_blocks} | Aktuelle Audiozeit: {last_end_time:.2f}s")

        score, matched_start_idx, actual_match_part = find_best_match_in_area(
            block_hira, ki_full_string, search_start, search_end
        )

        if score >= MATCH_THRESHOLD:
            current_ki_end_idx = matched_start_idx + block_len
            if current_ki_end_idx < last_ki_index:
                current_ki_end_idx = min(total_ki_len - 1, last_ki_index + max(5, int(block_len * 0.5)))
                method_info = "FORCED_LINEAR"
                diagnosis = "Muster korreliert, aber Index läuft rückwärts. Erzwungene Vorwärtsbewegung."
            else:
                method_info = "FUZZY (OK)"
                diagnosis = "Gutes Text-Match auf der Timeline gefunden. Synchronisation stabil."
            
            s_idx = max(0, min(last_ki_index, total_ki_len - 1))
            e_idx = max(0, min(int(current_ki_end_idx), total_ki_len - 1))
            start_t = ki_timeline[s_idx]["t"]
            end_t = ki_timeline[e_idx]["t"]

            if start_t < last_end_time: start_t = last_end_time
            if end_t <= start_t: end_t = start_t + max(1.5, block_len * 0.14)

            final_output.append(f"[{start_t:6.2f} -> {end_t:6.2f}] {block}")
            
            json_mapping_details.append({
                "block_index": block_idx,
                "text_preview": block[:30] + "...",
                "methode": method_info,
                "score": round(score, 4),
                "zeit_start": round(start_t, 2),
                "zeit_end": round(end_t, 2),
                "vergleich": {"original_skript_anker_hiragana": block_hira[:50], "ki_transkript_match_hiragana": actual_match_part}
            })

            mapping_logs.append(f"Block {block_idx:03d} | Methode: {method_info}\n  Diagnose: {diagnosis}\n  Zeit: {start_t:.2f}s bis {end_t:.2f}s\n{'-'*50}")
            
            last_ki_index = e_idx
            last_end_time = end_t
            block_idx += 1

        else:
            # --- ZIELGERICHTETE ZWEI-WEGE-SUCHE BEI FEHLSCHLAG ---
            # Sofortige Konsolen-Meldung, dass eine komplexe Suche/Lookahead stattfindet (Hier könnte das Programm "hängen")
            print(f"   ⚠️ [Lookahead Suche] Block {block_idx:03d} passt nicht direkt (Score: {score:.2f}). Scanne Zukunftstext...")
            
            found_future_match = False
            lookahead_limit = min(block_idx + 15, num_blocks)
            
            for future_idx in range(block_idx + 1, lookahead_limit):
                future_hira = block_hira_list[future_idx]
                f_search_start = max(0, last_ki_index - 50)
                f_search_end = min(total_ki_len, last_ki_index + 3000) 
                
                f_score, f_matched_idx, f_match_part = find_best_match_in_area(
                    future_hira, ki_full_string, f_search_start, f_search_end
                )
                
                if f_score >= MATCH_THRESHOLD and f_matched_idx >= last_ki_index:
                    skipped_count = future_idx - block_idx
                    future_match_time = ki_timeline[f_matched_idx]["t"]
                    
                    total_skipped_duration = max(2.0, future_match_time - last_end_time)
                    time_per_skipped_block = total_skipped_duration / skipped_count
                    
                    diagnosis = f"DELETION_STRETCH! Whisper hat {skipped_count} Blöcke übersprungen. Verteilung linear über {total_skipped_duration:.2f}s."
                    print(f"   🔍 -> Match bei Block {future_idx} gefunden! Überbrücke {skipped_count} fehlende Blöcke linear.")
                    
                    running_time = last_end_time
                    for k in range(block_idx, future_idx):
                        s_t = running_time
                        e_t = running_time + time_per_skipped_block
                        
                        final_output.append(f"[{s_t:6.2f} -> {e_t:6.2f}] {consolidated_blocks[k]}")
                        
                        json_mapping_details.append({
                            "block_index": k,
                            "text_preview": consolidated_blocks[k][:30] + "...",
                            "methode": "DELETION_STRETCH",
                            "score": round(f_score, 4),
                            "zeit_start": round(s_t, 2),
                            "zeit_end": round(e_t, 2),
                            "vergleich": {"original_skript_anker_hiragana": block_hira_list[k][:50], "ki_transkript_match_hiragana": ""}
                        })
                        mapping_logs.append(f"Block {k:03d} | Methode: DELETION_STRETCH\n  Diagnose: {diagnosis}\n  Zeit: {s_t:.2f}s bis {e_t:.2f}s\n{'-'*50}")
                        running_time = e_t
                    
                    last_end_time = future_match_time
                    last_ki_index = f_matched_idx
                    block_idx = future_idx  
                    found_future_match = True
                    break

            if found_future_match:
                continue

            # --- FALLBACK ---
            method_info = "LOOP_RECOVERY_FALLBACK"
            estimated_duration = max(2.0, block_len * 0.14)
            target_time = last_end_time + estimated_duration
            diagnosis = "Kein Match im Zukunftstext des Buches. Verwende lineare Zeitschätzung basierend auf Zeichenlänge."
            
            print(f"   🚨 [Fallback] Komplett asynchron bei Block {block_idx:03d}. Schätze Zeit linear (+{estimated_duration:.1f}s).")

            current_ki_end_idx = last_ki_index
            for idx in range(last_ki_index, total_ki_len):
                if ki_timeline[idx]["t"] >= target_time:
                    current_ki_end_idx = idx
                    break
            if current_ki_end_idx == last_ki_index:
                current_ki_end_idx = min(total_ki_len - 1, last_ki_index + max(5, block_len))

            s_idx = max(0, min(last_ki_index, total_ki_len - 1))
            e_idx = max(0, min(int(current_ki_end_idx), total_ki_len - 1))
            start_t = ki_timeline[s_idx]["t"]
            end_t = ki_timeline[e_idx]["t"]

            if start_t < last_end_time: start_t = last_end_time
            if end_t <= start_t: end_t = start_t + max(1.5, block_len * 0.14)

            final_output.append(f"[{start_t:6.2f} -> {end_t:6.2f}] {block}")
            
            json_mapping_details.append({
                "block_index": block_idx,
                "text_preview": block[:30] + "...",
                "methode": method_info,
                "score": round(score, 4),
                "zeit_start": round(start_t, 2),
                "zeit_end": round(end_t, 2),
                "vergleich": {"original_skript_anker_hiragana": block_hira[:50], "ki_transkript_match_hiragana": ""}
            })
            mapping_logs.append(f"Block {block_idx:03d} | Methode: {method_info}\n  Diagnose: {diagnosis}\n  Zeit: {start_t:.2f}s bis {end_t:.2f}s\n{'-'*50}")
            
            last_ki_index = e_idx
            last_end_time = end_t
            block_idx += 1

    # 5. Dateien schreiben
    print("\n⏳ Schreibe Output-Dateien...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(line + "\n" for line in final_output)

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"MAPPING LOG - Kapitel: {base_name}\n")
        f.write(f"Gesamtzeichen (Original): {len(consolidated_blocks)}\n")
        f.write(f"Gesamtzeichen (KI-Extrakt): {total_ki_len}\n")
        f.write("="*50 + "\n")
        f.writelines(line + "\n" for line in mapping_logs)

    with open(json_log_path, "w", encoding="utf-8") as f:
        json.dump(json_mapping_details, f, ensure_ascii=False, indent=4)

    print(f"✅ Erfolgreich abgeschlossen: {output_path}")

    # 6. Automatische ASS-Konvertierung
    print("⏳ Starte ASS-Generierung aus der Textquelle...")
    txt_to_ass(output_path)


def main():
    print("=== ASS-GENERATOR AUS VORHANDENEN WHISPERX JSON-ROHDATEN ===")
    
    # Tkinter initialisieren und verstecken
    root = tk.Tk()
    root.withdraw()

    print("\nBitte wähle die existierende RAW-JSON-DATEI (*_ai_raw.json) im Explorer-Fenster aus...")
    json_path = filedialog.askopenfilename(
        title="Wähle die _ai_raw.json Datei",
        filetypes=[("WhisperX Raw JSON", "*_ai_raw.json"), ("JSON-Dateien", "*.json")]
    )
    
    if not json_path:
        print("Keine JSON-Datei ausgewählt. Programm beendet.")
        return

    output_folder = os.path.dirname(json_path)
    json_file_name = os.path.basename(json_path)
    
    # Den Basisnamen des Kapitels extrahieren (schneidet '_ai_raw.json' am Ende ab)
    if json_file_name.endswith("_ai_raw.json"):
        base_name = json_file_name[:-12]
    else:
        base_name = os.path.splitext(json_file_name)[0]

    # Automatische Pfadableitung für die korrespondierende Skript-Textdatei
    text_path = os.path.join(output_folder, f"{base_name}.txt")

    # Überprüfung, ob die zugehörige Textdatei existiert
    if not os.path.exists(text_path):
        print(f"\n❌ FEHLER: Die erwartete Textdatei wurde nicht gefunden!")
        print(f"Gesucht nach: {text_path}")
        print("Bitte stelle sicher, dass die .txt-Datei denselben Hauptnamen besitzt und im selben Ordner liegt.")
        return

    print(f"\n➔ Basisname erkannt: {base_name}")
    print(f"➔ Textquelle: {text_path}")
    
    # Verarbeitung starten
    process_from_json(json_path, text_path, output_folder, base_name)


if __name__ == "__main__":
    main()